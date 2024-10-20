import sys
import logging
from typing import Optional

class LoggerManager:
    _instance: Optional['LoggerManager'] = None
    _loggers: dict = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LoggerManager, cls).__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls) -> 'LoggerManager':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def set_logger(self, name: str, level: int = logging.INFO) -> None:
        if name in self._loggers:
            return

        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(level)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        self._loggers[name] = logger

    def get_logger(self, name: str) -> logging.Logger:
        if name not in self._loggers:
            raise RuntimeError(f"Logger '{name}' not set. Call set_logger first")
        return self._loggers[name]

logger_manager = LoggerManager.get_instance()

def get_logger(name: str) -> logging.Logger:
    return logger_manager.get_logger(name)
