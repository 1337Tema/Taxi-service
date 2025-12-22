import { useEffect, useRef } from 'react';
import { useAppContext } from '../context/AppContext';

const WEBSOCKET_URL = 'ws://127.0.0.1:8000/api/v1/notifications/ws';

export const useWebSocket = (token: string | null) => {
  const { addNotification } = useAppContext();
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (token && !ws.current) {
      console.log('Попытка установить WebSocket соединение...');

      const socket = new WebSocket(`${WEBSOCKET_URL}?token=${token}`);
      ws.current = socket;

      socket.onopen = () => {
        console.log('✅ WebSocket соединение установлено.');
        socket.send('ping');
      };

      // ########### НАЧАЛО БЛОКА ИЗМЕНЕНИЙ ###########
      socket.onmessage = (event) => {
        // Сначала проверяем, не является ли сообщение служебным "pong"
        if (event.data === 'pong') {
          console.log('Получен pong от сервера.');
          return; // Прерываем дальнейшую обработку
        }
        
        // Если это не "pong", пытаемся обработать как JSON
        try {
          const message = JSON.parse(event.data);
          console.log('📥 Получено JSON сообщение WebSocket:', message);

          if (message.type && message.data) {
            addNotification({
              type: message.type,
              data: message.data,
            });
          }
        } catch (error) {
          console.error('Ошибка парсинга WebSocket JSON сообщения:', error);
          console.error('Полученные данные:', event.data);
        }
      };
      // ########### КОНЕЦ БЛОКА ИЗМЕНЕНИЙ ###########

      socket.onerror = (error) => {
        console.error('❌ Ошибка WebSocket:', error);
      };

      socket.onclose = (event) => {
        console.log(`🔌 WebSocket соединение закрыто: Код ${event.code}, Причина: ${event.reason}`);
        ws.current = null;
      };
    }

    return () => {
      if (ws.current && ws.current.readyState === WebSocket.OPEN) {
        console.log('Закрытие WebSocket соединения...');
        ws.current.close();
      }
    };
  }, [token, addNotification]);
};