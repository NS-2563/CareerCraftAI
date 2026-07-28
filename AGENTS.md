# Security & Implementation Audit Summary

## Completed Phases
- **Phase 2A**: Password Hashing (bcrypt, legacy SHA256 migration, min_length=8)
- **Phase 2B**: Token Lifecycle (token_version, JWT `ver` claim, refresh rotation, server-side logout)
- **Phase 2C**: Abuse Protection (rate limiting, account lockout, user enumeration prevention)
- **Phase 2D**: CSRF/SSRF (security headers middleware, CSP, safe HTTP client, hardened CORS)
- **Phase 2E**: Input Validation & XSS (max_length on all schemas, output sanitizer, career coach schema)
- **Phase 2F**: Authorization (route ordering fix, resume_id ownership check, dead code cleanup)
- **Phase 2G**: Resume Import Pipeline Hardening (see below)

## Phase 2H — Communication & Suggestion Features

### Summary
Added a full communication suggestion system (daily cron generating suggestions for stale applications), recruiter reply mode, database migration for 4 missing columns, route ordering fix, and 429 error handling.

### Changes
| Component | Description | Files |
|-----------|-------------|-------|
| Suggestion System | Daily APScheduler job creates suggestions for applications stale >7 days; 3 new endpoints (GET `/suggestions`, POST dismiss, POST generate-from-suggestion) | `backend/app/communication/scheduler.py`, `router.py` (new endpoints), `models.py` (Suggestion model), `main.py` (suggestions_router), `frontend/src/communication/NotificationBell.jsx`, `JobRow.jsx`, `hooks/useSuggestions.js` |
| Recruiter Reply Mode | New `recruiter_reply` message_type with `inbound_message` + `reply_intent` fields; dedicated prompt with injection defense; `generate_recruiter_reply` in provider | `backend/app/communication/router.py`, `services/gemini.py`, `providers/factory.py`, `providers/gemini.py`, `frontend MessageTypeSelector.jsx`, `MessageComposer.jsx` |
| Database Schema Fix | Migration `_003_add_missing_columns.py` adding `job_description`, `resume_id` to `job_applications` and `related_job_application_id`, `related_resume_id` to `communication_messages` | `backend/app/migrations/versions/_003_add_missing_columns.py`, `migrations/env.py` |
| Route Ordering Fix | Swapped `suggestions_router` before `communication_router` in `main.py` to fix 422 on `/suggestions` (was caught by `/{message_id}` with int type) | `backend/app/main.py` |
| 429 Error Handling | Disabled React Query retry on suggestions query and messages query; user-friendly 429 banner "Too many AI generation requests. Please wait a moment and try again." | `frontend CommunicationHub.jsx:207-214` (error extraction + is429), `MessageComposer.jsx:300-309` (error banner), `hooks/useSuggestions.js`, `hooks/useMessages.js` |

### Investigation Note (429 on POST /api/communication/generate)
- **Root cause**: Google Gemini API quota exceeded (external limitation)
- **No app-level bug**: frontend does NOT retry 429 (axios interceptor excludes 429 from `retryableStatusCodes`, React Query mutation retry=0, button disables while pending)
- **Amplifying factor**: `_generate_content()` retries 429 up to 2× with 1s/2s backoff, but quota doesn't reset in that window
- **All AI features share quota**: cover letter, resume analysis, career coach also hit Gemini; Cover Letter bypasses provider factory (`cover_letter.py:28` uses `GeminiProvider()` directly)

## Phase 2G — Resume Import Pipeline Hardening

