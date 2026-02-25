import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# Loaded from .env for local dev; falls back to hardcoded URL inside APK
# (APK bundles compiled Python — .env is not reliably accessible at runtime)
API_BASE_URL: str = os.environ.get(
    "API_BASE_URL",
    "https://weather.danielkravchenko.dev/api/v1",
)
