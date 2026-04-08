class AppException(Exception):
    """Base class for all application-level domain exceptions."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


from app.exceptions.task_exceptions import TaskAlreadyProcessed, TaskNotFound  # noqa: E402

__all__ = ["AppException", "TaskNotFound", "TaskAlreadyProcessed"]
