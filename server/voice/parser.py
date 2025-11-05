"""
Local LLM Parser for reminder text using LM Studio.

This module provides the LocalLLMParser class which connects to a local
LM Studio instance to parse natural language reminder text into structured
metadata using Llama 3.2 1B or similar small language models.

Architecture:
- Async HTTP client (httpx) for non-blocking LM Studio API calls
- System prompt from prompts.py with few-shot examples
- JSON response parsing with validation
- Confidence scoring per field
- Graceful error handling with fallback to empty parse

Author: Claude Sonnet 4.5 (Phase 8.1)
Date: 2025-11-04
"""

import json
from datetime import datetime
from typing import Dict, Optional, Any
from enum import Enum

import httpx
from pydantic import BaseModel, Field, ValidationError

from server.voice.prompts import get_reminder_parse_prompt, get_user_message
from server.voice.date_utils import (
    parse_natural_date,
    parse_natural_time,
    is_past_date,
    get_relative_date
)


class ParseMode(str, Enum):
    """Parsing mode for reminder text."""
    LOCAL = "local"
    CLOUD = "cloud"
    AUTO = "auto"


class ParsedReminder(BaseModel):
    """Validated parsed reminder metadata from LLM."""
    text: str = Field(..., description="Core reminder text")
    due_date: Optional[str] = Field(None, description="ISO date (YYYY-MM-DD)")
    due_time: Optional[str] = Field(None, description="ISO time (HH:MM:SS)")
    time_required: bool = Field(False, description="Is specific time required?")
    priority: Optional[str] = Field(None, description="Priority level")
    category: Optional[str] = Field(None, description="Category")
    location: Optional[str] = Field(None, description="Location name/address")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Overall confidence")


