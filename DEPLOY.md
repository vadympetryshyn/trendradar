# TrendRadar — Production Deployment Instructions

> **For Claude / LLM**: Read this entire file, then execute each phase in order via SSH.
> When you see **[USER ACTION]** — stop, show the user what they need to do, and wait for confirmation before continuing.

---

## Server Access

```
SSH_USER=ubuntu
SSH_PASSWORD=aSd068222!.$5.
SSH_HOST=51.210.14.13
```

**Connect with:** `ssh ubuntu@51.210.14.13`

> **Note:** The SSH password may contain special characters (`!`, `$`). When using `sshpass`, write the password to a file with a file-write tool (not `printf`/`echo` which may escape characters), then use `sshpass -f /path/to/passfile`. All commands on the server require `sudo` since we connect as `ubuntu`, not `root`.

---

## Project Config

| Key | Value |
|-----|-------|
| Domain (frontend) | `trendradar.cc` |
| Domain (API) | `api.trendradar.cc` |
| Server IP | `51.210.14.13` |
| Project path | `/var/www/trendradar` |
| Git repo | `git@github.com:vadympetryshyn/trendradar.git` |
| SSL email | `vadympetryshyn@gmail.com` |
| Frontend port | `3005` |
| Backend port | `3006` |

### Services Overview

| Service | Description |
|---------|-------------|
| `front` | Next.js 16 frontend |
| `back` | FastAPI backend (Python 3.12, Uvicorn, 4 workers) |
| `celery_worker` | Celery task worker (concurrency=2) |
| `celery_beat` | Celery beat scheduler (trend collection every 5 min, cleanup daily) |
| `postgres` | PostgreSQL 16 with pgvector extension |
| `redis` | Redis 7 (password-protected in prod) |

---

## Phase 1: System Update & Essential Packages

SSH into the server and run:

```bash
apt-get update && apt-get upgrade -y
```

> **Warning:** If a kernel update is installed, the server may automatically reboot. SSH will be unreachable for 1-3 minutes. Wait and reconnect before continuing.

```bash
apt-get install -y curl wget git ufw fail2ban htop unzip software-properties-common ca-certificates gnupg lsb-release
```

---

## Phase 2: Firewall & Security

```bash
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
```

```bash
systemctl enable fail2ban
systemctl start fail2ban
```

Verify firewall:
```bash
ufw status
```

Expected: SSH(22), HTTP(80), HTTPS(443) allowed.

---

## Phase 3: Install Docker & Docker Compose

```bash
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
```

```bash
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
```

```bash
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

```bash
systemctl enable docker
systemctl start docker
```

Verify:
```bash
docker --version
docker compose version
```

---

## Phase 4: Install Nginx

```bash
apt-get install -y nginx
systemctl enable nginx
systemctl start nginx
```

---

## Phase 5: Generate SSH Deploy Key for GitHub

```bash
ssh-keygen -t ed25519 -C "trendradar-server-deploy" -f /root/.ssh/trendradar_deploy -N ""
```

Configure SSH to use this key for GitHub:

```bash
cat >> /root/.ssh/config <<'EOF'

Host github.com
    HostName github.com
    User git
    IdentityFile /root/.ssh/trendradar_deploy
    StrictHostKeyChecking no
EOF
chmod 600 /root/.ssh/config
```

> **Note:** If a deploy key for another project already exists in `/root/.ssh/config`, use a Host alias to avoid conflicts:
> ```
> Host github-trendradar
>     HostName github.com
>     User git
>     IdentityFile /root/.ssh/trendradar_deploy
>     StrictHostKeyChecking no
> ```
> Then clone with: `git clone git@github-trendradar:vadympetryshyn/trendradar.git`

Print the public key:
```bash
cat /root/.ssh/trendradar_deploy.pub
```

### [USER ACTION] — Add deploy key to GitHub

**Stop here and tell the user:**

> I generated an SSH deploy key on the server. You need to add it to GitHub:
>
> 1. Go to https://github.com/vadympetryshyn/trendradar/settings/keys
> 2. Click **"Add deploy key"**
> 3. Title: `trendradar-server`
> 4. Paste the public key shown above
> 5. Click **"Add key"**
>
> Tell me when done.

**Wait for user confirmation before continuing.**

Test the connection:
```bash
ssh -T git@github.com
```

Expected: `Hi vadympetryshyn/trendradar! You've successfully authenticated...`

---

## Phase 6: Clone Repository

```bash
mkdir -p /var/www
```

```bash
git clone git@github.com:vadympetryshyn/trendradar.git /var/www/trendradar
```

