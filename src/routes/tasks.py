# 任务 CRUD 路由，路径和状态码严格按作业表实现。
from fastapi import APIRouter, HTTPException, Response, status

from src.models.task import Task, TaskCreate, TaskUpdate
from src.storage import repository

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[Task], status_code=status.HTTP_200_OK)
def list_tasks() -> list[Task]:
    # GET /tasks：返回当前内存里的全部任务。
    return repository.list_tasks()


@router.get("/{task_id}", response_model=Task, status_code=status.HTTP_200_OK)
def get_task(task_id: str) -> Task:
    # GET /tasks/{id}：找到返回 200，找不到返回 404。
    task = repository.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.post("", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate) -> Task:
    # POST /tasks：校验通过后创建并返回 201。
    # 非法 JSON / 空标题 / 非法 status 会进全局校验异常处理，返回 400。
    return repository.create_task(payload)


@router.put("/{task_id}", response_model=Task, status_code=status.HTTP_200_OK)
def update_task(task_id: str, payload: TaskUpdate) -> Task:
    # PUT /tasks/{id}：更新已有任务。不存在返回 404。
    task = repository.update_task(task_id, payload)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: str) -> Response:
    # DELETE /tasks/{id}：删除成功返回 204 空 body，不存在返回 404。
    deleted = repository.delete_task(task_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
