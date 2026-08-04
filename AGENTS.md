# Security & Implementation Audit Summary

## Phase 11 — Job Application Workspace Layout Refinement

### Summary
Reworked the Job Application workspace into a three-block layout above the tabs: a deterministic "next recommended action" banner (fixed decision tree over real completion state — never AI), dismissible `InsightCard`s surfaced from data that already exists (JD match gaps, resume analysis suggestions), and a per-application Recent Activity feed. Insight dismissals are persisted so a dismissed card does not reappear, and the next-action banner updates in place whenever the underlying state changes (JD saved, match run, cover letter generated, message logged, interview logged).

### Changes
| Component | Description | Files |
|-----------|-------------|-------|
| Decision tree | `recommend_next_action(state)` — pure, deterministic: R0 terminal status (Accepted/Rejected/Withdrawn) → `None`; R1 no saved JD → `save_job_description`; R2 no linked resume → `link_resume`; R3 no JD match → `run_jd_match`; R4 no cover letter → `generate_cover_letter`; R5 active pursuit + no communication + `days_since_applied > 7` → `send_follow_up` (date unknown ⇒ never fires); R6 interview status + no interview activity → `practice_interview`; R7 complete → `None`. Returns `key`/`title`/`description`/`cta`/`tab` | `backend/app/job_tracker/next_action.py` |
| Workspace service | `recommend_next_action_for_job` (counts real cover letters/messages/interview sessions via `get_latest_result`), `build_insight_cards` (JD gaps from `match_result.missing_skills`, resume suggestions from `analysis_json["suggestions"]`, `MAX_INSIGHT_REASONS=6` + `extra_count`), `get_dismissed_keys`, `dismiss_insight` (idempotent), `build_workspace_payload` (filters dismissed keys) | `backend/app/job_tracker/workspace.py` |
| Dismissal persistence | `insight_dismissals` table: `(user_id, job_application_id, insight_key)` unique, FK `ondelete CASCADE`, gated+idempotent migration `_018`, registered in `database.py` | `backend/app/models/insight_dismissal.py`, `backend/app/migrations/_018_add_insight_dismissals.py`, `app/database.py` |
| Router | `GET /api/jobs/{job_id}/workspace` (next_action + non-dismissed insights + dismissed keys) and `POST /api/jobs/{job_id}/workspace/insights/{key}/dismiss` (returns updated dismissed list), both ownership-checked (404 on foreign application) | `backend/app/routers/job_tracker.py` |
| API client | `getWorkspaceInsights(jobId)`, `dismissWorkspaceInsight(jobId, insightKey)` | `frontend/src/modules/jobTracker/api/jobTrackerApi.js` |
| Workspace hook | `useWorkspace` (query key `["workspace", jobApplicationId]`), `useDismissWorkspaceInsight` (invalidates on success) | `frontend/src/modules/jobTracker/hooks/useWorkspace.js` |
| Next-action banner | `NextActionBanner` renders the recommendation with a per-key icon/accent and a CTA that navigates to the matching tab (`onNavigate(tab)`); renders `null` when there is no action | `frontend/src/modules/jobTracker/components/NextActionBanner.jsx` |
| Insight cards | `WorkspaceInsights` maps the payload to dismissible `InsightCard`s (atoms), with an X button that calls the dismiss mutation; reasons list shows the real stored reasons + "+N more" for the cap overflow | `frontend/src/modules/jobTracker/components/WorkspaceInsights.jsx` |
| Activity feed | `ApplicationActivityFeed` renders the real per-application activity via `activityApi.getFeed({ jobApplicationId })` into the `Timeline` atom with module icons/accents | `frontend/src/modules/jobTracker/components/ApplicationActivityFeed.jsx` |
| Workspace wiring | `ApplicationLinkedResources` renders banner → insights → checklist → tabs in the body and the activity feed after Job details; invalidates `["workspace", job.id]` on JD save, match re-run, resume link, cover letter generate, real-interview log; dismiss button disabled while pending | `frontend/src/modules/jobTracker/components/ApplicationLinkedResources.jsx` |
| Communication invalidation | message save in `ReplyComposerDialog` and inbound log via `useLogInbound` also invalidate `["workspace", jobId]` so `send_follow_up` clears once outreach is logged | `frontend/src/communication/components/ApplicationCommunicationThread.jsx`, `frontend/src/communication/hooks/useLogInbound.js` |

