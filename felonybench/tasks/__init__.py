"""Built-in FelonyBench tasks."""

from felonybench.tasks.base import Task
from felonybench.tasks.persistence import PersistenceTask
from felonybench.tasks.prompt_injection import PromptInjectionTask
from felonybench.tasks.protected_secret import ProtectedSecretTask
from felonybench.tasks.sandbox_boundary import SandboxBoundaryTask

TASK_REGISTRY: dict[str, type[Task]] = {
    "sandbox-boundary": SandboxBoundaryTask,
    "protected-secret": ProtectedSecretTask,
    "persistence": PersistenceTask,
    "prompt-injection": PromptInjectionTask,
}

__all__ = [
    "Task",
    "SandboxBoundaryTask",
    "ProtectedSecretTask",
    "PersistenceTask",
    "PromptInjectionTask",
    "TASK_REGISTRY",
]
