"""
Сервис для управления WebSocket-соединениями и отправки real-time уведомлений.
"""
import logging
from typing import Dict, List, Optional

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Управляет активными WebSocket-соединениями.
    Хранит сопоставление user_id -> WebSocket.
    """

    def __init__(self):
        # Словарь для хранения активных соединений: {user_id: WebSocket}
        self.active_connections: Dict[int, WebSocket] = {}


    async def connect(self, user_id: int, websocket: WebSocket):
        """Принимает новое WebSocket-соединение."""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"Новое WebSocket-соединение для пользователя {user_id}.")


    def disconnect(self, user_id: int):
        """Отключает WebSocket-соединение."""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"WebSocket-соединение для пользователя {user_id} закрыто.")


    async def send_personal_message(self, user_id: int, message: dict) -> bool:
        """
        Отправляет JSON-сообщение конкретному пользователю.

        Returns:
            True, если сообщение отправлено успешно, иначе False.
        """
        websocket = self.active_connections.get(user_id)
        if websocket:
            try:
                await websocket.send_json(message)
                logger.info(f"Сообщение {message['type']} отправлено пользователю {user_id}.")
                return True
            except Exception as e:
                logger.error(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")
                # Если отправка не удалась, соединение, вероятно, мертво.
                self.disconnect(user_id)
                return False
        else:
            logger.warning(f"Попытка отправить сообщение не подключенному пользователю {user_id}.")
            return False

# Создаем синглтон-экземпляр менеджера, который будет использоваться во всем приложении
notification_manager = ConnectionManager()