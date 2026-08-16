"""
config.py
Configuration with comprehensive debugging (OpenAI version only)
"""

import os
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    env_path = Path('.') / '.env'
    load_dotenv(dotenv_path=env_path, verbose=True)
    print(f"✅ .env loaded successfully from: {env_path.absolute()}")
except Exception as e:
    print(f"⚠️ Failed to load .env: {e}")

class Config:
    """Application configuration - OpenAI only"""

    def __init__(self):
        # Read OpenAI settings
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
        self.OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        # Feature Flags
        self.USE_LLM_EXTRACTION = (
            os.getenv("USE_LLM_EXTRACTION", "true").lower() == "true"
        )

        # API runtime settings
        self.API_HOST = os.getenv("API_HOST", "127.0.0.1")
        self.API_PORT = int(os.getenv("API_PORT", "8000"))

        # Debug info
        print("\n" + "=" * 70)
        print("🔧 CONFIGURATION LOADED (OpenAI)")
        print("=" * 70)
        print(f"USE_LLM_EXTRACTION: {self.USE_LLM_EXTRACTION}")
        print(f"OPENAI_MODEL: {self.OPENAI_MODEL}")
        print(f"OPENAI_API_KEY present: {bool(self.OPENAI_API_KEY)}")
        if self.OPENAI_API_KEY:
            print(f"  → Key starts with: {self.OPENAI_API_KEY[:8]}")
            print(f"  → Key ends with: ...{self.OPENAI_API_KEY[-4:]}")
        else:
            print("  → ❌ NO OPENAI KEY FOUND — system will fail on LLM calls")
        print("=" * 70 + "\n")


# Global config instance
config = Config()