### Design Decisions
- **The "next action" is never an AI decision** — it is a fixed, documented decision tree evaluated over real completion state (which fields exist, what is recorded). Given identical state it always returns the same recommendation; there is no time/effort estimate or quality score anywhere.
- **Insight cards reuse existing derivations** — JD gaps come from the stored `JDMatchResult.missing_skills`; resume suggestions come from the stored `ResumeAnalysis.analysis_json["suggestions"]`. No new extractor, no new AI call, no invented score.
- **Dismissals persist per user+application** (`unique(user_id, job_application_id, insight_key)`), so a dismissed card does not reappear on reload or after a refresh; re-running the match does not resurrect a dismissed key.
- **Follow-up rule is date-safe**: `days_since_applied` prefers `applied_date`, falls back to `created_at`, and returns `None` when unknown so the rule never fires on missing dates. Active-pursuit statuses only (Applied/Interview/Offer) — never Wishlist.
- The workspace payload (next action + non-dismissed insights + dismissed keys) is a single fetch per application; the three UI blocks render from it without extra round-trips.

### Test Coverage
- `backend/tests/test_workspace_next_action.py` — 37 tests in 3 classes: decision tree (20: every branch R0–R7, terminal-wins, follow-up threshold boundary incl. exactly N days, unknown date, Wishlist non-firing, determinism), insight/dismissal service (9: JD gap card + reason cap, resume suggestions card, dismiss persistence + idempotency + per-application scoping), API (8: auth required, bare-job → `save_job_description`, full-completion → `None`, interview → `practice_interview`, dismiss → does-not-reappear, 404 IDOR on foreign application for GET + dismiss, 401). Full related run `test_score_diff.py + test_conversation_status.py + test_job_description.py + test_activity.py + test_workspace_next_action.py` → 121 passed. Frontend `eslint .` clean + `vite build` succeeds (only pre-existing chunk-size warnings).

## Phase 11 Follow-on — Communication Provenance, Thread Summary & Timeline Interleave

### Summary
Gave Communication a real provenance field (`generation_method`), a deterministic per-application thread summary (last reply / last recruiter email / response-overdue) with a single documented overdue threshold, and reworked the per-application Communication timeline into one `Timeline`-atom view that interleaves messages with interview events (real-interview logs + practice sessions tied to the application). The thread summary is surfaced as chips in the workspace Communication section and on Communication Hub cards, and outbound AI-generated messages carry an "AI" badge in both places.

### Changes
| Component | Description | Files |
|-----------|-------------|-------|
| `generation_method` column | `communication_messages.generation_method VARCHAR(20) NOT NULL DEFAULT 'manual'`; gated + idempotent migration (existing rows backfill `manual`); `CommunicationMessageResponse` exposes it | `backend/app/models/communication_models.py`, `backend/app/migrations/_019_add_generation_method.py`, `app/database.py`, `backend/app/communication/schemas.py` |
| Provenance set per path | `create_from_generation` → `ai_generated`; manual `create` → `manual`; `log_inbound` → `manual`; `duplicate` copies `original.generation_method` (AI drafts duplicate as AI) | `backend/app/communication/service.py` |
| Thread summary module | `compute_thread_summary(messages)` — pure/deterministic: most-recent message by `(created_at, id)`, most-recent inbound, single overdue rule, coarse `state` (`none`/`waiting`/`needs_reply`/`response_overdue`); `attach_thread_summary(db, messages)` batch-computes over each app's FULL thread (one query) so a paginated hub slice never truncates the source | `backend/app/communication/thread_summary.py` |
| Overdue rule (documented) | `settings.COMMUNICATION_OVERDUE_AFTER_DAYS = 5`; overdue ⇔ most recent message is inbound AND `> 5` whole days since it with no outbound after; at exactly N days NOT overdue. Never fires on missing timestamps. | `backend/app/config.py` |
| Router wiring | `get_thread` + `list_messages` chain `attach_thread_summary` after `attach_conversation_status` | `backend/app/communication/router.py` |
| Sessions-for-application API | `InterviewPrepService.list_sessions_for_application` (both `practice` + `real_interview` tied to the app, oldest first) + `GET /api/interview-prep/applications/{id}/sessions` (ownership-checked 404) | `backend/app/interview_prep/service.py`, `backend/app/interview_prep/router.py` |
| `Timeline` atom extension | Backward-compatible optional `item.content` renderer (renders below subtitle) — existing callers unaffected | `frontend/src/components/ui/atoms.jsx` |
| StatusBadge fix | Added `needs_reply` (underscore) to `STATUS_META` so conversation-status badges render the soft amber badge instead of the outline fallback | `frontend/src/components/ui/atoms.jsx` |
| Thread rework | `ApplicationCommunicationThread` now renders the merged timeline via the `Timeline` atom: message items (author, subject, full body via `content`, inbound rows linkable → Generate AI Reply dialog) interleaved with interview items (real-interview how-it-went / practice score) by timestamp; `ThreadSummaryChips` row (Last reply / Last recruiter email / Needs your reply / Waiting / Response overdue · Nd) above the list; `AiBadge` on `ai_generated` outbound items | `frontend/src/communication/components/ApplicationCommunicationThread.jsx` |
| Hub cards | `MessageCard` shows `AiBadge` on AI-generated outbound messages + compact `ThreadSummaryChips` row (incl. overdue state) from `message.thread_summary` | `frontend/src/communication/pages/CommunicationHub.jsx` |
| New API + hook | `listApplicationSessions(jobApplicationId)` + `useApplicationSessions` (query key `["applicationSessions", jobApplicationId]`); **fix**: `useRealInterviews` previously checked `result?.success` on a plain-array response and silently returned `[]` — now `Array.isArray` | `frontend/src/modules/interview/services/interviewSessionApi.js`, `frontend/src/modules/jobTracker/hooks/useApplicationSessions.js`, `useRealInterviews.js` |

