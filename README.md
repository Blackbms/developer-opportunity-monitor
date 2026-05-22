# Developer Opportunity Monitor

A lightweight local automation platform for monitoring engineering job opportunities and delivering filtered notifications through Telegram.

The system is designed specifically for experienced engineers seeking high-signal technical roles while avoiding noisy aggregators, stale postings, and low-quality matches.

---

# Goals

## Primary Goals

- Monitor official company career portals
- Detect new relevant job postings
- Score roles against a configurable engineering profile
- Deliver actionable alerts through Telegram
- Avoid duplicate notifications
- Run fully local-first

---

# Non-Goals

- Mass job scraping from aggregators
- Automated job applications
- Resume auto-submission
- Browser automation for ATS systems
- AI-generated spam applications

---

# Initial Target Companies

## Tier 1

- GitHub
- GitLab
- Atlassian
- HashiCorp
- JFrog
- CloudBees

## Tier 2

- Viasat
- Microsoft
- Red Hat
- Docker
- JetBrains
- Canonical

---

# Target Role Categories

## High Priority

- Developer Experience Engineer
- Platform Engineer
- DevSecOps Engineer
- Solutions Engineer
- Customer Engineer
- Enterprise Enablement Engineer
- CI/CD Engineer
- Technical Account Manager
- Field Engineer
- Productivity Engineer

## Medium Priority

- Site Reliability Engineer
- Infrastructure Engineer
- Internal Tools Engineer

## Excluded Roles

- Marketing
- Recruiting
- Sales Executive
- Finance
- HR
- Design
- Frontend-only roles
- Pure Data Science
- AI Research

---

# Functional Requirements

## Job Discovery

### FR-001
The system shall fetch job listings from official company careers pages.

### FR-002
The system shall support:
- HTML scraping
- RSS feeds
- JSON APIs
- Greenhouse/Lever endpoints

### FR-003
The system shall avoid known low-quality job aggregators.

### FR-004
The system shall support configurable company sources.

---

## Job Filtering

### FR-005
The system shall filter postings by:
- Geography
- Remote eligibility
- Keywords
- Seniority
- Employment type

### FR-006
The system shall support exclusion keyword filtering.

### FR-007
The system shall support weighted keyword scoring.

Example:

```yaml
weights:
  developer experience: 10
  platform engineer: 8
  ci/cd: 8
  devsecops: 7
  customer engineer: 9
```

---

# Local Setup (uv)

## Prerequisites

- Python 3.11+
- `uv` installed: https://docs.astral.sh/uv/getting-started/installation/

## Setup

```bash
uv sync
cp .env.example .env
```

Edit `.env` and set:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

## Run Once

```bash
uv run -m app.main
```

The first run creates `data/jobs.db` automatically for deduplication.

## Test Telegram

```bash
make notify-test
```

If this fails, confirm `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are set in `.env`.

## Debug Telegram

```bash
make notify-debug
```

This checks token validity (`getMe`) and chat access (`getChat`) and prints next-step guidance.
It also includes Telegram API error descriptions (for example, permission or membership errors).

## Discover Chat IDs

```bash
make notify-chat-ids
```

If no chat IDs are returned, send `/start` to your bot (or post in your target
group/channel) and run it again.
