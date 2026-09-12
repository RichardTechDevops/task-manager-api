from typing import Dict, List, Optional, Protocol

from src.models.task import Task, TaskCreate, TaskUpdate, utc_now


class TaskRepository(Protocol):
    def list_tasks(self) -> List[Task]:
        ...

    def get_task(self, task_id: str) -> Optional[Task]:
        ...

    def create_task(self, payload: TaskCreate) -> Task:
        ...

    def update_task(self, task_id: str, payload: TaskUpdate) -> Optional[Task]:
        ...

    def delete_task(self, task_id: str) -> bool:
        ...

    def clear(self) -> None:
        ...


class InMemoryTaskRepository:
    def __init__(self) -> None:
        self._tasks: Dict[str, Task] = {}

    def list_tasks(self) -> List[Task]:
        return list(self._tasks.values())

    def get_task(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)

    def create_task(self, payload: TaskCreate) -> Task:
        now = utc_now()
        task = Task(
            title=payload.title,
            description=payload.description,
            status=payload.status,
            created_at=now,
            updated_at=now,
        )
        self._tasks[task.id] = task
        return task

    def update_task(self, task_id: str, payload: TaskUpdate) -> Optional[Task]:
        current = self._tasks.get(task_id)
        if current is None:
            return None

        updates = payload.model_dump(exclude_unset=True)
        updated = current.model_copy(update={**updates, "updated_at": utc_now()})
        self._tasks[task_id] = updated
        return updated

    def delete_task(self, task_id: str) -> bool:
        return self._tasks.pop(task_id, None) is not None

    def clear(self) -> None:
        self._tasks.clear()


repository = InMemoryTaskRepository()
