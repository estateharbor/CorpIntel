FROM node:20-alpine AS deps
WORKDIR /app/frontend-next
COPY package.json yarn.lock* ./
RUN yarn install --frozen-lockfile || yarn install

FROM node:20-alpine AS build
WORKDIR /app/frontend-next
ARG NEXT_PUBLIC_BACKEND_URL
ARG NEXT_PUBLIC_SITE_URL
ENV NEXT_PUBLIC_BACKEND_URL=$NEXT_PUBLIC_BACKEND_URL
ENV NEXT_PUBLIC_SITE_URL=$NEXT_PUBLIC_SITE_URL
COPY --from=deps /app/frontend-next/node_modules ./node_modules
COPY . ./
RUN yarn build

FROM node:20-alpine AS runner
WORKDIR /app/frontend-next
ENV NODE_ENV=production
ENV PORT=3000

COPY --from=build /app/frontend-next/public ./public
COPY --from=build /app/frontend-next/.next/standalone ./
COPY --from=build /app/frontend-next/.next/static ./.next/static

EXPOSE 3000
CMD ["node", "server.js"]
