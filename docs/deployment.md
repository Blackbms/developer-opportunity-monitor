# Deployment

## Current Runtime

The monitor is run hourly by cron on a Hermes system from the `main` branch.

## Production Branch

`main`

## Safe Release Checklist

- [ ] Branch merged only after local `make verify`
- [ ] Telegram config validated with `make notify-test`
- [ ] No test-only `min_score: 0` settings unless intentional
- [ ] Database schema changes are backward compatible
- [ ] First production run monitored manually

## Rollback

Revert to the prior known-good commit on `main`, then rerun the cron command manually.
