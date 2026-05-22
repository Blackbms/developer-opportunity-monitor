# Implementation Status

## Runtime Deployment

A Hermes system runs the `main` branch hourly via cron.

Implications:
- `main` is treated as the production branch.
- Changes to fetchers, scoring, notification, or database schema must be tested before merge.
- Avoid committing experimental scoring thresholds directly to `main`.
- Any migration must preserve the existing `data/jobs.db` or include a clear migration path.

## Current Branch
architecture

## Implemented
- README requirements started
- uv setup documented
- Telegram env/config expectations documented
- Telegram test/debug/chat-id make targets planned

## Not Yet Confirmed in Code
- app.main entry point
- SQLite schema
- fetcher implementations
- Telegram notifier implementation
- scoring engine
- dedupe logic
- analysis agent integration

## Current Architecture
- Scheduler runs job fetcher
- Fetchers collect company jobs
- Jobs are normalized
- SQLite stores collected jobs
- Agent analyzes unanalyzed jobs
- Telegram alerts are sent when score threshold is met

## Next Implementation Targets
1. Create database schema
2. Create normalized Job model
3. Implement one fetcher end-to-end, probably GitLab/Greenhouse
4. Implement dedupe by canonical URL + content hash
5. Implement Telegram notifier
6. Add dry-run mode