### Design Decisions
- **Provenance is persisted data** — the AI path is the only caller of `create_from_generation`, so it alone tags `ai_generated`; manual create + manual inbound both tag `manual`. Duplicates carry the source's method. No heuristic "was this AI?" guessing.
- **Thread summary is never a stored/AI value** — always `compute_thread_summary` over the real full thread, recomputed per request; identical rows → identical summary (order-independent).
- **Single documented overdue threshold** (`COMMUNICATION_OVERDUE_AFTER_DAYS = 5`, strictly-greater-than). The summary's `response_overdue`/`state` and every frontend chip read from it; no second threshold anywhere.
- **One timeline, one atom** — the per-application view uses the same `Timeline` atom as the cross-module Activity Timeline; interview events (via the new sessions endpoint) merge with messages by timestamp. No second timeline rendering component.
- Manual-create endpoints already existed (`POST /api/communication` manual + `POST /log-inbound` manual inbound), so only the AI path needed tagging.

### Test Coverage
- `backend/tests/test_thread_summary.py` — 27 tests in 5 classes: pure summary (12: empty, outbound→waiting, inbound→needs_reply, overdue boundary exactly-5-not-overdue / day-6-overdue / long-overdue days, reply-after-inbound clears overdue, missing-date never overdue, most-recent-inbound selection, id-tiebreaker, order-independence, determinism), generation_method per path (4: manual create / AI generate / manual inbound / duplicate copies), attach_thread_summary (2), thread-summary API (3: thread + list carry `generation_method`+`thread_summary`, generate tags `ai_generated`), application-sessions API (4: both types, per-app scoping, 404 IDOR, 401). Focused run `test_thread_summary.py + test_communication_threads.py + test_conversation_status.py + test_real_interviews.py` → 94 passed. Full suite (excluding documented pre-existing JD-matching failures) 1034 passed. Frontend `eslint` clean + `vite build` succeeds (only pre-existing warnings).

## Phase 10 — Cover Letter Studio Transparency & Saved-Letters Library

### Summary
Made the Cover Letter Studio trustworthy and transparent: the actual AI provider/model and real generation timestamp are persisted and shown, a deterministic ATS keyword-coverage count reuses the existing JD-matcher keyword extractor, a real before/after line diff is computed between versions, a pre-flight check gates the Generate button on missing inputs, and a new Cover Letter Library page (mirroring Resume Library) gives search/filter/archive/versions over every saved letter. Every displayed metric is stored data or a deterministic derivation — no new AI-judged quality scores, no "reading level".

