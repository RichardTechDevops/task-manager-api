# 任务仓储层。
# 作业允许内存存储，但要求模型可扩展：路由只依赖 TaskRepository 协议，
# 以后换成数据库时，只要新写一个实现类，不用改 routes。
from typing import Dict, List, Optional, Protocol

from src.models.task import Task, TaskCreate, TaskUpdate, utc_now


class TaskRepository(Protocol):
    # 存储接口约定。Protocol 不会被实例化，只用来约束实现类的方法签名。
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
    # 当前实现：进程内字典。重启容器后数据会清空。
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

        # exclude_unset=True：只覆盖请求里真正传了的字段。
        updates = payload.model_dump(exclude_unset=True)
        updated = current.model_copy(update={**updates, "updated_at": utc_now()})
        self._tasks[task_id] = updated
        return updated

    def delete_task(self, task_id: str) -> bool:
        # pop 返回原对象则删除成功，返回 None 表示不存在。
        return self._tasks.pop(task_id, None) is not None

    def clear(self) -> None:
        self._tasks.clear()


# 进程级单例。当前只有一个 worker，所有请求共享这份内存数据。
repository = InMemoryTaskRepository()
