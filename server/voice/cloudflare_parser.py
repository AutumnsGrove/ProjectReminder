"""
Cloudflare Workers AI Parser for reminder text.

This module provides CloudflareAIParser which uses Cloudflare's Workers AI
platform to parse natural language reminder text. It offers the same interface
as LocalLLMParser but runs inference on Cloudflare's edge network.

Benefits over local:
- No local GPU required
- Serverless / always available (when online)
- Automatic scaling

Tradeoffs:
- Requires internet connection
- Data sent to Cloudflare (privacy consideration)
- May have rate limits on free tier

Author: Claude Sonnet 4.5 (Phase 8.1)
Date: 2025-11-04
"""

import json
import os
from datetime import datetime
from typing import Dict, Optional, Any

import httpx
from pydantic import BaseModel, Field, ValidationError

from server.voice.prompts import get_reminder_parse_prompt, get_user_message
from server.voice.date_utils import parse_natural_date, parse_natural_time


class CloudflareAIParser:
    """
    Parser for reminder text using Cloudflare Workers AI.

    Uses Cloudflare's serverless AI inference platform to parse natural language
    reminder text. Requires Cloudflare account ID and API token.

    Attributes:
        account_id: Cloudflare account ID
        api_token: Cloudflare API token with Workers AI permissions
        model_name: Model identifier on Cloudflare AI
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts for transient errors
    """

    # Cloudflare API base URL
    CF_API_BASE = "https://api.cloudflare.com/client/v4"

    def __init__(
        self,
        account_id: Optional[str] = None,
        api_token: Optional[str] = None,
        model_name: str = "@cf/openai/gpt-oss-20b",
        timeout: float = 10.0,
        max_retries: int = 2
    ):
        """
        Initialize CloudflareAIParser.

        Args:
            account_id: Cloudflare account ID (reads from secrets.json if not provided)
            api_token: Cloudflare API token (reads from secrets.json if not provided)
            model_name: Model identifier on Cloudflare Workers AI
            timeout: HTTP request timeout in seconds
            max_retries: Number of retry attempts for transient errors

        Raises:
            ValueError: If credentials are not provided and not found in secrets.json
        """
        # Load credentials from secrets.json if not provided
        if account_id is None or api_token is None:
            secrets = self._load_secrets()
            account_id = account_id or secrets.get("cloudflare_account_id")
            api_token = api_token or secrets.get("cloudflare_api_token")

        if not account_id or not api_token:
            raise ValueError(
                "Cloudflare credentials not found. Please provide account_id and api_token, "
                "or add them to secrets.json (cloudflare_account_id, cloudflare_api_token)"
            )

        self.account_id = account_id
        self.api_token = api_token
        self.model_name = model_name
        self.timeout = timeout
        self.max_retries = max_retries

        # Create async HTTP client
        self.client = httpx.AsyncClient(
            base_url=self.CF_API_BASE,
            timeout=httpx.Timeout(timeout),
            headers={
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
        )

    def _load_secrets(self) -> Dict[str, str]:
        """
        Load secrets from secrets.json file.

        Returns:
            Dictionary of secrets (empty if file not found)
        """
        try:
            # Look for secrets.json in project root
            secrets_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "secrets.json"
            )
            if os.path.exists(secrets_path):
                with open(secrets_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"[CloudflareAIParser] Error loading secrets: {e}")

        return {}

    async def close(self):
        """Close the HTTP client (cleanup)."""
        await self.client.aclose()

    async def parse_reminder_text(self, text: str) -> Dict[str, Any]:
        """
        Parse reminder text using Cloudflare Workers AI.

        Args:
            text: Natural language reminder text

        Returns:
            Dictionary with parsed metadata (same format as LocalLLMParser)

        Raises:
            Exception: If Cloudflare API is unavailable or auth fails
        """
        if not text or not text.strip():
            return self._empty_parse(text or "", 0.0)

        # Retry logic for transient errors
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                result = await self._parse_attempt(text)
                return result

            except httpx.HTTPStatusError as e:
                # Don't retry on auth errors (401) or bad requests (400)
                if e.response.status_code in (400, 401, 403):
                    raise Exception(
                        f"Cloudflare auth/request error ({e.response.status_code}): "
                        f"Check your account_id and api_token"
                    )

                # Retry on rate limits (429) and server errors (5xx)
                if e.response.status_code in (429, 500, 502, 503, 504):
                    last_error = e
                    if attempt < self.max_retries:
                        # Exponential backoff: wait 1s, 2s, 4s
                        await asyncio.sleep(2 ** attempt)
                        continue

                raise Exception(f"Cloudflare API error: {e}")

            except httpx.TimeoutException:
                raise Exception(f"Cloudflare request timed out after {self.timeout}s")

            except Exception as e:
                last_error = e
                if attempt < self.max_retries:
                    await asyncio.sleep(2 ** attempt)
                    continue
                break

        # All retries failed
        print(f"[CloudflareAIParser] All retry attempts failed: {last_error}")
        return self._empty_parse(text, 0.1)

    async def _parse_attempt(self, text: str) -> Dict[str, Any]:
        """
        Single parse attempt (called by retry logic).

        Args:
            text: Reminder text to parse

        Returns:
            Parsed metadata dictionary
        """
        # Get current date for prompt context
        current_date = datetime.now().strftime('%Y-%m-%d')

        # Generate system prompt with few-shot examples
        system_prompt = get_reminder_parse_prompt(current_date)
        user_message = get_user_message(text)

        # Cloudflare Workers AI endpoint
        endpoint = f"/accounts/{self.account_id}/ai/run/{self.model_name}"

        # Request body format for Cloudflare AI
        request_body = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "temperature": 0.3,
            "max_tokens": 400
        }

        # Call Cloudflare Workers AI
        response = await self.client.post(endpoint, json=request_body)
        response.raise_for_status()

        data = response.json()

        # Cloudflare response format: { "result": { "response": "..." }, "success": true }
        if not data.get("success"):
            errors = data.get("errors", [])
            raise Exception(f"Cloudflare API returned success=false: {errors}")

        result = data.get("result", {})
        llm_response = result.get("response", "")

        # Parse JSON response
        parsed_json = self._extract_json(llm_response)

        if not parsed_json:
            print(f"[CloudflareAIParser] Failed to extract JSON from: {llm_response[:200]}")
            return self._empty_parse(text, 0.2)

        # Validate and post-process
        validated = self._validate_and_normalize(parsed_json, text)

        # Add parse mode
        validated["parse_mode"] = "cloud"

        return validated

    def _extract_json(self, llm_response: str) -> Optional[Dict]:
        """
        Extract JSON from LLM response (same logic as LocalLLMParser).

        Args:
            llm_response: Raw text from LLM

        Returns:
            Parsed JSON dict or None
        """
        try:
            return json.loads(llm_response.strip())
        except json.JSONDecodeError:
            pass

        # Try code blocks
        if "```json" in llm_response:
            start = llm_response.find("```json") + 7
            end = llm_response.find("```", start)
            if end != -1:
                try:
                    return json.loads(llm_response[start:end].strip())
                except json.JSONDecodeError:
                    pass

        # Try brace extraction
        start = llm_response.find('{')
        end = llm_response.rfind('}')
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(llm_response[start:end+1])
            except json.JSONDecodeError:
                pass

        return None

    def _validate_and_normalize(self, parsed_json: Dict, original_text: str) -> Dict[str, Any]:
        """
        Validate and normalize parsed JSON (same as LocalLLMParser).

        Args:
            parsed_json: Raw JSON from LLM
            original_text: Original reminder text

        Returns:
            Validated dictionary
        """
        # Use same validation logic as LocalLLMParser for consistency
        # (Import ParsedReminder from parser.py in real implementation)
        result = {
            "text": parsed_json.get("text", original_text),
            "due_date": parsed_json.get("due_date"),
            "due_time": parsed_json.get("due_time"),
            "time_required": parsed_json.get("time_required", False),
            "priority": parsed_json.get("priority"),
            "category": parsed_json.get("category"),
            "location": parsed_json.get("location"),
            "confidence": parsed_json.get("confidence", 0.5)
        }

        # Validate priority
        valid_priorities = {"urgent", "important", "chill", "someday", "waiting"}
        if result.get("priority") and result["priority"].lower() not in valid_priorities:
            result["priority"] = None
            result["confidence"] *= 0.9

        # Validate category
        valid_categories = {
            "Personal", "Work", "Errands", "Home",
            "Health", "Calls", "Shopping", "Projects"
        }
        if result.get("category") and result["category"] not in valid_categories:
            result["category"] = None
            result["confidence"] *= 0.9

        # Clamp confidence
        result["confidence"] = max(0.0, min(1.0, result["confidence"]))

        return result

    def _empty_parse(self, text: str, confidence: float) -> Dict[str, Any]:
        """
        Create empty parse result.

        Args:
            text: Original text
            confidence: Low confidence score

        Returns:
            Empty parse dict
        """
        return {
            "text": text,
            "due_date": None,
            "due_time": None,
            "time_required": False,
            "priority": None,
            "category": None,
            "location": None,
            "confidence": confidence,
            "parse_mode": "cloud"
        }

    def __del__(self):
        """Cleanup on garbage collection."""
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.close())
        except Exception:
            pass


# Import asyncio for sleep in retry logic
import asyncio
