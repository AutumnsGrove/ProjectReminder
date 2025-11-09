"""
config.py - Configuration management

Loads secrets from secrets.json with fallback to environment variables.
"""

import os
import json
from pathlib import Path


def load_secrets():
    """
    Load API keys and secrets from secrets.json.

    Falls back to environment variables if file not found.

    Returns:
        Dictionary of secrets
    """
    secrets_path = Path(__file__).parent.parent / "secrets.json"
    try:
        with open(secrets_path, 'r') as f:
            secrets = json.load(f)
        print(f"SUCCESS: Loaded secrets from {secrets_path}")
        return secrets
    except FileNotFoundError:
        print(f"WARNING: secrets.json not found at {secrets_path}. Using environment variables as fallback.")
        return {}
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse secrets.json: {e}. Using environment variables as fallback.")
        return {}


# Load secrets at module import
SECRETS = load_secrets()

# Database
DB_PATH = Path(__file__).parent.parent / "reminders.db"

# Authentication
API_TOKEN = SECRETS.get("api_token", os.getenv("API_TOKEN", ""))

# MapBox
MAPBOX_ACCESS_TOKEN = SECRETS.get("mapbox_access_token", os.getenv("MAPBOX_ACCESS_TOKEN", ""))

# CORS (allow local development)
# Add your Tailscale/VPN IP to this list if needed for remote access
CORS_ORIGINS = [
    "http://localhost:3077",
    "http://localhost:8080",
    "http://127.0.0.1:3077",
    "http://127.0.0.1:8080",
    "http://100.114.120.17:3077",  # Tailscale mesh network
    "http://100.114.120.17:8080",  # Tailscale mesh network
    "null"  # For file:// protocol during development
]

# Optionally add custom origins from environment
if custom_origin := os.getenv("CUSTOM_CORS_ORIGIN"):
    CORS_ORIGINS.append(custom_origin)

# Server
HOST = "0.0.0.0"
PORT = 8000
DEBUG = True

# API Configuration
API_VERSION = "v1"
API_PREFIX = "/api"
