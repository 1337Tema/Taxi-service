"""
Публикация событий в Redis Streams.
"""

from typing import Mapping, Any
import json
import asyncio

from redis.asyncio import Redis
from src.core.redis import redis_pool

STREAM_ORDERS = "order_events"


async def _get_redis_client() -> Redis:
    return Redis(connection_pool=redis_pool)


async def publish_event(event_name: str, payload: Mapping[str, Any]) -> str:
    client = await _get_redis_client()
    try:
        data = {
            "event": event_name,
            "data": json.dumps(payload, ensure_ascii=False),
        }
        return await client.xadd(STREAM_ORDERS, data)
    finally:
        try:
            await client.close()
        except Exception:
            await asyncio.sleep(0)


async def publish_order_created(payload: Mapping[str, Any]) -> str:
    return await publish_event("OrderCreated", payload)


async def publish_driver_assigned(payload: Mapping[str, Any]) -> str:
    return await publish_event("DriverAssigned", payload)


async def publish_ride_completed(payload: Mapping[str, Any]) -> str:
    return await publish_event("RideCompleted", payload)
