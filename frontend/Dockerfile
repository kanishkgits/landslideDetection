FROM node:20-alpine AS build
WORKDIR /web
COPY frontend/package*.json ./
RUN npm install
COPY frontend ./
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build
FROM nginx:alpine
COPY --from=build /web/dist /usr/share/nginx/html
EXPOSE 80
