"""API эндпоинт для WebSocket-уведомлений."""

import logging
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from src.services.notification_service import notification_manager
from .dependencies import get_current_user_id_stub

router = APIRouter(prefix="/notifications", tags=["Notifications"])
logger = logging.getLogger(__name__)


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: int = Depends(get_current_user_id_stub)
):
    """
    Основной эндпоинт для WebSocket-соединений.

    Клиент должен подключаться по адресу:
    ws://<host>/api/v1/notifications/ws?token=<jwt_token>

    Принимает соединение и держит его открытым, пока клиент не отключится.
    """
    await notification_manager.connect(user_id, websocket)
    try:
        while True:
            # Просто держим соединение открытым, ожидая данных от клиента.
            # В нашей архитектуре клиент в основном слушает.
            # Можно добавить обработку входящих сообщений, например, "ping".
            data = await websocket.receive_text()
            logger.debug(f"Получено сообщение от пользователя {user_id}: {data}")
            # Пример "pong" ответа на "ping" клиента
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        # Это исключение возникает, когда клиент закрывает соединение
        logger.info(f"Клиент {user_id} отключился.")
    finally:
        # Вне зависимости от причины, удаляем соединение из менеджера
        notification_manager.disconnect(user_id)