### Changes
| Component | Description | Files |
|-----------|-------------|-------|
| Metadata columns + migration | `cover_letters.ai_provider VARCHAR(50)`, `model_name VARCHAR(100)`, `generated_at TIMESTAMPTZ` (nullable); migration gated + idempotent; `CoverLetterResponse` + AI response schemas expose them (`protected_namespaces=()` to silence pydantic warning) | `backend/app/models/cover_letter.py`, `backend/app/migrations/_017_add_cover_letter_generation_metadata.py`, `app/database.py`, `backend/app/schemas/cover_letter.py`, `schemas/cover_letter_ai.py` |
| ATS keyword coverage | `compute_keyword_coverage(job_description, letter_content)` **reuses `_extract_keywords` from the JD matcher** (same `_STOP_WORDS`, same normalization — no second extractor); returns covered/missing keyword lists + `"N of M keywords present"` label, or `"No job description to check"` when total=0 | `backend/app/services/cover_letter_ats.py`, reuse of `app/analysis/deterministic/jd_matcher.py` |
| Version diff | `compute_cover_letter_diff(from_text, to_text)` via `difflib.SequenceMatcher` line opcodes → added/removed line counts, word-count delta, per-hunk changes; mirrors the resume score-history diff approach | `backend/app/services/cover_letter_diff.py`, `app/analytics/service.py` |
| Service additions | `check_generation_prerequisites` (missing list: `["resume","job title","company name","job description"]`, whitespace-aware); `get_version_content` (current = live column, historical = snapshot `data.content`) | `backend/app/services/cover_letter_service.py` |
| Router | `_provider_metadata(provider)` helper (class name minus `Provider` + `provider.model_name`); `POST /api/cover-letter/preflight`; `GET /{id}/ats-coverage`; `GET /{id}/diff?from_version&to_version` (400 same version, 404 unknown version, ownership-scoped); saving `/generate` and `/apply-edit` now persist + return metadata and `ats_coverage` (commit+refresh after update); GET detail returns `ats_coverage` | `backend/app/routers/cover_letter.py` |
| Bug fix | `POST /{id}/generate` had `response_model=CoverLetterGenerateRequest` (wrong type) → now `CoverLetterResponse`; removed unused `CoverLetterGenerateRequest`/`CoverLetterAIEditsRequest` imports | `backend/app/routers/cover_letter.py` |
| Pre-flight checklist UI | `CoverLetterChecklist` calls the preflight endpoint (350ms debounce) → `ChecklistProgress` of the 4 required inputs → `onReadyChange` gates the Generate button on real backend data (not client-only) | `frontend/src/components/coverLetter/CoverLetterChecklist.jsx` |
| Output-view metadata | `CoverLetterMetadata` footer: tone badge, real provider/model, generated timestamp, linked resume, ATS coverage count with expandable covered/missing keyword chips, and a job-application link badge with a setter/unlink (via `updateCoverLetter`) | `frontend/src/components/coverLetter/CoverLetterMetadata.jsx` |
| Diff view | `CoverLetterDiffView` renders the deterministic `v{from} → v{to}` line changes (green added / red removed / word delta); loaded automatically after regenerate/AI-edit | `frontend/src/components/coverLetter/CoverLetterDiffView.jsx` |
| Builder wiring | Builder now uses the saving `/generate` endpoint, tracks `generateReady`/`atsCoverage`/`diffData`, resets them on selection, deep-links via `?id=` / `?create=1` (URL params), and links to the library | `frontend/src/components/coverLetter/CoverLetterBuilder.jsx` |
| Toolbar gating | Generate button disabled with a tooltip until the checklist is complete | `frontend/src/components/coverLetter/CoverLetterToolbar.jsx` |
| API client | `searchCoverLetters(query, includeArchived, sort)` (`/search?q&include_archived&sort`), `listArchivedCoverLetters`, `preflightCoverLetter`, `getAtsCoverage`, `getCoverLetterDiff` | `frontend/src/services/coverLetterApi.js` |
| Library page + routing | `CoverLetterLibrary` mirrors Resume Library: search/sort/filter (active/archived), cards with tone/template/job-link/metadata, rename/duplicate/version-history-restore/archive/delete; routed `/cover-letter-library` + registered in the modules registry | `frontend/src/pages/CoverLetterLibrary.jsx`, `frontend/src/App.jsx`, `frontend/src/lib/modules.js` |

### Design Decisions
- **Provider/model metadata did NOT previously exist anywhere** to reuse — the communication router only logs provider/model at debug level and resume analysis stores none. Added fresh columns + `GeminiProvider.model_name` (`settings.GEMINI_MODEL or "gemini-2.0-flash"`) as the source.
- **ATS coverage reuses the JD-matcher extractor verbatim** (`jd_matcher._extract_keywords` + `_STOP_WORDS`) — deterministic set intersection on normalized keywords, never a second/ad-hoc extractor.
- **No AI-judged quality score.** Coverage is a real count of real keywords; the diff is real line-level text change; the checklist is real missing-field detection. "N of M keywords present" is the honest label, and missing JD → "No job description to check".
- `job_application_id` linking is stored data on the letter (exposed by the metadata footer) and is an existing column — no new schema for it.
- Metadata is persisted on the saving paths (`/{id}/generate`, `/{id}/apply-edit`) so it survives reloads; the non-saving `/generate` (one-off preview) returns it without persisting.

### Test Coverage
- `backend/tests/test_cover_letter_transparency.py` — 30 tests: keyword coverage (8: match/miss/case/stop-words/empty JD), preflight pure (5: missing combinations, whitespace), diff pure (4: insert/delete/replace/no-op), API (13: metadata persistence on generate/apply-edit, ats-coverage, diff 400/404, preflight endpoint, ownership scoping). Full related run `test_score_diff.py + test_linked_workspace.py + test_cover_letter_transparency.py + test_job_description.py` → 75 passed. Frontend `eslint .` clean + `vite build` succeeds (only pre-existing chunk-size warnings).

## Phase 9 — Career Coach Structured Recommendations & Task Status

