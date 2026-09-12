"""In-memory task repository. The class boundary keeps a future database swap local."""

from typing import Dict, List, Optional, Protocol

from src.models.task import Task, TaskCreate, TaskUpdate, utc_now


class TaskRepository(Protocol):
    """Storage contract used by HTTP routes."""

    def list_tasks(self) -> List[Task]:
        """Return every stored task."""

    def get_task(self, task_id: str) -> Optional[Task]:
        """Return one task or None when it does not exist."""

    def create_task(self, payload: TaskCreate) -> Task:
        """Persist and return a new task."""

    def update_task(self, task_id: str, payload: TaskUpdate) -> Optional[Task]:
        """Update an existing task or return None when missing."""

    def delete_task(self, task_id: str) -> bool:
        """Delete a task. Return True when a record was removed."""

    def clear(self) -> None:
        """Remove all tasks. Used by tests."""


class InMemoryTaskRepository:
    """Simple dictionary-backed store suitable for demos and local development."""

    def __init__(self) -> None:
        self._tasks: Dict[str, Task] = {}

    def list_tasks(self) -> List[Task]:
        """Return every stored task."""
        return list(self._tasks.values())

    def get_task(self, task_id: str) -> Optional[Task]:
        """Return one task or None when it does not exist."""
        return self._tasks.get(task_id)

    def create_task(self, payload: TaskCreate) -> Task:
        """Persist and return a new task."""
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
        """Update an existing task or return None when missing."""
        current = self._tasks.get(task_id)
        if current is None:
            return None

        updates = payload.model_dump(exclude_unset=True)
        updated = current.model_copy(update={**updates, "updated_at": utc_now()})
        self._tasks[task_id] = updated
        return updated

    def delete_task(self, task_id: str) -> bool:
        """Delete a task. Return True when a record was removed."""
        return self._tasks.pop(task_id, None) is not None

    def clear(self) -> None:
        """Remove all tasks. Used by tests."""
        self._tasks.clear()


repository = InMemoryTaskRepository()