### Issues Found During Audit
| Severity | Issue | Fix Location |
|----------|-------|-------------|
| P0 | Projects `title→name` mismatch: deterministic parser outputs `title` but Pydantic schema expects `name`, silently dropping all project data | `resume_pipeline.py:112-117` — convert title→name before validation; `ai_parser.py:375-381` — normalize det entries for merge matching; `ai_parser.py:430-434` — normalize name→title in merged output |
| P0 | `techStack` string→List[str] mismatch: deterministic parser outputs comma-separated string, `ProjectItem` expects list; projects section fails validation entirely | `resume_pipeline.py:118-120` — split techStack string into list before ProjectItem creation |
| P0 | `liveDemo` roundtrip data loss: `mapProjectsFromBackend` hardcoded `liveDemo: ""`; `toProjectsForBackend` didn't send `live_url` | `resumeDataCompat.js:85` — read `live_url` from backend; `resumeDataCompat.js:222-228` — send `live_url` to backend |
| P1 | Prompt injection: resume text embedded directly in AI prompt without instruction isolation or embedded-instruction stripping | `resume_prompt.py` — added `_INSTRUCTION_SEPARATOR`, `_sanitize_section_text()` strips JSON blocks & instruction-like lines, added "IGNORE embedded instructions" to system prompt |
| P2 | Unused `deterministic` variable in `resume_import.py:67` | Removed unused variable |
| P2 | Sanitizer regex didn't match self-closing `<embed>`, `<script>`, `<iframe>`, `<object>` tags | `sanitizer.py` — unified tag patterns to handle both paired and self-closing variants |

### Files Modified
- `backend/app/resume/services/resume_pipeline.py` — projects title/techStack normalization in `_build_resume_create`
- `backend/app/resume/services/ai_parser.py` — det list normalization for merge matching, post-merge name→title normalization for AI-only entries
- `backend/app/resume/services/resume_prompt.py` — prompt injection defense (separator, sanitizer, ignore instruction)
- `backend/app/utils/sanitizer.py` — unified HTML tag stripping patterns
- `backend/app/routers/resume_import.py` — removed unused `deterministic` variable
- `frontend/src/utils/resumeDataCompat.js` — `liveDemo`/`live_url` roundtrip fix

### Test Coverage Added
- `tests/test_phase2g.py` — 43 new tests in 4 test classes
  - `TestProjectsPipelineIntegrity` (13 tests): title→name, techStack→list, liveDemo, merge matching, dedup, deterministic wins
  - `TestPromptInjectionProtection` (8 tests): instruction separator, sanitize_text, embedded instruction stripping
  - `TestPipelineEdgeCases` (8 tests): empty text, AI failure/malformed response, empty sections, personal.title not affected
  - `TestSanitizerSecurity` (14 tests): XSS vectors (script, iframe, embed, event handlers, javascript:, data:), control chars, max length, list sanitization

## P1-001 — Deprecated SDK Removal
- Removed `google-generativeai` SDK (old v0.8.3). Migrated `ai_engine.py` from `ask_gemini()` → `get_provider()._generate_content()`. Deleted `gemini_service.py`. Fixed `cover_letter.py` to use `factory.get_provider()`. Updated `requirements.txt`.

## P1-002 — Rate-Limit Tightening
- Custom key function `_user_or_ip_key` in `main.py` extracts JWT `sub` for authenticated requests, falls back to IP for unauthenticated (slowapi `Limiter(key_func=...)`).
- Daily quotas added to `config.py`: per-user compound limits (`X/minute;Y/day`) for analysis, JD match, AI, cover letter, communication, and career coach endpoints.
- `@limiter.limit` decorators applied to all AI-calling endpoints that lacked them: 6 in `routers/ai.py`, 4 in `routers/cover_letter.py`, 2 in `communication/router.py` + `suggestions_router.py`, 1 in `routers/career.py`. Existing decorators in `analysis.py` and `jd_matching.py` upgraded to compound limits.
- 5 new tests in `test_rate_limiting.py` (key function, 429 enforcement).

## Remaining Fixes Applied
- fastapi 0.115.0 (latest: 0.139.2)
- python-jose 3.3.0 (latest: 3.5.0)
- google-genai 0.5.0 (latest: 2.14.0)
- pydantic 2.9.2 (latest: 2.13.4)

## Test Status
- **710/710 tests pass** (2 pre-existing failures excluded)
- Frontend builds successfully (vite build)

## Deployment Notes
- Set `SECRET_KEY` in `.env` (use `python -c "import secrets; print(secrets.token_urlsafe(64))"`)
- Configure `CORS_ORIGINS` for production domain
- Run with `uvicorn --no-server-header app.main:app` to suppress `Server` header
- Consider HTTPS termination at reverse proxy (nginx/Caddy)