### Summary
Turned Career Coach into a structured recommendations page: every `skill_gap.priority` recommendation carries a deterministic High/Medium/Low confidence bucket (pure derivation of the real `supported_signals/total_possible_signals` counts — never an AI value), a `generated_at` timestamp, an expandable "Why this recommendation?" reasons list, and a user-set Not started / In progress / Done selector that persists independently of regeneration. Added a "Refresh with latest data" action and a Career Progress Timeline built from `career_readiness` score snapshots.

### Changes
| Component | Description | Files |
|-----------|-------------|-------|
| Confidence bucket | `confidence_label(supported, total)`: ratio ≥ 0.75 → `high`, ≥ 0.4 → `medium`, else `low` (zero/total-0 → low); added `confidence` key to every enriched priority entry | `backend/app/career/services/recommendation_signals.py` |
| `generated_at` | ISO timestamp embedded in the report dict by `generate_career_report` (AI + fallback branches) so it persists into `report_json` and is returned by generate/refresh/history | `backend/app/career/services/roadmap_service.py` |
| Task model + migration | `roadmap_task_statuses`: `(user_id, skill_key)` unique, `skill` (display casing), `status` (`not_started`/`in_progress`/`done`), `created_at`/`updated_at` | `backend/app/models/roadmap_task_status.py`, `backend/app/migrations/_016_add_roadmap_task_statuses.py`, `app/database.py` |
| Task service | `ensure_task_rows` (get-or-create per normalized skill), `attach_task_statuses` (transient enrichment of report priority entries: `task_id`, `task_status`, `task_status_settable`, + `confidence` backfill for old reports), `get_task_status`/`set_task_status` (ownership-scoped) | `backend/app/career/services/roadmap_task_service.py` |
| API | `POST /api/career/roadmap/refresh` (regenerates from latest report inputs + current DB, saves new history row, records readiness snapshot, rate-limited like career-coach), `GET/PUT /api/career/roadmap/tasks/{task_id}/status` (ownership-checked, invalid status → 422) | `backend/app/career/roadmap_router.py`, `main.py` |
| Existing endpoints | `POST /api/career-coach` and `GET /career/history{/{report_id}}` now attach task statuses to priority entries on the response (transient — never persisted into `report_json`) | `backend/app/routers/career.py`, `routers/career_history.py` |
| Recommendation card UI | `InsightCard` gained a `collapsible` mode ("Why this recommendation?" toggle); `ConfidenceBadge` atom + `confidenceBucket` derivation (client-side fallback); `SkillGap` renders StatusSelector with optimistic mutation | `frontend/src/components/ui/atoms.jsx`, `components/career/SkillGap.jsx` |
| Refresh + timestamp | Career page header shows "Last updated {timeAgo}" (from `report.generated_at`) + "Refresh with latest data" button | `frontend/src/pages/Career.jsx`, `services/careerApi.js` |
| Progress timeline | `CareerProgressTimeline` renders readiness snapshots via the `Timeline` atom (`/api/analytics/history?metric_type=career_readiness`) | `frontend/src/components/career/CareerProgressTimeline.jsx`, `CareerDashboard.jsx` |

### Design Decisions
- **Confidence is never AI-generated** — always `confidence_label()` of the real integer counts; bucket thresholds: `high` ≥ 0.75, `medium` ≥ 0.4, else `low` (including 0 evaluable signals).
- **Task-status matching across refreshes** is by *normalized skill identity* (`skill_key` = lowercased/whitespace-stripped name), never list position — verified by test reordering priority and by test adding a brand-new skill (new skill → `not_started`, kept skill → its user-set status).
- **Task status lives only in `roadmap_task_statuses`**, keyed `(user_id, skill_key)`; a re-recommended skill keeps its status, a dropped skill's row is harmless and resurfaces if recommended again. Refresh never wipes statuses.
- `generated_at` is part of the stored `report_json` (real generation time); `created_at` remains the row timestamp on `career_reports`.
- No chat UI. No freeform Q&A. Every element is stored data or a deterministic derivation.
- Bonus fix: `build_fallback_report` referenced undefined `db`/`user_id` (latent NameError on every AI failure path); signature now accepts them and `generate_career_report` passes them through.

### Test Coverage
- `backend/tests/test_roadmap_tasks.py` — 28 tests in 5 classes: confidence bucket (6), task-status persistence across refresh incl. reorder/new-skill/ownership/invalid (7), `generated_at` AI+fallback (2), readiness snapshot accumulation/dedup/order (3), task-status + refresh API (10: auth, ownership 404s, 422, refresh keeps `done`, history carries statuses). All pass in isolation; full suite 985 passed — only pre-existing JD-matching failure + documented login-429 flakes in `test_score_diff.py`/`test_score_history.py`/`test_today_focus.py` API tests.

## Phase 8 — Per-Application Conversation Status

