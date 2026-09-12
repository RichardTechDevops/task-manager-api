"""Task CRUD routes."""

from fastapi import APIRouter, HTTPException, Response, status

from src.models.task import Task, TaskCreate, TaskUpdate
from src.storage import repository

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[Task], status_code=status.HTTP_200_OK)
def list_tasks() -> list[Task]:
    """Return every task currently stored in memory."""
    return repository.list_tasks()


@router.get("/{task_id}", response_model=Task, status_code=status.HTTP_200_OK)
def get_task(task_id: str) -> Task:
    """Return a single task by ID."""
    task = repository.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.post("", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate) -> Task:
    """Create a new task after request validation."""
    return repository.create_task(payload)


@router.put("/{task_id}", response_model=Task, status_code=status.HTTP_200_OK)
def update_task(task_id: str, payload: TaskUpdate) -> Task:
    """Update task fields that were provided in the request body."""
    task = repository.update_task(task_id, payload)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: str) -> Response:
    """Delete a task. Returns 204 when the record existed."""
    deleted = repository.delete_task(task_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
