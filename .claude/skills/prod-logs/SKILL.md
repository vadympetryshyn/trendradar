---
name: prod-logs
description: >
  Check production server logs to diagnose bugs, errors, or problems. Use this skill whenever
  the user wants to investigate what's happening on production, check container logs, debug a
  production issue, find errors in prod, trace a bug on the live server, or understand why
  something is broken in production. Trigger when the user says things like "check prod logs",
  "what's happening on prod", "look at production logs", "prod is broken check logs",
  "find the error on prod", "why is prod failing", or "/prod-logs". Also trigger when the user
  describes a specific problem and wants to investigate it on the production server.
---

# Production Log Inspector

This skill connects to the TrendRadar production server and checks Docker container logs to
diagnose issues, find errors, or verify that everything is running correctly.

## Credentials

Read `/Users/vadympetryshyn/work/trendradar/PROD_CREDENTIALS.md` for SSH credentials and server details.

**SSH connection method:** Write the SSH password to a temp file using the Write tool (NOT echo/printf — special characters get mangled), then use:
```
sshpass -f /tmp/trendradar_ssh_pass ssh -o StrictHostKeyChecking=no ubuntu@<host>
```

**Important:** Every SSH command that uses `docker compose` must include `cd /var/www/trendradar &&` at the start.

## Production Server Details

- **Project path:** `/var/www/trendradar`
- **Compose file:** `docker-compose.prod.yml`
- **Services:** `postgres`, `redis`, `back` (FastAPI), `front` (Next.js), `celery_worker`, `celery_beat`
- **All commands require `sudo`**

## Behavior Depending on How the Skill Is Called

### Called without a problem description (general health check)

#### Step 1: Container status (always first)

Check container statuses and uptime in parallel:
```bash
cd /var/www/trendradar && sudo docker compose -f docker-compose.prod.yml ps
sudo docker ps --format "table {{.Names}}\t{{.Status}}\t{{.RunningFor}}"
```

#### Step 2: Fetch logs from key services

Fetch logs from the **four important services** in parallel — `back`, `front`, `celery_worker`, and `celery_beat`. Skip `postgres` and `redis` by default (only check them if the user specifically asks or if other logs point to database/cache issues).

For efficiency, use grep on the server to filter for errors instead of pulling all 1000 lines:
```bash
cd /var/www/trendradar && sudo docker compose -f docker-compose.prod.yml logs --tail=1000 --no-color back 2>&1 | grep -iE 'error|ERROR|warning|WARNING|traceback|exception|CRITICAL|500|502|fatal'
```

Also pull the full (unfiltered) last 1000 lines of `back` since it's the most likely source of issues and you may need context around errors.

For `front`, `celery_worker`, and `celery_beat`, pulling the full last 200 lines is usually sufficient.

#### Step 3: Report

After collecting logs, report:
- Container statuses (running, exited, crash-looping)
- Any ERROR, CRITICAL, WARNING, Traceback, or exception entries with context
- Unusual restart counts
- A brief "all looks good" if nothing suspicious is found

### Called with a specific problem description

When the user describes a bug, error, or unexpected behavior, use that context to be smarter about log analysis:

1. **Determine which containers are most likely involved.** Frontend issues → `front`. API errors, 500s, data problems → `back`. Task/scheduling issues → `celery_worker` or `celery_beat`. Database issues → `postgres`. Cache issues → `redis`. Focus there first, but also check others if the root cause isn't clear.

2. **Choose an appropriate log window.** For recent issues use `--tail=500`. For longer-running problems or "it's been broken since yesterday" use `--tail=2000` or add `--since=24h`.

3. **Search for relevant keywords** in the logs. For example, if the user says "trends aren't updating", look for Celery task errors, OpenAI API errors, database connection errors, or Python exceptions in the `back` and `celery_worker` logs.

4. **Cross-reference.** If you find an error in `back`, check `celery_worker` logs around the same time for related task failures. If you find frontend errors, check `back` for the API side of the story.

5. **Report findings clearly:**
   - Quote the relevant log lines (include timestamps)
   - State which container the error came from
   - Identify the likely root cause if possible
   - Suggest a fix direction (e.g., "this looks like a missing env var", "this is a 502 from nginx upstream", "alembic migration likely didn't run", "Celery task is failing due to...")

## Useful Log Commands

```bash
# Last N lines from a specific service
cd /var/www/trendradar && sudo docker compose -f docker-compose.prod.yml logs --tail=1000 --no-color back

# Last N lines from all services at once
cd /var/www/trendradar && sudo docker compose -f docker-compose.prod.yml logs --tail=200 --no-color

# Logs since a time window
cd /var/www/trendradar && sudo docker compose -f docker-compose.prod.yml logs --since=2h --no-color back

# Container status overview
cd /var/www/trendradar && sudo docker compose -f docker-compose.prod.yml ps

# Check restart counts and uptime
sudo docker ps --format "table {{.Names}}\t{{.Status}}\t{{.RunningFor}}"
```

## What to Look For

| Signal | Likely meaning |
|---|---|
| `Traceback (most recent call last)` | Python exception in backend or Celery worker |
| `Error` / `ERROR` | Generic error — read context |
| `500 Internal Server Error` | Backend crash on a request |
| `502 Bad Gateway` | Frontend can't reach backend |
| `connection refused` | Service not running or wrong port |
| `FATAL` in postgres logs | Database startup failure |
| `Restarting` in `docker ps` | Container crash-looping |
| `alembic.exc.` | Migration not applied |
| `ModuleNotFoundError` | Missing dependency (needs rebuild) |
| `Task .* raised` | Celery task failure |
| `ConnectionError` to Redis | Redis down or connection issue |
| `openai.error` / `APIError` | OpenAI API issue |

## Important Rules

- **Never make changes on prod** based on what you find — diagnose only. If a fix is needed, tell the user what to change locally and offer to run `/prod-rebuild` after.
- **Clean up** the temp password file when done: `rm -f /tmp/trendradar_ssh_pass`
- **Be concise in your report** — don't dump thousands of log lines at the user. Extract and highlight what matters.
- If logs are clean and you find no issues, say so clearly so the user knows the server is healthy.