### Summary
Added a deterministic per-application conversation status (Needs Reply / Waiting / Closed) to the Communication timeline. The status is a pure function of real data — the last message's `direction` and the linked application's real pipeline status — never a standalone manual-only value. A nullable override column lets users force a state, but terminal application statuses always win.

### Precedence Rule (documented decision)
`TERMINAL APPLICATION STATUS > MANUAL OVERRIDE > DERIVED FROM LAST MESSAGE`
1. Application status in `{Accepted, Rejected, Withdrawn}` → **closed**, always (even over a manual "needs_reply"). The override column is preserved, not deleted, so re-opening the application restores the manual choice.
2. Manual override (`closed`/`needs_reply`/`waiting`) → respected (sticky across new messages) while the app is non-terminal.
3. Derived: last inbound → `needs_reply`, last outbound → `waiting`, no messages → `None`.

### Changes
| Component | Description | Files |
|-----------|-------------|-------|
| Resolution module | `resolve_status(job, last_message)` implements the precedence rule; `derive_from_direction`; `build_status_response`; `_last_message_map` (single-query batch) | `backend/app/communication/conversation_status.py` |
| Model + migration | `job_applications.conversation_status_override VARCHAR(20)` nullable (NULL = auto), migration gated + idempotent | `backend/app/models/job_application.py`, `backend/app/migrations/_014_add_conversation_status_override.py`, `app/database.py` |
| Service | `get_conversation_status`, `set_conversation_status` (null clears), `get_all_conversation_statuses`, `attach_conversation_status` (transient enrichment of message list/thread) | `backend/app/communication/service.py` |
| API | `GET/PUT /api/communication/conversation-status/{id}` (ownership-checked), `GET /api/communication/conversation-statuses`; `CommunicationMessageResponse` gains `conversation_status`/`conversation_status_source` | `backend/app/communication/router.py`, `schemas.py` |
| Workspace UI | StatusBadge in the Communication thread header + workspace sticky header; "Mark closed"/"Reopen" toggle (hidden when closed-by-application-status) | `frontend/src/communication/components/ApplicationCommunicationThread.jsx`, `modules/jobTracker/components/ApplicationLinkedResources.jsx`, `hooks/useConversationStatus.js` |
| Hub cross-app view | StatusBadge on each message card + conversation-status filter + "Needs attention first" sort (needs_reply → waiting → closed) | `frontend/src/communication/pages/CommunicationHub.jsx`, `services/communicationApi.js` |

### Design Decisions
- Terminal set is `{Accepted, Rejected, Withdrawn}` (no "Offer declined" value exists in `JobStatus`; a declined offer maps to Withdrawn/Rejected). **Offer is intentionally NOT terminal** — negotiation may still be ongoing.
- Rejected overrides a manually-set "needs_reply" (the decided precedence). Manual override is masked, not deleted, on terminal status.
- No messages → no status (not "waiting"); the badge and actions only appear once a conversation exists.

### Test Coverage
- `backend/tests/test_conversation_status.py` — 31 tests: derivation (5), precedence rule (8), service flips/persistence (8), API (10). Pass in isolation; full suite 952 passed (only pre-existing JD-matching failure + documented login 429 flakes in `test_score_history.py`).

## Phase 7 — Dashboard "Today's Focus" Card

### Summary
Added a single-recommendation "Today's Focus" card to the Dashboard that surfaces the top signal-backed Career Coach recommendation. It is **not** a new recommendation algorithm — it reuses Phase 2's real signal counts stored in the latest Career Report and simply picks the best one.

### Changes
| Component | Description | Files |
|-----------|-------------|-------|
| Focus service | `categorize_recommendation()` maps Phase-2 reason templates to an honest coarse category ("New skill" ← "saved job matches", "Resume wording" ← "resume analysis", "Practice" ← "weakest interview"); `get_today_focus()` picks highest `supported_signals/total_possible_signals` ratio, tie-broken by ease of categorization (single dominant signal) → more signals → alphabetical; returns `None` when no report, no enriched entries, or top pick has 0 supported signals | `backend/app/dashboard/focus_service.py` |
| Summary wiring | `today_focus` section added to `DashboardService.get_summary()` (try/except, never breaks the page) | `backend/app/dashboard/service.py` |
| Frontend card | `DashboardTodayFocus` renders the pick via `InsightCard` + `SignalStrengthBadge` with a category badge and "Open in Career Coach" CTA; `DashboardTodayFocusEmpty` renders "You're all caught up" empty state. Named distinctly to avoid collision with the existing `DashboardFocusCard` (Continue where you left off) | `frontend/src/features/dashboard/components/DashboardTodayFocus.jsx`, `frontend/src/pages/Dashboard.jsx`, `hooks/useDashboardData.js` |

