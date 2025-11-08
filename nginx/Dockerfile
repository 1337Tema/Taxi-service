# Используем официальный легковесный и АКТУАЛЬНЫЙ образ Nginx
FROM nginx:stable-alpine

# Копируем наш файл конфигурации nginx.conf внутрь образа,
# заменяя стандартный файл конфигурации.
COPY nginx.conf /etc/nginx/conf.d/default.conf