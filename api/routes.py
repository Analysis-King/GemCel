from fastapi import APIRouter, WebSocket
from core.emitter import EventEmitter
from pydantic import BaseModel
from uuid import uuid4


from api.websocket_manager import manager
from core.multi_agent_system import MultiAgentSystem
from core.emitter import EventEmitter

router = APIRouter()


TASKS = {}


class TaskRequest(BaseModel):
    task: str


@router.post("/api/task")
async def create_task(req: TaskRequest):

    task_id = str(uuid4())

    TASKS[task_id] = req.task

    return {
        "task_id": task_id
    }


@router.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):

    await manager.connect(task_id, websocket)

    try:

        task = TASKS.get(task_id)

        emitter = EventEmitter(manager, task_id)

        system = MultiAgentSystem(emitter)

        await system.process(task)

    except Exception as e:

        await manager.send(task_id, {
            "event": "final",
            "data": {
                "answer": str(e)
            }
        })

    finally:
        manager.disconnect(task_id)