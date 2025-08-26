# frontend/Dockerfile
# Multi-stage build for Next.js (Node 20 on Alpine)

# --- deps stage: install node_modules locked by package-lock.json
FROM node:20-alpine AS deps
WORKDIR /app

# Install OS deps if needed (kept minimal for speed)
# RUN apk add --no-cache libc6-compat

# Copy lockfiles and install production+build deps
COPY package.json package-lock.json* ./
RUN npm ci

# --- builder stage: compile the Next.js app
FROM node:20-alpine AS builder
WORKDIR /app

# Reuse node_modules from deps
COPY --from=deps /app/node_modules ./node_modules

# Copy the rest of the app source
# (This includes next.config.js, tsconfig/jsconfig, src/, etc.)
COPY . .

# Build the app (must be "next build" in package.json scripts)
RUN npm run build

# --- runner stage: minimal image to run `next start`
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
# Optionally expose the backend URL to the app at runtime
# ENV NEXT_PUBLIC_API_URL=http://api:8000

# Create a non-root user for security
RUN addgroup -g 1001 nodejs \
 && adduser -S -u 1001 nextjs \
 && mkdir -p /app \
 && chown -R nextjs:nodejs /app

# Copy only what we need to run the built app
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next

# If your app serves files from /public at runtime, ensure the dir exists.
# We don't hard copy it to avoid failing when /public is absent.
RUN mkdir -p public

USER nextjs
EXPOSE 3000

# Start the Next.js server
CMD ["npm", "run", "start", "--", "-p", "3000"]
