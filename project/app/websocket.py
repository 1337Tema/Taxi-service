# app/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from . import services, dependencies
from .redis import get_redis
import redis
import json

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str,
    redis_client: redis.Redis = Depends(get_redis)
):
    """WebSocket соединение для реального времени"""
    # Аутентификация по токену
    user = await dependencies.get_current_user_ws(token)
    if not user:
        await websocket.close(code=1008)
        return
    
    await services.connection_manager.connect(websocket, user.id)
    
    try:
        while True:
            data = await websocket.receive_text()
            # Обработка входящих сообщений (если нужно)
            message = json.loads(data)
            await handle_websocket_message(message, user, redis_client)
            
    except WebSocketDisconnect:
        services.connection_manager.disconnect(user.id)

async def handle_websocket_message(message: dict, user, redis_client):
    """Обработка входящих WebSocket сообщений"""
    message_type = message.get("type")
    
    if message_type == "subscribe_ride_updates":
        ride_id = message.get("ride_id")
        await services.subscribe_to_ride_updates(redis_client, user.id, ride_id)
    
    elif message_type == "unsubscribe_ride_updates":
        ride_id = message.get("ride_id")
        await services.unsubscribe_from_ride_updates(redis_client, user.id, ride_id)