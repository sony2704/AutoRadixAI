"""
WebSocket endpoint for real-time inference progress updates.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

router = APIRouter()
logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections, grouped by study_id."""

    def __init__(self) -> None:
        self._connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, study_id: str) -> None:
        await websocket.accept()
        if study_id not in self._connections:
            self._connections[study_id] = set()
        self._connections[study_id].add(websocket)
        logger.debug("WS connected: study=%s total=%d", study_id, len(self._connections[study_id]))

    def disconnect(self, websocket: WebSocket, study_id: str) -> None:
        if study_id in self._connections:
            self._connections[study_id].discard(websocket)
            if not self._connections[study_id]:
                del self._connections[study_id]

    async def broadcast(self, study_id: str, message: dict) -> None:
        dead = set()
        for ws in self._connections.get(study_id, set()):
            try:
                if ws.client_state == WebSocketState.CONNECTED:
                    await ws.send_json(message)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self.disconnect(ws, study_id)


manager = ConnectionManager()


@router.websocket("/inference/{study_id}")
async def inference_progress(websocket: WebSocket, study_id: str) -> None:
    """
    Real-time inference progress for a study.
    Client subscribes; server pushes status updates.
    """
    await manager.connect(websocket, study_id)
    try:
        while True:
            # Keep connection alive — client can send heartbeat
            data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except asyncio.TimeoutError:
        await websocket.send_json({"type": "heartbeat"})
    except WebSocketDisconnect:
        manager.disconnect(websocket, study_id)
        logger.debug("WS disconnected: study=%s", study_id)
    except Exception as exc:
        logger.error("WS error: %s", exc)
        manager.disconnect(websocket, study_id)


async def push_inference_update(study_id: str, payload: dict) -> None:
    """Call this from Celery task callbacks to push updates to clients."""
    await manager.broadcast(study_id, {"type": "inference_update", **payload})