If the directory already exists (redeployment):
```bash
cd /var/www/trendradar && git pull origin main
```

---

## Phase 6.5: Copy Environment Files

The `.env.production` files are gitignored and must be copied manually to the server.

Copy the production env files from local machine to the server:
```bash
scp back/.env.production ubuntu@<server-ip>:/tmp/back.env.production
scp front/.env.production ubuntu@<server-ip>:/tmp/front.env.production
```

Then on the server, move them into place:
```bash
cp /tmp/back.env.production /var/www/trendradar/back/.env.production
cp /tmp/front.env.production /var/www/trendradar/front/.env.production
rm /tmp/back.env.production /tmp/front.env.production
```

Verify:
```bash
ls -la /var/www/trendradar/back/.env.production /var/www/trendradar/front/.env.production
```

> **Important:** Without these files, `docker compose up` will fail with `env file not found` error.

---

## Phase 7: SSL Certificates (Let's Encrypt)

### [USER ACTION] — DNS must be configured first

**Before running this phase, tell the user:**

> Before I can get SSL certificates, these DNS records must point to `51.210.14.13`:
>
> | Record | Type | Value |
> |--------|------|-------|
> | `trendradar.cc` | A | `51.210.14.13` |
> | `www.trendradar.cc` | A | `51.210.14.13` |
> | `api.trendradar.cc` | A | `51.210.14.13` |
>
> **Note:** `trendradar.cc` and `api.trendradar.cc` are on different TLDs. Make sure DNS is configured for both domains.
>
> Tell me when DNS is configured. You can check with:
> ```
> dig @8.8.8.8 trendradar.cc +short
> dig @8.8.8.8 api.trendradar.cc +short
> ```

> **Cloudflare users:** If using Cloudflare DNS proxy (orange cloud), you must temporarily switch all records to **"DNS only"** (grey cloud) before running certbot. The standalone HTTP-01 challenge requires direct access to the server. Re-enable Cloudflare proxy after certificates are obtained. When re-enabling, set SSL/TLS mode to **Full (Strict)**.

**Wait for user confirmation.**

First, check if certificates already exist:
```bash
ls -la /var/www/trendradar/ssl-certificates/fullchain.pem /var/www/trendradar/ssl-certificates/privkey.pem 2>/dev/null
```

**If both files exist** — skip certificate generation and go directly to Phase 8.

**If certificates do NOT exist** — continue with the steps below.

Install certbot:
```bash
apt-get install -y certbot python3-certbot-nginx
```

Stop nginx temporarily (certbot needs port 80):
```bash
systemctl stop nginx
```

Get certificates (covers both TLDs):
```bash
certbot certonly --standalone -d trendradar.cc -d www.trendradar.cc -d api.trendradar.cc --email vadympetryshyn@gmail.com --agree-tos --no-eff-email
```

Move certificates to the project directory:
```bash
mkdir -p /var/www/trendradar/ssl-certificates
cp /etc/letsencrypt/live/trendradar.cc/fullchain.pem /var/www/trendradar/ssl-certificates/fullchain.pem
cp /etc/letsencrypt/live/trendradar.cc/privkey.pem /var/www/trendradar/ssl-certificates/privkey.pem
```

Set up auto-renewal (copies renewed certs to project directory):
```bash
(crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --quiet --pre-hook 'systemctl stop nginx' --post-hook 'cp /etc/letsencrypt/live/trendradar.cc/fullchain.pem /var/www/trendradar/ssl-certificates/fullchain.pem && cp /etc/letsencrypt/live/trendradar.cc/privkey.pem /var/www/trendradar/ssl-certificates/privkey.pem && systemctl start nginx'") | crontab -
```

Verify certs exist:
```bash
ls -la /var/www/trendradar/ssl-certificates/
```

Expected: `fullchain.pem`, `privkey.pem`.

---

## Phase 8: Configure Nginx

Backup default config:
```bash
cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup
```

Copy project nginx config:
```bash
cp /var/www/trendradar/nginx.conf /etc/nginx/nginx.conf
```

**Important:** Before applying, replace `SERVER_IP` in the nginx config with the actual server IP:
```bash
sed -i 's/SERVER_IP/<server-ip>/g' /etc/nginx/nginx.conf
```

Test the config:
```bash
nginx -t
```

Expected: `syntax is ok` and `test is successful`.

Start nginx:
```bash
systemctl start nginx
```

---

## Phase 9: Build & Start Docker Containers

```bash
cd /var/www/trendradar
docker compose -f docker-compose.prod.yml build
```

