type MessageHandler = (data: any) => void;

class WebSocketService {
  private ws: WebSocket | null = null;
  private handlers: MessageHandler[] = [];

  connect() {
    const token = localStorage.getItem('token');
    if (!token) return;

    // Подключаемся к вебсокету бэкенда
    const host = window.location.host;
    this.ws = new WebSocket(`ws://${host}/api/v1/notifications/ws?token=${token}`);

    this.ws.onopen = () => {
      console.log('🟢 WS Connected');
    };

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        console.log('📩 WS Message:', message);
        // Рассылаем сообщение всем подписчикам
        this.handlers.forEach(handler => handler(message));
      } catch (e) {
        console.error('WS Parse Error', e);
      }
    };

    this.ws.onclose = () => {
      console.log('🔴 WS Disconnected');
      // Можно добавить авто-реконнект, но для курсовой хватит и так
    };
  }

  subscribe(handler: MessageHandler) {
    this.handlers.push(handler);
    // Функция отписки
    return () => {
      this.handlers = this.handlers.filter(h => h !== handler);
    };
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

export const wsService = new WebSocketService();