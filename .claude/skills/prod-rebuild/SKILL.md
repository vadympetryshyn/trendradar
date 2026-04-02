---
name: prod-rebuild
description: >
  Deploy changes to the TrendRadar production server. Use this skill whenever the user wants to
  deploy to production, update prod, rebuild prod containers, restart production, push changes
  to the live server, or fix production errors. Also trigger when the user says things like
  "deploy", "push to prod", "update production", "prod rebuild", "restart prod", "production is broken",
  or "/prod-rebuild". This skill handles SSH connection, git pull, smart container rebuild/restart,
  and safe Docker cleanup — all with zero downtime.
---

# Production Rebuild & Deploy

This skill deploys code changes to the TrendRadar production server with zero downtime.
It connects via SSH, pulls latest code, analyzes what changed, and applies the fastest
correct Docker strategy (restart vs recreate vs rebuild).

## Credentials

Read `/Users/vadympetryshyn/work/trendradar/PROD_CREDENTIALS.md` for SSH credentials and server details.

**SSH connection method:** Write the SSH password to a temp file using the Write tool (NOT echo/printf — special characters get mangled), then use `sshpass -f /tmp/trendradar_ssh_pass ssh -o StrictHostKeyChecking=no ubuntu@<host>`.

**Important:** Every SSH command that uses `docker compose` must include `cd /var/www/trendradar &&` at the start, because compose needs to find the compose file relative to the project directory. Standalone docker commands (like `docker image prune`) don't need this.

## Production Server Details

- **Project path:** `/var/www/trendradar`
- **Compose file:** `docker-compose.prod.yml`
- **Services:** postgres, redis, back (FastAPI), front (Next.js), celery_worker, celery_beat
- **All commands on server require `sudo`**

## Deployment Flow

Execute these phases in order. If any phase fails, stop and diagnose.

### Phase 1: Connect & Pull

1. Write the SSH password to `/tmp/trendradar_ssh_pass` using the Write tool
2. SSH into the server
3. `cd /var/www/trendradar && sudo git pull`
4. Capture the git pull output — you need it to determine what changed

### Phase 2: Analyze Changes

Parse the `git pull` output to determine which files changed. Categorize:

| What changed | Action needed |
|---|---|
| `front/` source code, `front/Dockerfile.prod`, `front/package.json`, `front/package-lock.json` | **Rebuild** `front` service |
| `back/` source code, `back/Dockerfile.prod`, `back/requirements.txt` | **Rebuild** `back`, `celery_worker`, `celery_beat` services (they share the same image) |
| `docker-compose.prod.yml` | **Recreate** affected services |
| `.env.production` files only | **Restart** affected services (env_file is read on container start) |
| `postgres` or `redis` config only | **Restart** those services |

In production, all code is baked into Docker images (no volume mounts), so ANY source code
change in `front/` or `back/` requires a rebuild of that service.

**If git pull says "Already up to date":** Tell the user there are no new changes to deploy.
Only proceed with a rebuild if the user explicitly asks for it.

### Phase 3: Safe Docker Cleanup

Before building, free disk space. This is important because the server has limited storage.

```bash
# Remove dangling images, stopped containers, unused networks
# -f skips confirmation prompt
# Do NOT use -a flag here — it removes ALL unused images including base images
# that are needed for layer caching during builds
sudo docker image prune -f
sudo docker container prune -f
```

**Why not `docker system prune -af`?** The `-a` flag removes all unused images, including
cached base layers (python:3.12-slim, node:20-alpine). Removing those forces a full re-download
on next build, which is slow and wasteful. We only prune dangling (untagged) images to reclaim
space from previous builds while keeping useful cache layers.

### Phase 4: Build & Deploy (Zero Downtime)

The key to zero downtime: build new images first, THEN swap containers.

**If rebuild is needed:**
```bash
cd /var/www/trendradar

# Build new images (old containers keep running during build)
# Use 2>&1 to capture build output — docker compose sends progress to stderr over SSH
sudo docker compose -f docker-compose.prod.yml build <service1> <service2> 2>&1

# After build, verify new images exist before swapping:
sudo docker images --format '{{.Repository}}:{{.Tag}} {{.CreatedSince}}' | grep trendradar

# Swap to new containers (docker compose recreates only what changed)
sudo docker compose -f docker-compose.prod.yml up -d <service1> <service2>
```