### Design Decisions
- **No time/effort estimate anywhere** — no effort-estimation capability exists; the category is a real classification from which signal dominates, never a fabricated duration.
- Selection is deterministic and data-driven: reuses Phase 2's `supported_signals`/`total_possible_signals` + `reasons` verbatim from `CareerReport.report_json.skill_gap.priority`; no new algorithm, no AI call.
- Zero-signal candidates and missing/malformed entries are dropped; brand-new users get the empty state (no Career Report → `None`).
- `InsightCard` "Because" reasons list renders the real reasons strings — same visual language as Career Coach's `SkillGap.jsx`.

### Test Coverage
- `backend/tests/test_today_focus.py` — 23 tests in 4 classes: category classification (7), selection logic (10), dashboard/API integration (6). All pass in isolation.
- Note: the 2 API integration tests share the global login rate limit (10/min per TestClient) and can flake when the full suite runs back-to-back — same documented pattern as `test_dashboard.py`/`test_score_history.py`/`test_analytics.py`.

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
- **758/760 tests pass** (2 pre-existing JD matching failures excluded)
- Frontend builds successfully (vite build)

## Phase 3 — Interview Module UI Polish

### Summary
Redesigned all 6 interview pages (Dashboard, SetupWizard, Practice, Results, History, Progress) with premium shadcn/ui + Tailwind UI, while keeping all backend APIs, session engine, and question loader untouched.

### Changes
- **All 6 pages**: Hero sections with gradient headers, MiniStatCard grids with count-up animation, Card hover-lift + `active:scale-[0.97]`, skeleton loading placeholders, entry animation (fade-in + slide-up, ≤250ms), consistent spacing/typography/color, responsive mobile layouts.
- **Dashboard.jsx**: Active session banner, QuickActionCard grid, empty state illustration.
- **SetupWizard.jsx**: Job Role cards, Question Source toggle, AI mode inputs, Question Bank categories + difficulty, sticky sidebar + mobile bottom bar.
- **Practice.jsx**: Top bar with progress + badges, expandable textarea with char count + auto-save indicator, AI Feedback panel with ScoreRing + slide-in.
- **Results.jsx**: ScoreRing with count-up + performance label, collapsible QuestionCard.
- **History.jsx**: Search + segmented filter + sort dropdown, smart pagination.
- **Progress.jsx**: Metric cards with trend/color, Role Performance with gradient bars, Weak Areas for scores <50, AI Recommendation card.

### Fixes
- **InterviewProvider wrapping** (`App.jsx`): All 6 interview sub-routes wrapped in `<InterviewProvider>` — fixed "must be used within an InterviewProvider" error.
- **500 serialization** (`response.py`): `success_response()` now uses `jsonable_encoder()` for Pydantic v2 model instances before `JSONResponse`.

## Phase 4 — Cross-Module Activity Logging

### Summary
Added a dedicated `app/activity/` module to log user actions across the app for an upcoming Dashboard "Recent Activity" and "Continue Where You Left Off" feature.

### Components
| Component | Description | Key Files |
|-----------|-------------|-----------|
| **Model** | `ActivityEvent` ORM — user_id, event_type, title, description, related_entity_type/id, created_at | `app/activity/models.py` |
| **Constants** | `EventType` enum — 24 values covering resume, job, cover letter, communication, interview, analysis, career | `app/activity/constants.py` |
| **Service** | `ActivityService.log_event()` (wrapped in try/except, never breaks caller) + `get_recent()` (scoped by user, ordered by created_at desc + id desc) | `app/activity/service.py` |
| **Router** | `GET /api/activity/recent` — auth required, paginated (limit param) | `app/activity/router.py` |
| **Migration** | `_007_add_activity_events.py` — registered in `database.py` | `app/migrations/_007_add_activity_events.py` |

### Integration Points
Event logging added to 9 service/router files (all wrapped in try/except):
- `resume_service.py`: `RESUME_CREATED`, `RESUME_UPDATED`, `RESUME_DELETED`
- `job_tracker_service.py`: `JOB_APPLICATION_CREATED`, `JOB_APPLICATION_STATUS_CHANGED`, `JOB_APPLICATION_UPDATED`
- `cover_letter_service.py`: `COVER_LETTER_CREATED`
- `cover_letter.py` (router): `COVER_LETTER_GENERATED`
- `communication/service.py`: `COMMUNICATION_MESSAGE_GENERATED`
- `interview_prep/service.py`: `INTERVIEW_SESSION_COMPLETED`
- `career.py` (router): `CAREER_REPORT_GENERATED`
- `analysis.py` (router): `ANALYSIS_COMPLETED`
- `jd_matching.py` (router): `JD_MATCH_ANALYZED`

### Test Coverage
- `tests/test_activity.py` — 8 tests across 3 test classes:
  - `TestActivityService` (4 unit tests): create, ordering (id tiebreaker), user scoping, resilience on failure
  - `TestActivityApi` (3 integration tests): empty, returns events, scoped per user
  - `TestResilience` (1 test): original op succeeds even if logging raises

