import axios from 'axios';

// Создаем настроенный экземпляр axios
export const api = axios.create({
  // Адрес нашего Python-сервера (локально)
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Добавляем "перехватчик" (interceptor).
// Он будет автоматически вставлять JWT-токен в каждый запрос, если мы залогинены.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});