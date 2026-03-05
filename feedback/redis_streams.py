"""Redis Streams event bus for A2Alaw five-channel architecture."""

from __future__ import annotations

import json
import time
from typing import Any

import redis

STREAMS = [
    "user:intent",
    "agent:plan",
    "system:logs",
    "agent:report",
    "agent:audit",
]


class EventBus:
    def __init__(self, redis_url: str = "redis://:a2alaw-dev@localhost:6380/0"):
        self.r = redis.from_url(redis_url, decode_responses=True)

    def publish(self, stream: str, data: dict[str, Any]) -> str:
        """Publish an event to a stream. Returns the message ID."""
        if stream not in STREAMS:
            raise ValueError(f"Unknown stream: {stream}. Valid: {STREAMS}")
        flat = {k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) for k, v in data.items()}
        flat["_ts"] = str(time.time())
        return self.r.xadd(stream, flat)

    def consume(
        self,
        stream: str,
        group: str = "a2alaw",
        consumer: str = "worker-0",
        count: int = 1,
        block_ms: int = 5000,
    ) -> list[tuple[str, dict]]:
        """Consume messages from a stream using consumer groups."""
        try:
            self.r.xgroup_create(stream, group, id="0", mkstream=True)
        except redis.ResponseError:
            pass  # Group already exists

        messages = self.r.xreadgroup(group, consumer, {stream: ">"}, count=count, block=block_ms)
        if not messages:
            return []

        result = []
        for _, entries in messages:
            for msg_id, fields in entries:
                parsed = {}
                for k, v in fields.items():
                    if k == "_ts":
                        continue
                    try:
                        parsed[k] = json.loads(v)
                    except (json.JSONDecodeError, TypeError):
                        parsed[k] = v
                result.append((msg_id, parsed))
                self.r.xack(stream, group, msg_id)
        return result

    def init_streams(self) -> None:
        """Initialize all five streams."""
        for stream in STREAMS:
            self.r.xgroup_create(stream, "a2alaw", id="0", mkstream=True)
            print(f"  Initialized stream: {stream}")
