.PHONY: help sync setup run verify prune-seen notify-test notify-debug notify-chat-ids lock format check clean

help:
	@echo "Targets:"
	@echo "  make setup   - Sync dependencies and create .env if missing"
	@echo "  make sync    - Sync dependencies from uv.lock"
	@echo "  make run     - Run the monitor once"
	@echo "  make verify  - Run monitor and validate DB/table checks"
	@echo "  make prune-seen - Remove seen jobs that now match exclusion filters"
	@echo "  make prune-seen DRY_RUN=1 - Preview removals without deleting rows"
	@echo "  make notify-test - Send a Telegram test message"
	@echo "  make notify-debug - Diagnose Telegram token/chat configuration"
	@echo "  make notify-chat-ids - List candidate Telegram chat IDs"
	@echo "  make lock    - Refresh uv.lock from pyproject.toml"
	@echo "  make clean   - Remove local runtime artifacts"

sync:
	uv sync

setup: sync
	@if [ ! -f .env ]; then cp .env.example .env; fi
	@echo "Setup complete. Edit .env with TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID."

run:
	uv run -m app.main

verify:
	@echo "[verify] running monitor once"
	@uv run -m app.main >/tmp/dom_verify.log 2>&1 || { \
		echo "[verify] FAIL: monitor execution failed"; \
		tail -n 20 /tmp/dom_verify.log; \
		exit 1; \
	}
	@echo "[verify] checking database file"
	@test -f data/jobs.db || { echo "[verify] FAIL: data/jobs.db not found"; exit 1; }
	@echo "[verify] checking seen_jobs table"
	@uv run python -c "import sqlite3; c=sqlite3.connect('data/jobs.db'); n=c.execute('select count(*) from seen_jobs').fetchone()[0]; print(f'[verify] PASS: seen_jobs exists, rows={n}')"
	@echo "[verify] checking collected_jobs table"
	@uv run python -c "import sqlite3; c=sqlite3.connect('data/jobs.db'); n=c.execute('select count(*) from collected_jobs').fetchone()[0]; print(f'[verify] PASS: collected_jobs exists, rows={n}')"
	@echo "[verify] PASS: make run validation complete"

prune-seen:
	@case "$(DRY_RUN)" in 1|true|yes|on) echo "[prune-seen] previewing filtered jobs" ;; *) echo "[prune-seen] removing seen jobs that are now excluded" ;; esac
	@uv run python -c "import os; from app.main import prune_seen_jobs; dry_run = os.getenv('DRY_RUN', '').lower() in ('1', 'true', 'yes', 'on'); raise SystemExit(0 if prune_seen_jobs(dry_run=dry_run) >= 0 else 1)"

notify-test:
	@echo "[notify-test] sending Telegram test notification"
	@uv run python -c "import os; from dotenv import load_dotenv; from app.notify import send_telegram_test_message; load_dotenv(); ok,msg = send_telegram_test_message(os.getenv('TELEGRAM_BOT_TOKEN',''), os.getenv('TELEGRAM_CHAT_ID','')); print('[notify-test] ' + ('PASS: ' if ok else 'FAIL: ') + msg); raise SystemExit(0 if ok else 1)"

notify-debug:
	@echo "[notify-debug] running Telegram diagnostics"
	@uv run python -c "import os; from dotenv import load_dotenv; from app.notify import diagnose_telegram; load_dotenv(); ok,notes = diagnose_telegram(os.getenv('TELEGRAM_BOT_TOKEN',''), os.getenv('TELEGRAM_CHAT_ID','')); [print(f'[notify-debug] NOTE: {line}') for line in notes]; print('[notify-debug] ' + ('PASS' if ok else 'FAIL') + ': diagnostics complete'); raise SystemExit(0 if ok else 1)"

notify-chat-ids:
	@echo "[notify-chat-ids] fetching candidate chat IDs from Telegram updates"
	@uv run python -c "import os; from dotenv import load_dotenv; from app.notify import list_candidate_chat_ids; load_dotenv(); ok,lines = list_candidate_chat_ids(os.getenv('TELEGRAM_BOT_TOKEN','')); [print(f'[notify-chat-ids] {line}') for line in lines]; raise SystemExit(0 if ok else 1)"

lock:
	uv lock

clean:
	rm -rf .venv
	rm -f data/jobs.db
