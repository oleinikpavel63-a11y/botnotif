# Mini App static build + nginx reverse proxy (FULL mode front door).
FROM node:22-alpine AS build
WORKDIR /build
COPY apps/mini-app/package*.json ./
RUN npm ci || npm install
COPY apps/mini-app ./
# VITE_API_BASE_URL is same-origin in production (nginx proxies /api).
ENV VITE_API_BASE_URL=""
RUN npm run build

FROM nginx:1.27-alpine
COPY infra/nginx/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /build/dist /usr/share/nginx/html/app
EXPOSE 80
