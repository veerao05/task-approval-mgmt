from app.exceptions import AppException


class TaskNotFound(AppException):
    """Raised when a task with the given ID does not exist."""

    def __init__(self, task_id: str) -> None:
        self.task_id = task_id
        super().__init__(f"Task '{task_id}' not found.")


class TaskAlreadyProcessed(AppException):
    """Raised when approve/reject is attempted on a non-PENDING task."""

    def __init__(self, task_id: str, current_status: str) -> None:
        self.task_id = task_id
        self.current_status = current_status
        super().__init__(
            f"Task '{task_id}' is already '{current_status}'. "
            "Only PENDING tasks can be approved or rejected."
        )
