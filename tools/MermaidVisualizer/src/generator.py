"""
Mermaid diagram generator module.

This module provides functionality to generate PNG and SVG diagrams from Mermaid syntax
using the mermaid-cli tool (mmdc command) or kroki.io API as a fallback.
"""

import base64
import glob
import logging
import os
import subprocess
import tempfile
import zlib
from pathlib import Path
from typing import Optional, Tuple

import requests

logger = logging.getLogger(__name__)


def generate_diagram_via_kroki(
    mermaid_content: str,
    output_path: Path,
    format: str = "png",
) -> bool:
    """
    Generate a diagram using kroki.io API as a fallback.

    Args:
        mermaid_content: The Mermaid diagram syntax as a string
        output_path: Path where the output diagram should be saved
        format: Output format, either "png" or "svg" (default: "png")

    Returns:
        True if diagram generation was successful, False otherwise
    """
    try:
        # Compress and encode the mermaid content
        compressed = zlib.compress(mermaid_content.encode('utf-8'), 9)
        encoded = base64.urlsafe_b64encode(compressed).decode('utf-8')

        url = f"https://kroki.io/mermaid/{format}/{encoded}"
        logger.info(f"Using kroki.io API fallback for diagram generation")

        response = requests.get(url, timeout=60)

        if response.status_code == 200:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'wb') as f:
                f.write(response.content)

            logger.info(f"Successfully generated diagram via kroki.io: {output_path}")
            return True
        else:
            logger.error(f"kroki.io API failed with status {response.status_code}")
            return False

    except Exception as e:
        logger.error(f"Failed to generate diagram via kroki.io: {e}")
        return False


def find_chrome_executable() -> Optional[str]:
    """
    Automatically detect Chrome/Chromium executable path.

    Searches in common installation locations for Chrome, prioritizing:
    1. PUPPETEER_EXECUTABLE_PATH environment variable
    2. ~/.cache/puppeteer/chrome installations (most recent version)
    3. System Chrome installations

    Returns:
        Path to Chrome executable if found, None otherwise
    """
    # Check environment variable first
    if "PUPPETEER_EXECUTABLE_PATH" in os.environ:
        chrome_path = os.environ["PUPPETEER_EXECUTABLE_PATH"]
        if Path(chrome_path).exists():
            logger.debug(f"Using Chrome from PUPPETEER_EXECUTABLE_PATH: {chrome_path}")
            return chrome_path

    # Check puppeteer cache (common for npm/npx installations)
    home = Path.home()
    puppeteer_cache = home / ".cache" / "puppeteer" / "chrome"

    if puppeteer_cache.exists():
        # Find all Chrome installations, sorted by version (newest first)
        chrome_pattern = str(
            puppeteer_cache
            / "*"
            / "chrome-mac-arm64"
            / "Google Chrome for Testing.app"
            / "Contents"
            / "MacOS"
            / "Google Chrome for Testing"
        )
        chrome_paths = sorted(glob.glob(chrome_pattern), reverse=True)

        if chrome_paths:
            logger.debug(f"Found Chrome in puppeteer cache: {chrome_paths[0]}")
            return chrome_paths[0]

    # Check for system Chrome installations (macOS)
    system_chrome_paths = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ]

    for chrome_path in system_chrome_paths:
        if Path(chrome_path).exists():
            logger.debug(f"Found system Chrome: {chrome_path}")
            return chrome_path

    # Check for Linux Chrome installations
    linux_chrome_paths = [
        "/usr/bin/google-chrome",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
    ]

    for chrome_path in linux_chrome_paths:
        if Path(chrome_path).exists():
            logger.debug(f"Found Linux Chrome: {chrome_path}")
            return chrome_path

    logger.warning(
        "Could not find Chrome executable. Puppeteer will attempt auto-detection."
    )
    return None


