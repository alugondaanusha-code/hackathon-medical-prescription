powershell -Command "@'
import os

# tokens (read from env by default; can also be sent from the UI per-request)
HF_TOKEN = os.getenv("HF_TOKEN", "")
IBM_API_KEY = os.getenv("IBM_API_KEY", "")
IBM_URL = os.getenv("IBM_URL", "")  # e.g., https://<region>.watsonplatform.net/... or watsonx endpoint

# ports/URLs
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_URL = f"http://{API_HOST}:{API_PORT}"
'@ | Set-Content -Encoding UTF8 config.py"