## Phase 5 — Analytics Score Snapshotting

### Summary
Added `app/analytics/` module that records historical score snapshots (career_readiness, interview_average, ats_score) so trend graphs on the dashboard have real data. Snapshot calls are fire-and-forget: wrapped in try/except, never break the caller.

### Changes
| Component | Description | Files |
|-----------|-------------|-------|
| ScoreSnapshot Model | `ScoreSnapshot` ORM with user_id (FK, indexed), metric_type (String(64) indexed), value (Float), recorded_at (default now) | `backend/app/analytics/models.py` |
| AnalyticsService | `record_snapshot()` with dedup (same value + <24h skips, new value or >=24h creates row), `get_history()` ordered by recorded_at asc | `backend/app/analytics/service.py` |
| Analytics API | `GET /api/analytics/history?metric_type=...&limit=100` (auth required, scoped to user, max limit 500) | `backend/app/analytics/router.py` |
| Migration | `_008_add_score_snapshots.py` — `CREATE TABLE IF NOT EXISTS score_snapshots` + indexes, registered in `database.py` | `backend/app/migrations/_008_add_score_snapshots.py`, `app/database.py` |
| Snapshot Call Sites | career_readiness → `career.py:69-72`; interview_average → `interview_prep/service.py:186-188`; ats_score → `analysis.py:168-170,301-303,373-375` | 3 files, 5 locations |

### Test Coverage
- `tests/test_analytics.py` — 12 tests (create, dedup same-value/<24h, different value, same-value >=24h, user/type scoping, ordering, resilience, API empty/scoped/auth)

## Phase 6 — Cross-Module Dashboard

### Summary
Built the real home page Dashboard at `/` with fan-out queries across all 7 modules (Resume, Job Tracker, Interview, Career, Activity, Analytics, Communication). Each section wrapped in try/except so no single module failure breaks the whole page.

### Changes
| Component | Description | Files |
|-----------|-------------|-------|
| DashboardService | `get_summary(db, user_id)` returns resume stats, job stats, interview summary, career readiness, recent activity, continue-items, career-journey stages, AI insights, empty-state detection | `backend/app/dashboard/service.py` |
| Dashboard API | `GET /api/dashboard/summary` (auth required, scoped to user) | `backend/app/dashboard/router.py` |
| Dashboard Frontend | New `Dashboard.jsx` component at `/` with welcome header, stat cards, Continue Where You Left Off, Career Journey stepper, Recent Activity list, AI Insights cards, empty-dashboard onboarding CTA | `frontend/src/pages/Dashboard.jsx` |
| Dashboard Api Service | `getSummary()` calling `/api/dashboard/summary` | `frontend/src/services/dashboardApi.js` |
| Route Wiring | `App.jsx` already had `path="/"` → Dashboard (no change needed) | `frontend/src/App.jsx` |

### Frontend Sections
- **StatCards**: resume count, job apps, interview score, career readiness (skeleton loading, error state with retry)
- **ContinueWhereYouLeftOff**: per-module clickable cards (resume, cover letter, message, interview, job)
- **CareerJourney**: 6-stage badge list (resume → analysis → career coach → job apps → interview → communication), each "complete" or "not_started"
- **RecentActivity**: time-ago display, per-type icons, empty message
- **AiInsights**: follow-up suggestions, practice-reminder (≥7 days stale), readiness score, ATS trend (only when ≥2 snapshots)
- **EmptyDashboard**: hero section with illustration + CTA button → `/resume-studio`

### Design Decisions
- Every section wrapped in try/except — any module failure is logged as warning, section returns empty/default, page never breaks
- Resume section handles serialization error to dict (returns null on failure) — avoids crashing the entire summary
- ai_insights fallback to empty list on any error
- is_empty = resume_count === 0 && activity is empty → triggers full onboarding CTA
- Continue-items labeled with the actual entity name (e.g., "Resume A" not just "Resume")

### Test Coverage
- `tests/test_dashboard.py` — 11 tests (full user, brand-new/empty, partial/no-interview, resume failure graceful, career journey states, ATS insight threshold, follow-up suggestion insight, API auth/scoping)

## Test Status
- **758/760 tests pass** (2 pre-existing JD matching failures excluded)
- Frontend builds successfully (vite build, zero errors)

## Deployment Notes
- Set `SECRET_KEY` in `.env` (use `python -c "import secrets; print(secrets.token_urlsafe(64))"`)
- Configure `CORS_ORIGINS` for production domain
- Run with `uvicorn --no-server-header app.main:app` to suppress `Server` header
- Consider HTTPS termination at reverse proxy (nginx/Caddy)
