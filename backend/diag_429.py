"""
Diagnostic: make ONE controlled AI generation request through the full stack.
Captures complete error metadata if 429 occurs.
"""
import sys, logging, os, json
sys.path.insert(0, os.path.dirname(__file__))

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

from app.config import settings

print("=" * 60)
print("429 DIAGNOSTIC: Pre-request Configuration Check")
print("=" * 60)

# 1. Verify model at runtime
print(f"\n[1] Runtime settings.GEMINI_MODEL = {settings.GEMINI_MODEL!r}")
print(f"[1] Config default               = 'gemini-2.0-flash'")
print(f"[1] .env value                    = 'gemini-3.5-flash-lite'")
print(f"[1] OVERRIDE ACTIVE               = {settings.GEMINI_MODEL != 'gemini-2.0-flash'}")

# 2. API key prefix (safe - only first 10 chars)
api_key = (settings.GEMINI_API_KEY or "").strip()
key_prefix = api_key[:15] + "..." if len(api_key) > 15 else "(empty)"
print(f"\n[2] GEMINI_API_KEY present: {bool(api_key)}")
print(f"[2] GEMINI_API_KEY prefix: {key_prefix}")
print(f"[2] Key format suggests: {'Google Cloud API key (AQ prefix)' if api_key.startswith('AQ.') else 'Unknown format'}")

# 3. Make ONE request through the exact same code path
print(f"\n[3] Making ONE controlled request...")
from app.providers.factory import get_provider, reset_provider
reset_provider()
provider = get_provider()

print(f"[3] Provider class: {provider.__class__.__name__}")
print(f"[3] Provider model: {provider.model_name!r}")

try:
    result = provider.generate_cold_email(
        recipient_name="Test User",
        recipient_role="Engineer",
        recipient_company="TestCorp",
        tone="professional",
    )
    print(f"\n[3] RESULT: SUCCESS (no 429)")
    print(f"[3] Subject: {result.get('subject', '')[:100]!r}")
    print(f"[3] Body starts: {result.get('body', '')[:80]!r}...")
except Exception as e:
    print(f"\n[3] RESULT: FAILED")
    print(f"[3] Exception type: {type(e).__name__}")
    print(f"[3] Exception str: {e}")
    status_code = getattr(e, "status_code", None)
    print(f"[3] status_code attr: {status_code}")
    if hasattr(e, "message"):
        print(f"[3] .message attr: {getattr(e, 'message')}")
    # Try to dig deeper into the error
    if hasattr(e, "details") and e.details:
        print(f"[3] .details: {e.details}")
    if hasattr(e, "args") and e.args:
        for i, arg in enumerate(e.args):
            print(f"[3] .args[{i}]: {arg}")
    if hasattr(e, "body"):
        try:
            body = json.loads(e.body) if isinstance(e.body, str) else e.body
            print(f"[3] .body: {json.dumps(body, indent=2)}")
        except:
            print(f"[3] .body: {e.body[:500] if isinstance(e.body, str) else e.body}")

print(f"\n{'=' * 60}")
print("DIAGNOSTIC COMPLETE")
print(f"{'=' * 60}")