def validate_mermaid_syntax(mermaid_content: str) -> Tuple[bool, str]:
    """
    Validate Mermaid syntax by attempting to generate a diagram.

    Args:
        mermaid_content: The Mermaid diagram content to validate

    Returns:
        A tuple of (is_valid, error_message). If valid, error_message is empty.
        If invalid, error_message contains details about the validation failure.

    Example:
        >>> is_valid, error = validate_mermaid_syntax("graph TD\\nA-->B")
        >>> if not is_valid:
        ...     print(f"Validation failed: {error}")
    """
    if not mermaid_content or not mermaid_content.strip():
        return False, "Mermaid content is empty"

    # Check if content has basic Mermaid diagram structure
    mermaid_content_lower = mermaid_content.strip().lower()
    valid_diagram_types = [
        "graph",
        "flowchart",
        "sequencediagram",
        "classDiagram",
        "stateDiagram",
        "erDiagram",
        "gantt",
        "pie",
        "gitgraph",
        "journey",
        "mindmap",
        "timeline",
        "quadrantchart",
        "requirement",
    ]

    # Remove whitespace for checking
    content_no_space = mermaid_content_lower.replace(" ", "").replace("\n", "")

    has_valid_type = any(
        diagram_type.lower().replace(" ", "") in content_no_space
        for diagram_type in valid_diagram_types
    )

    if not has_valid_type:
        return (
            False,
            f"Content does not appear to contain a valid Mermaid diagram type. "
            f"Expected one of: {', '.join(valid_diagram_types)}",
        )

    # Try to generate a diagram to validate syntax
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".mmd", delete=False
        ) as temp_input:
            temp_input_path = Path(temp_input.name)
            temp_input.write(mermaid_content)

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_output:
            temp_output_path = Path(temp_output.name)

        try:
            # Set up environment with Chrome path if found
            env = os.environ.copy()
            chrome_path = find_chrome_executable()
            if chrome_path:
                env["PUPPETEER_EXECUTABLE_PATH"] = chrome_path

            result = subprocess.run(
                [
                    "mmdc",
                    "-i",
                    str(temp_input_path),
                    "-o",
                    str(temp_output_path),
                ],
                capture_output=True,
                text=True,
                timeout=30,
                env=env,
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() or result.stdout.strip()
                return False, f"Mermaid syntax validation failed: {error_msg}"

            return True, ""

        finally:
            # Clean up temporary files
            if temp_input_path.exists():
                temp_input_path.unlink()
            if temp_output_path.exists():
                temp_output_path.unlink()

    except subprocess.TimeoutExpired:
        logger.error("Validation timed out after 30 seconds")
        if temp_input_path.exists():
            temp_input_path.unlink()
        if temp_output_path.exists():
            temp_output_path.unlink()
        return False, "Validation timed out - diagram may be too complex"

    except FileNotFoundError:
        logger.error("mermaid-cli (npx) not found in system")
        return False, "mermaid-cli is not installed or not found in PATH"

    except Exception as e:
        logger.error(f"Unexpected error during validation: {str(e)}")
        if temp_input_path.exists():
            temp_input_path.unlink()
        if temp_output_path and temp_output_path.exists():
            temp_output_path.unlink()
        return False, f"Validation failed with unexpected error: {str(e)}"


def generate_diagram(
    mermaid_content: str,
    output_path: Path,
    format: str = "png",
    scale: int = 3,
    width: int = 2400,
) -> bool:
    """
    Generate a diagram image from Mermaid syntax.

    This function takes Mermaid diagram content and generates either a PNG or SVG
    output file using the mermaid-cli tool (mmdc command via npx).

    Args:
        mermaid_content: The Mermaid diagram syntax as a string
        output_path: Path where the output diagram should be saved
        format: Output format, either "png" or "svg" (default: "png")
        scale: Scale factor for PNG output (default: 3 for high resolution)
        width: Width of the output image in pixels (default: 2400)

    Returns:
        True if diagram generation was successful, False otherwise

    Raises:
        No exceptions are raised; all errors are logged and result in False return

    Example:
        >>> mermaid = "graph TD\\nA[Start] --> B[End]"
        >>> output = Path("diagram.png")
        >>> success = generate_diagram(mermaid, output, "png", scale=3)
        >>> if success:
        ...     print("Diagram generated successfully")
    """
    # Validate inputs
    if not mermaid_content or not mermaid_content.strip():
        logger.error("Cannot generate diagram: Mermaid content is empty")
        return False

    if format not in ["png", "svg"]:
        logger.error(f"Unsupported output format: {format}. Use 'png' or 'svg'")
        return False

    # Convert output_path to Path object if it's a string
    output_path = Path(output_path)

    # Check if output directory exists and is writable
    output_dir = output_path.parent
    if not output_dir.exists():
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created output directory: {output_dir}")
        except PermissionError:
            logger.error(f"Permission denied: Cannot create directory {output_dir}")
            return False
        except Exception as e:
            logger.error(f"Failed to create output directory {output_dir}: {str(e)}")
            return False

    # Check write permissions
    try:
        # Test write permission by attempting to create a temporary file
        test_file = output_dir / f".test_write_{output_path.name}"
        test_file.touch()
        test_file.unlink()
    except PermissionError:
        logger.error(f"Permission denied: Cannot write to directory {output_dir}")
        return False
    except Exception as e:
        logger.error(f"Cannot write to directory {output_dir}: {str(e)}")
        return False

    # Create temporary input file with Mermaid content
    temp_input_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".mmd", delete=False
        ) as temp_input:
            temp_input_path = Path(temp_input.name)
            temp_input.write(mermaid_content)
            logger.debug(f"Created temporary input file: {temp_input_path}")

    except Exception as e:
        logger.error(f"Failed to create temporary input file: {str(e)}")
        return False

    # Run mermaid-cli to generate diagram
    try:
        logger.info(
            f"Generating {format.upper()} diagram from Mermaid content to {output_path}"
        )

        # Build command with scale and width parameters for high resolution
        cmd = [
            "mmdc",
            "-i",
            str(temp_input_path),
            "-o",
            str(output_path),
            "-s",
            str(scale),
            "-w",
            str(width),
        ]

        # Set Puppeteer environment variables to use installed Chrome
        env = os.environ.copy()
        chrome_path = find_chrome_executable()
        if chrome_path:
            env["PUPPETEER_EXECUTABLE_PATH"] = chrome_path
            logger.debug(f"Using Chrome executable: {chrome_path}")
        else:
            logger.debug(
                "No Chrome executable found, relying on Puppeteer auto-detection"
            )

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            env=env,
        )

        if result.returncode != 0:
            error_output = result.stderr.strip() or result.stdout.strip()
            logger.error(
                f"mermaid-cli failed with return code {result.returncode}: {error_output}"
            )

            # Check for specific error patterns and use fallback where appropriate
            if "syntax" in error_output.lower() or "parse" in error_output.lower():
                logger.error("Invalid Mermaid syntax detected - cannot use fallback")
                return False
            elif "could not find chrome" in error_output.lower():
                logger.warning("Chrome not available, falling back to kroki.io API")
                return generate_diagram_via_kroki(mermaid_content, output_path, format)
            elif (
                "not found" in error_output.lower()
                or "command not found" in error_output.lower()
            ):
                logger.warning("mermaid-cli not found, falling back to kroki.io API")
                return generate_diagram_via_kroki(mermaid_content, output_path, format)

            # For other errors, try kroki.io fallback
            logger.info("Attempting fallback to kroki.io API...")
            return generate_diagram_via_kroki(mermaid_content, output_path, format)

        # Verify output file was created
        if not output_path.exists():
            logger.error(
                f"Diagram generation completed but output file not found: {output_path}"
            )
            return False

        # Verify output file has content
        if output_path.stat().st_size == 0:
            logger.error(f"Generated diagram file is empty: {output_path}")
            output_path.unlink()  # Remove empty file
            return False

        logger.info(f"Successfully generated diagram: {output_path}")
        return True

    except subprocess.TimeoutExpired:
        logger.error("Diagram generation timed out after 60 seconds")
        logger.info("Attempting fallback to kroki.io API...")
        return generate_diagram_via_kroki(mermaid_content, output_path, format)

    except FileNotFoundError:
        logger.warning(
            "mermaid-cli not found locally, using kroki.io API fallback"
        )
        return generate_diagram_via_kroki(mermaid_content, output_path, format)

    except Exception as e:
        logger.error(f"Unexpected error during diagram generation: {str(e)}")
        logger.info("Attempting fallback to kroki.io API...")
        return generate_diagram_via_kroki(mermaid_content, output_path, format)

    finally:
        # Clean up temporary input file
        if temp_input_path and temp_input_path.exists():
            try:
                temp_input_path.unlink()
                logger.debug(f"Cleaned up temporary file: {temp_input_path}")
            except Exception as e:
                logger.warning(
                    f"Failed to clean up temporary file {temp_input_path}: {str(e)}"
                )
