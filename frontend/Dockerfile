# ============================================================
# Festchuk Frontend — Dockerfile
# ============================================================

# --- Base ---
FROM node:20-alpine AS base

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# --- Development ---
FROM base AS development

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]

# --- Production ---
FROM base AS build

COPY . .

RUN npm run build

# Runtime stage
FROM node:20-alpine AS production

WORKDIR /app

ENV NODE_ENV=production

COPY --from=build /app/package*.json ./
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/.next ./.next
COPY --from=build /app/public ./public
COPY --from=build /app/next.config.js ./
COPY --from=build /app/messages ./messages

EXPOSE 3000

CMD ["npm", "start"]