**Note:** `celery_worker` and `celery_beat` share the same build context as `back`. If `back/`
changed, rebuild all three: `back celery_worker celery_beat`.

**If only restart is needed:**
```bash
cd /var/www/trendradar
sudo docker compose -f docker-compose.prod.yml restart <service>
```

**If recreate is needed (compose file changed):**
```bash
cd /var/www/trendradar
sudo docker compose -f docker-compose.prod.yml up -d
```

### Phase 5: Post-Deploy Cleanup & Verify

```bash
cd /var/www/trendradar

# Remove old images that are now dangling (from the previous build)
sudo docker image prune -f

# Verify all containers are running
sudo docker compose -f docker-compose.prod.yml ps

# Check logs for errors (last 20 lines of each rebuilt service)
sudo docker compose -f docker-compose.prod.yml logs --tail=20 <service>
```

If containers are crash-looping or logs show errors, report to the user immediately.

## Handling Production Errors

If you discover errors on production (from logs or user report):

1. **Do NOT fix code on the production server**
2. Diagnose the error from prod logs
3. Fix the code **locally** in the working directory (`/Users/vadympetryshyn/work/trendradar/`)
4. Commit and push the fix locally
5. Then SSH to prod and run the deployment flow above (git pull → build → deploy)

## Important Rules

- **Never use `--no-cache`** during builds. It forces a complete rebuild from scratch and is
  extremely slow. Only use it if explicitly requested by the user for a critical situation
  where cached layers are suspected to be corrupted.
- **Never run commands on prod without `sudo`** — we connect as `ubuntu`, not root.
- **Never edit code on the production server** — all fixes go through git.
- **Always build before swapping** — this ensures zero downtime. Old containers serve traffic
  while new images are being built.
- **Always check logs after deploy** — catch errors early before the user discovers them.
- Clean up the temp password file when done: `rm -f /tmp/trendradar_ssh_pass`

## Alembic Migrations

If `back/alembic/versions/` has new migration files, run migrations after the backend container is up:

```bash
cd /var/www/trendradar && sudo docker compose -f docker-compose.prod.yml exec back alembic upgrade head
```

## Deploying Niche Changes (`niches.json`)

When `back/app/niches.json` is modified (niches added, removed, renamed, or subreddits changed):

1. **Deploy normally** — rebuild `back`, `celery_worker`, `celery_beat` (niches.json is baked into the image)
2. **Niche sync happens automatically on startup** — `seed_data()` in `app/seed.py` runs on every backend boot and:
   - Creates new niches from the config (with `is_active=True` and 3 disabled ScheduleConfigs)
   - Updates existing niches if subreddits/description changed (matched by `slug`)
   - Deactivates niches whose slug is no longer in the config AND disables all their ScheduleConfigs
3. **After deploy, verify the niche state** by running:
   ```bash
   cd /var/www/trendradar && sudo docker compose -f docker-compose.prod.yml exec -T back python -c "
   from app.database import SessionLocal
   from app.models import Niche, ScheduleConfig
   db = SessionLocal()
   for n in db.query(Niche).order_by(Niche.id).all():
       enabled = db.query(ScheduleConfig).filter(ScheduleConfig.niche_id == n.id, ScheduleConfig.is_enabled == True).count()
       print(f'id={n.id} slug={n.slug} active={n.is_active} enabled_schedules={enabled}/3')
   db.close()
   "
   ```
4. **Enable schedules for new niches** — new niches are created with all schedules disabled. Enable them via admin API or directly:
   ```bash
   cd /var/www/trendradar && sudo docker compose -f docker-compose.prod.yml exec -T back python -c "
   from app.database import SessionLocal
   from app.models import ScheduleConfig, Niche
   db = SessionLocal()
   # Enable all schedules for active niches
   db.query(ScheduleConfig).join(Niche).filter(Niche.is_active == True).update({ScheduleConfig.is_enabled: True})
   db.commit()
   db.close()
   print('All active niche schedules enabled')
   "
   ```

**Important:** The scheduler (`run_scheduled_collections`) has a safety net — it joins on `Niche.is_active` so even if a stale schedule somehow remains enabled, it will never dispatch for an inactive niche.
