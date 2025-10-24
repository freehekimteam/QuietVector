# build stage
FROM node:20-alpine AS build
WORKDIR /web
COPY package.json package-lock.json* pnpm-lock.yaml* yarn.lock* .npmrc* ./ 2>/dev/null || true
RUN npm i --no-audit --no-fund
COPY . .
RUN npm run build

# serve stage
FROM nginx:alpine
COPY --from=build /web/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
