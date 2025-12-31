# Этап 1: Сборка
FROM node:20-alpine AS build-stage
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Этап 2: Раздача (используем легковесный образ)
FROM nginx:stable-alpine
# Копируем собранный фронтенд в папку, которую понимает nginx
COPY --from=build-stage /app/dist /usr/share/nginx/html
# Копируем конфиг (мы обновим его на следующем шаге)
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]