FROM node:20-alpine AS web-deps

RUN apk add --no-cache libc6-compat
WORKDIR /web

COPY web/package.json web/pnpm-lock.yaml ./
RUN corepack enable pnpm && pnpm i --frozen-lockfile

FROM node:20-alpine AS web-builder

RUN apk add --no-cache libc6-compat
WORKDIR /web

COPY --from=web-deps /web/node_modules ./node_modules
COPY web/ .

ARG NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
ENV NEXT_PUBLIC_BACKEND_URL=${NEXT_PUBLIC_BACKEND_URL}
ENV NEXT_TELEMETRY_DISABLED=1

RUN corepack enable pnpm && pnpm build

FROM python:3.10-slim AS development

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
  curl ca-certificates ffmpeg \
  nodejs npm \
  && npm i -g corepack \
  && corepack enable pnpm \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app/backend
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app/web
COPY --from=web-deps /web/node_modules ./node_modules

WORKDIR /app
COPY entrypoint.dev.sh /app/entrypoint.dev.sh
RUN chmod +x /app/entrypoint.dev.sh

EXPOSE 8000 3000

ENV NEXT_TELEMETRY_DISABLED=1
ENV HOSTNAME=0.0.0.0

ENTRYPOINT ["/app/entrypoint.dev.sh"]

FROM python:3.10-slim AS production

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
  curl ca-certificates ffmpeg \
  nodejs \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app/backend
COPY backend/ .
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app/web
COPY --from=web-builder /web/public ./public
COPY --from=web-builder /web/.next/standalone ./
COPY --from=web-builder /web/.next/static ./.next/static

WORKDIR /app
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000 3000

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV HOSTNAME=0.0.0.0

ENTRYPOINT ["/app/entrypoint.sh"]
