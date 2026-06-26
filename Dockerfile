FROM node:25 AS web-deps

WORKDIR /web

COPY web/package.json web/pnpm-lock.yaml ./
RUN npm install -g pnpm@9 && pnpm install --frozen-lockfile

FROM node:25 AS web-builder

WORKDIR /web

COPY --from=web-deps /web/node_modules ./node_modules
COPY web/ .

ENV NEXT_TELEMETRY_DISABLED=1

RUN npm install -g pnpm@9 && pnpm build

FROM python:3.13-slim AS development

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
  curl ca-certificates ffmpeg nginx git \
  nodejs npm \
  && npm install -g pnpm@9 \
  && rm -f /etc/nginx/sites-enabled/default \
  && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# NOTE: Set UV_PROJECT_ENVIRONMENT to avoid issues with overwriting the dependencies
ENV UV_COMPILE_BYTECODE=1 \
  UV_PYTHON="python3" \
  UV_PROJECT_ENVIRONMENT="/app/.venv" \
  PATH="/app/.venv/bin:$PATH"

WORKDIR /app/backend
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev

WORKDIR /app/web
COPY --from=web-deps /web/node_modules ./node_modules

WORKDIR /app
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf
COPY entrypoint.dev.sh /app/entrypoint.dev.sh
RUN chmod +x /app/entrypoint.dev.sh

EXPOSE 80

ENV NEXT_TELEMETRY_DISABLED=1
ENV HOSTNAME=0.0.0.0

ENTRYPOINT ["/app/entrypoint.dev.sh"]

FROM python:3.13-slim AS production

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
  curl ca-certificates ffmpeg nginx git \
  nodejs \
  && rm -f /etc/nginx/sites-enabled/default \
  && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
  UV_PYTHON="python3" \
  UV_PROJECT_ENVIRONMENT="/app/.venv" \
  PATH="/app/.venv/bin:$PATH"

WORKDIR /app/backend
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev
COPY backend/ .

WORKDIR /app/web
COPY --from=web-builder /web/public ./public
COPY --from=web-builder /web/.next/standalone ./
COPY --from=web-builder /web/.next/static ./.next/static

WORKDIR /app
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 80

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV HOSTNAME=0.0.0.0

ENTRYPOINT ["/app/entrypoint.sh"]
