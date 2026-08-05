"""Test harness configuration.

Every test module constructs ``TestClient(app)`` from the shared ``app`` object
in ``app.main``. The app's slowapi Limiter is a process-wide singleton that uses
in-memory storage, so when a full suite runs, every test shares the same rate-limit
window. The unauthenticated ``/api/auth/login`` limit (10/minute keyed by IP) is
quickly exhausted across many tests, causing spurious 429s and cascading failures
that are purely a test-environment collision, not a real bug.

To make the suite deterministic regardless of how many tests run in sequence, we
mark this process as a test environment. ``app.config`` reads the ``TESTING`` env
var and the Limiter is constructed with ``enabled=not settings.TESTING``, so the
limiter is disabled for the whole suite. Production is unaffected: it runs with
``TESTING=False`` (the default) and the limiter stays enabled.

The two tests that deliberately verify 429 enforcement (``test_rate_limiting.py``
and ``test_profile_settings.py``) opt back in by setting ``limiter.enabled = True``
for their own scope and restoring it afterwards.
"""

import os


def pytest_configure(config):
    """Set the test-environment flag before any test module imports the app."""
    os.environ["TESTING"] = "true"