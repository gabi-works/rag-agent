import json
from abc import ABC, abstractmethod

from ingestion import logger
from ingestion.states import FileState


class BaseNode(ABC):
    def __init__(self, verbose=False, **kwargs):
        self.name = self.__class__.__name__
        self.verbose = verbose

    @abstractmethod
    def execute(self, state: FileState) -> FileState:
        pass

    def log(self, message: str, **kwargs):
        if self.verbose:
            log_data = {
                "class": self.name,
                "message": message,
            }

            if kwargs:
                log_data["extra"] = kwargs

            log_message = json.dumps(log_data, ensure_ascii=False, indent=2)
            log_method = getattr(logger, "info", logger.info)
            log_method(log_message)

    def __call__(self, state: FileState) -> FileState:
        return self.execute(state)