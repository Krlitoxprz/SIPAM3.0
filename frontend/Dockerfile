# ── Frontend React — SIPAM-USCO — Multi-stage build ──────────────────────────

# Stage 1: Build React app
FROM node:20-slim AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --prefer-offline
COPY . .
RUN npm run build

# Stage 2: Serve with Nginx (includes reverse proxy config)
FROM nginx:1.27-alpine

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy built React app
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config (injected at build time; falls back to template)
COPY nginx.conf /etc/nginx/conf.d/sipam.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget -qO- http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