This will take a few minutes (building Python backend + Next.js frontend).

```bash
docker compose -f docker-compose.prod.yml up -d
```

Wait for services to stabilize:
```bash
sleep 15
docker compose -f docker-compose.prod.yml ps
```

All 6 containers should show `Up` / `running`:
- `front`, `back`, `celery_worker`, `celery_beat`, `postgres`, `redis`

### Run Database Migrations

After containers are up, run Alembic migrations:
```bash
docker compose -f docker-compose.prod.yml exec back alembic upgrade head
```

Expected: All migrations run successfully with `Running upgrade ...` messages.

### Seed Initial Data (first deployment only)

If this is a fresh deployment, seed the niches:
```bash
docker compose -f docker-compose.prod.yml exec back python -m app.seed
```

---

## Phase 10: Verify Deployment

Check containers:
```bash
docker compose -f /var/www/trendradar/docker-compose.prod.yml ps
```

Check nginx:
```bash
systemctl status nginx --no-pager
```

Test endpoints:
```bash
curl -s -o /dev/null -w "Frontend (localhost):       %{http_code}\n" http://localhost:3005
curl -s -o /dev/null -w "Backend (localhost):        %{http_code}\n" http://localhost:3006
curl -s -o /dev/null -w "HTTPS trendradar.cc:       %{http_code}\n" https://trendradar.cc
curl -s -o /dev/null -w "HTTPS api.trendradar.cc:  %{http_code}\n" https://api.trendradar.cc
```

Expected: `200` for all (or `401`/`403` for password-protected frontend — that's OK).

Verify Celery workers are running:
```bash
docker compose -f /var/www/trendradar/docker-compose.prod.yml logs --tail=20 celery_worker
docker compose -f /var/www/trendradar/docker-compose.prod.yml logs --tail=20 celery_beat
```

Expected: Worker shows `celery@... ready`, Beat shows `beat: Starting...`

**Tell the user:**

> Deployment complete! Your site is live:
>
> | URL | Service |
> |-----|---------|
> | https://trendradar.cc | Frontend |
> | https://api.trendradar.cc | Backend API |
>
> Background services running:
> - Celery Worker: Processing trend collection tasks
> - Celery Beat: Scheduled collections every 5 min, expired trend cleanup daily

---

## Useful Commands (for future reference)

### View logs
```bash
docker compose -f /var/www/trendradar/docker-compose.prod.yml logs -f              # all
docker compose -f /var/www/trendradar/docker-compose.prod.yml logs -f back          # backend only
docker compose -f /var/www/trendradar/docker-compose.prod.yml logs -f front         # frontend only
docker compose -f /var/www/trendradar/docker-compose.prod.yml logs -f celery_worker # celery worker
docker compose -f /var/www/trendradar/docker-compose.prod.yml logs -f celery_beat   # celery beat
```

### Restart services
```bash
docker compose -f /var/www/trendradar/docker-compose.prod.yml restart
docker compose -f /var/www/trendradar/docker-compose.prod.yml restart back          # single service
docker compose -f /var/www/trendradar/docker-compose.prod.yml restart celery_worker # restart worker
```

### Redeploy (after pushing new code)
```bash
cd /var/www/trendradar
sudo git pull origin main
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml exec back alembic upgrade head
```

### Stop everything
```bash
docker compose -f /var/www/trendradar/docker-compose.prod.yml down
```

### Nginx
```bash
nginx -t                      # test config
systemctl reload nginx        # reload after config change
systemctl restart nginx       # full restart
```

### SSL renewal (manual)
```bash
certbot renew
cp /etc/letsencrypt/live/trendradar.cc/fullchain.pem /var/www/trendradar/ssl-certificates/fullchain.pem
cp /etc/letsencrypt/live/trendradar.cc/privkey.pem /var/www/trendradar/ssl-certificates/privkey.pem
```

### Check server resources
```bash
df -h                         # disk space
free -h                       # memory
docker system df              # docker disk usage
```

### Clean up Docker (free disk space)
```bash
docker system prune -af
```

### Database access
```bash
docker compose -f /var/www/trendradar/docker-compose.prod.yml exec postgres psql -U trendradar -d trendradar
```

### Celery task monitoring
```bash
# Check active tasks
docker compose -f /var/www/trendradar/docker-compose.prod.yml exec celery_worker celery -A app.celery_app inspect active

# Check scheduled tasks
docker compose -f /var/www/trendradar/docker-compose.prod.yml exec celery_worker celery -A app.celery_app inspect scheduled
```