class LocalLLMParser:
    """
    Parser for reminder text using local LM Studio instance.

    Connects to LM Studio's OpenAI-compatible API to parse natural language
    reminder text into structured metadata using a small language model.

    Attributes:
        lm_studio_url: Base URL for LM Studio API (default: http://127.0.0.1:1234)
        model_name: Name of the model to use (default: llama-3.2-1b-instruct)
        timeout: Request timeout in seconds (default: 10)
        temperature: LLM temperature for generation (default: 0.3 for consistency)
        max_tokens: Maximum tokens in response (default: 400)
    """

    def __init__(
        self,
        lm_studio_url: str = "http://127.0.0.1:1234",
        model_name: str = "llama-3.2-1b-instruct",
        timeout: float = 10.0,
        temperature: float = 0.3,
        max_tokens: int = 400
    ):
        """
        Initialize the LocalLLMParser.

        Args:
            lm_studio_url: Base URL for LM Studio API
            model_name: Model identifier in LM Studio
            timeout: HTTP request timeout in seconds
            temperature: LLM sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens for completion
        """
        self.lm_studio_url = lm_studio_url.rstrip('/')
        self.model_name = model_name
        self.timeout = timeout
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Create async HTTP client
        self.client = httpx.AsyncClient(
            base_url=self.lm_studio_url,
            timeout=httpx.Timeout(timeout)
        )

    async def close(self):
        """Close the HTTP client (cleanup)."""
        await self.client.aclose()

    async def parse_reminder_text(self, text: str) -> Dict[str, Any]:
        """
        Parse reminder text into structured metadata using local LLM.

        Args:
            text: Natural language reminder text from voice or typing

        Returns:
            Dictionary with parsed metadata:
            {
                "text": "Call mom",
                "due_date": "2025-11-05",
                "due_time": "15:00:00",
                "time_required": true,
                "priority": "urgent",
                "category": "Calls",
                "location": null,
                "confidence": 0.95,
                "parse_mode": "local"
            }

        Raises:
            Exception: If LM Studio is unavailable or parsing fails completely
        """
        if not text or not text.strip():
            return self._empty_parse(text or "", 0.0)

        try:
            # Get current date for prompt context
            current_date = datetime.now().strftime('%Y-%m-%d')

            # Generate system prompt with few-shot examples
            system_prompt = get_reminder_parse_prompt(current_date)
            user_message = get_user_message(text)

            # Call LM Studio API (OpenAI-compatible)
            response = await self.client.post(
                "/v1/chat/completions",
                json={
                    "model": self.model_name,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens
                }
            )

            response.raise_for_status()
            data = response.json()

            # Extract LLM response
            if "choices" not in data or len(data["choices"]) == 0:
                raise ValueError("No response from LLM")

            llm_response = data["choices"][0]["message"]["content"]

            # Parse JSON response
            parsed_json = self._extract_json(llm_response)

            if not parsed_json:
                # Fallback to empty parse if JSON extraction fails
                print(f"[LocalLLMParser] Failed to extract JSON from: {llm_response[:200]}")
                return self._empty_parse(text, 0.2)

            # Validate and post-process parsed data
            validated = self._validate_and_normalize(parsed_json, text)

            # Add parse mode
            validated["parse_mode"] = "local"

            return validated

        except httpx.ConnectError:
            raise Exception("LM Studio not available - is it running at {}?".format(self.lm_studio_url))
        except httpx.TimeoutException:
            raise Exception("LM Studio request timed out after {}s".format(self.timeout))
        except Exception as e:
            print(f"[LocalLLMParser] Parse error: {e}")
            # Return empty parse with low confidence on errors
            return self._empty_parse(text, 0.1)

    def _extract_json(self, llm_response: str) -> Optional[Dict]:
        """
        Extract JSON object from LLM response text.

        The LLM might return JSON with extra text or markdown formatting.
        This function attempts to extract the JSON cleanly.

        Args:
            llm_response: Raw text response from LLM

        Returns:
            Parsed JSON dict or None if extraction fails
        """
        try:
            # Try direct JSON parse first
            return json.loads(llm_response.strip())
        except json.JSONDecodeError:
            pass

        # Try to find JSON in code blocks (```json ... ```)
        if "```json" in llm_response:
            start = llm_response.find("```json") + 7
            end = llm_response.find("```", start)
            if end != -1:
                try:
                    return json.loads(llm_response[start:end].strip())
                except json.JSONDecodeError:
                    pass

        # Try to find first { and last }
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
        Validate LLM output and normalize date/time formats.

        Args:
            parsed_json: Raw JSON from LLM
            original_text: Original reminder text (fallback)

        Returns:
            Validated and normalized dictionary
        """
        try:
            # Use Pydantic for validation
            validated = ParsedReminder(**parsed_json)
            result = validated.model_dump()

        except ValidationError as e:
            print(f"[LocalLLMParser] Validation error: {e}")
            # Start with empty parse
            result = {
                "text": parsed_json.get("text", original_text),
                "due_date": None,
                "due_time": None,
                "time_required": False,
                "priority": None,
                "category": None,
                "location": None,
                "confidence": 0.3
            }

        # Post-process dates and times for consistency
        if result.get("due_date"):
            # Ensure date is valid ISO format
            try:
                # Re-parse with date_utils to catch edge cases
                reparsed_date = parse_natural_date(
                    result["due_date"],
                    datetime.now()
                )
                if reparsed_date:
                    result["due_date"] = reparsed_date
                else:
                    # Invalid date, set to None
                    result["due_date"] = None
                    result["confidence"] *= 0.8  # Reduce confidence
            except Exception:
                result["due_date"] = None
                result["confidence"] *= 0.8

        if result.get("due_time"):
            # Ensure time is HH:MM:SS format
            time_str = result["due_time"]
            if len(time_str) == 5:  # HH:MM
                result["due_time"] = f"{time_str}:00"
            elif len(time_str) != 8:  # Not HH:MM:SS
                result["due_time"] = None
                result["confidence"] *= 0.9

        # Validate priority values
        valid_priorities = {"urgent", "important", "chill", "someday", "waiting"}
        if result.get("priority") and result["priority"].lower() not in valid_priorities:
            result["priority"] = None
            result["confidence"] *= 0.9

        # Validate category values
        valid_categories = {
            "Personal", "Work", "Errands", "Home",
            "Health", "Calls", "Shopping", "Projects"
        }
        if result.get("category") and result["category"] not in valid_categories:
            result["category"] = None
            result["confidence"] *= 0.9

        # Ensure confidence is in [0.0, 1.0]
        result["confidence"] = max(0.0, min(1.0, result.get("confidence", 0.5)))

        return result

    def _empty_parse(self, text: str, confidence: float) -> Dict[str, Any]:
        """
        Create an empty parse result with low confidence.

        Args:
            text: Original reminder text
            confidence: Confidence score (typically 0.0-0.3)

        Returns:
            Empty parse dictionary
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
            "parse_mode": "local"
        }

    def __del__(self):
        """Cleanup: Close HTTP client on garbage collection."""
        # Note: This is not ideal for async, but provides basic cleanup
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.close())
        except Exception:
            pass
