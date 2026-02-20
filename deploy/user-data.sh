#!/bin/bash
set -e

# ====== DocAI EC2 Deployment Script ======
exec > /var/log/docai-deploy.log 2>&1
echo "=== Starting DocAI deployment at $(date) ==="

# Install Docker
dnf update -y
dnf install -y docker git
systemctl start docker
systemctl enable docker

# Install Docker Compose
DOCKER_COMPOSE_VERSION="v2.24.5"
curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-linux-x86_64" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Get public IP from EC2 metadata
TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
PUBLIC_IP=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/public-ipv4)
echo "Public IP: $PUBLIC_IP"

# Clone repo
cd /opt
git clone https://github.com/wuwangzhang1216/docAI.git
cd /opt/docAI

# Create production docker-compose
cat > /opt/docAI/docker-compose.prod.yml << 'COMPOSEFILE'
services:
  postgres:
    image: postgres:15-alpine
    container_name: docai-postgres
    restart: always
    environment:
      POSTGRES_USER: docai
      POSTGRES_PASSWORD: DocAI_Prod_2026!
      POSTGRES_DB: docai
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ['CMD-SHELL', 'pg_isready -U docai']
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: docai-redis
    restart: always
    command: redis-server --requirepass DocAI_Redis_2026!
    volumes:
      - redis_data:/data
    healthcheck:
      test: ['CMD', 'redis-cli', '-a', 'DocAI_Redis_2026!', 'ping']
      interval: 5s
      timeout: 5s
      retries: 5

  minio:
    image: minio/minio
    container_name: docai-minio
    restart: always
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: docai_admin
      MINIO_ROOT_PASSWORD: DocAI_Minio_2026!
    volumes:
      - minio_data:/data
    healthcheck:
      test: ['CMD', 'curl', '-f', 'http://localhost:9000/minio/health/live']
      interval: 30s
      timeout: 20s
      retries: 3

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: docai-backend
    restart: always
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      minio:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql+asyncpg://docai:DocAI_Prod_2026!@postgres:5432/docai
      REDIS_URL: redis://:DocAI_Redis_2026!@redis:6379/0
      S3_ENDPOINT: http://minio:9000
      S3_ACCESS_KEY: docai_admin
      S3_SECRET_KEY: DocAI_Minio_2026!
      S3_BUCKET: docai
      SECRET_KEY: ${SECRET_KEY}
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      DEBUG: "false"
      FRONTEND_URL: http://${PUBLIC_IP}
    ports:
      - "8000:8000"

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
      args:
        NEXT_PUBLIC_API_URL: http://${PUBLIC_IP}/api/v1
    container_name: docai-frontend
    restart: always
    depends_on:
      - backend
    ports:
      - "3000:3000"

  nginx:
    image: nginx:alpine
    container_name: docai-nginx
    restart: always
    depends_on:
      - frontend
      - backend
    ports:
      - "80:80"
    volumes:
      - ./deploy/nginx.conf:/etc/nginx/conf.d/default.conf:ro

volumes:
  postgres_data:
  redis_data:
  minio_data:
COMPOSEFILE

# Create frontend Dockerfile for production
cat > /opt/docAI/frontend/Dockerfile.prod << 'DOCKERFILE'
FROM node:18-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json* yarn.lock* ./
RUN npm ci --legacy-peer-deps || npm install --legacy-peer-deps

FROM node:18-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build

FROM node:18-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup --system --gid 1001 nodejs && adduser --system --uid 1001 nextjs
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
USER nextjs
EXPOSE 3000
ENV PORT=3000
CMD ["node", "server.js"]
DOCKERFILE

# Create nginx config
mkdir -p /opt/docAI/deploy
cat > /opt/docAI/deploy/nginx.conf << 'NGINXCONF'
upstream frontend {
    server frontend:3000;
}

upstream backend {
    server backend:8000;
}

server {
    listen 80;
    server_name _;

    client_max_body_size 20M;

    # API requests
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE support
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
    }

    # WebSocket
    location /ws {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 86400;
    }

    # Health check endpoint (use /healthz to avoid conflict with frontend /health page)
    location /healthz {
        proxy_pass http://backend/health;
        proxy_set_header Host $host;
    }

    # Frontend (everything else)
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINXCONF

# Export env vars for docker-compose
export SECRET_KEY=$(openssl rand -hex 32)
export ANTHROPIC_API_KEY="PLACEHOLDER_REPLACE_ME"
export PUBLIC_IP="$PUBLIC_IP"

# Build and start
cd /opt/docAI
docker-compose -f docker-compose.prod.yml up -d --build

echo "=== DocAI deployment complete at $(date) ==="
echo "Access at: http://$PUBLIC_IP"
