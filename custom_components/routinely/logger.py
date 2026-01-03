"""Logging utilities for the Routinely integration.

Home Assistant uses Python's standard logging module. Log levels can be controlled via:
1. Integration options (Settings → Devices & Services → Routinely → Configure)
2. configuration.yaml under `logger:` section:
   ```yaml
   logger:
     default: warning
     logs:
       custom_components.routinely: debug
   ```

Log Levels:
- DEBUG: Detailed diagnostic information (timer ticks, state changes)
- INFO: Routine/task lifecycle events, service calls
- WARNING: Recoverable issues, deprecated usage
- ERROR: Failures that prevent operations
- CRITICAL: Integration cannot function
"""
from __future__ import annotations

import logging
from enum import IntEnum
from functools import wraps
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

# Module-level logger for the integration
_LOGGER = logging.getLogger(__name__)

# Package root logger name
LOGGER_NAME = "custom_components.routinely"


class LogLevel(IntEnum):
    """Log level enum matching Python logging levels."""

    DEBUG = logging.DEBUG  # 10
    INFO = logging.INFO  # 20
    WARNING = logging.WARNING  # 30
    ERROR = logging.ERROR  # 40
    CRITICAL = logging.CRITICAL  # 50

    @classmethod
    def from_string(cls, level: str) -> "LogLevel":
        """Convert string to LogLevel."""
        level_map = {
            "debug": cls.DEBUG,
            "verbose": cls.DEBUG,  # Map verbose to debug
            "info": cls.INFO,
            "log": cls.INFO,  # Map generic 'log' to info
            "warning": cls.WARNING,
            "warn": cls.WARNING,
            "error": cls.ERROR,
            "critical": cls.CRITICAL,
        }
        return level_map.get(level.lower(), cls.INFO)


def get_logger(name: str | None = None) -> logging.Logger:
    """Get a logger for the integration.
    
    Args:
        name: Optional sub-module name. If provided, creates logger as
              'custom_components.routinely.{name}'
    
    Returns:
        Configured logger instance
    """
    if name:
        return logging.getLogger(f"{LOGGER_NAME}.{name}")
    return logging.getLogger(LOGGER_NAME)


def set_log_level(level: LogLevel | str | int) -> None:
    """Set the log level for all Routinely loggers.
    
    Args:
        level: Log level as LogLevel enum, string, or int
    """
    if isinstance(level, str):
        level = LogLevel.from_string(level)
    elif isinstance(level, int) and not isinstance(level, LogLevel):
        # Clamp to valid range
        level = max(logging.DEBUG, min(logging.CRITICAL, level))
    
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(int(level))
    _LOGGER.info("Routinely log level set to: %s", logging.getLevelName(int(level)))


def configure_logging(hass: HomeAssistant, level: str = "info") -> None:
    """Configure logging for the integration.
    
    This is called during integration setup to apply user-configured log level.
    
    Args:
        hass: Home Assistant instance
        level: Log level string from configuration
    """
    log_level = LogLevel.from_string(level)
    set_log_level(log_level)


class RoutinelyLogger:
    """Enhanced logger with context and structured logging support.
    
    Usage:
        logger = RoutinelyLogger("engine")
        logger.debug("Timer tick", task_id="abc123", remaining=45)
        logger.info("Routine started", routine_id="morning", tasks=5)
    """

    def __init__(self, name: str | None = None) -> None:
        """Initialize the logger.
        
        Args:
            name: Sub-module name for the logger
        """
        self._logger = get_logger(name)
        self._context: dict[str, Any] = {}

    def set_context(self, **kwargs: Any) -> None:
        """Set persistent context that will be included in all log messages."""
        self._context.update(kwargs)

    def clear_context(self) -> None:
        """Clear all context."""
        self._context.clear()

    def _format_message(self, message: str, **kwargs: Any) -> str:
        """Format message with context and additional kwargs."""
        all_context = {**self._context, **kwargs}
        if all_context:
            context_str = " | ".join(f"{k}={v}" for k, v in all_context.items())
            return f"{message} [{context_str}]"
        return message

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message with optional context."""
        self._logger.debug(self._format_message(message, **kwargs))

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message with optional context."""
        self._logger.info(self._format_message(message, **kwargs))

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message with optional context."""
        self._logger.warning(self._format_message(message, **kwargs))

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message with optional context."""
        self._logger.error(self._format_message(message, **kwargs))

    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message with optional context."""
        self._logger.critical(self._format_message(message, **kwargs))

    def exception(self, message: str, **kwargs: Any) -> None:
        """Log exception with traceback."""
        self._logger.exception(self._format_message(message, **kwargs))


def log_call(level: str = "debug") -> Callable:
    """Decorator to log function calls with arguments and return values.
    
    Usage:
        @log_call("info")
        async def start_routine(self, routine_id: str) -> bool:
            ...
    """
    def decorator(func: Callable) -> Callable:
        logger = get_logger(func.__module__.split(".")[-1])
        log_func = getattr(logger, level, logger.debug)

        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            func_name = func.__qualname__
            log_func("CALL %s(args=%s, kwargs=%s)", func_name, args[1:], kwargs)
            try:
                result = await func(*args, **kwargs)
                log_func("RETURN %s -> %s", func_name, result)
                return result
            except Exception as e:
                logger.error("EXCEPTION %s: %s", func_name, e)
                raise

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            func_name = func.__qualname__
            log_func("CALL %s(args=%s, kwargs=%s)", func_name, args[1:], kwargs)
            try:
                result = func(*args, **kwargs)
                log_func("RETURN %s -> %s", func_name, result)
                return result
            except Exception as e:
                logger.error("EXCEPTION %s: %s", func_name, e)
                raise

        if asyncio_iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def asyncio_iscoroutinefunction(func: Callable) -> bool:
    """Check if function is a coroutine function."""
    import asyncio
    return asyncio.iscoroutinefunction(func)


# Pre-configured loggers for each module
class Loggers:
    """Pre-configured loggers for each module."""
    
    init = RoutinelyLogger("init")
    config = RoutinelyLogger("config")
    storage = RoutinelyLogger("storage")
    engine = RoutinelyLogger("engine")
    coordinator = RoutinelyLogger("coordinator")
    services = RoutinelyLogger("services")
    notifications = RoutinelyLogger("notifications")
    sensor = RoutinelyLogger("sensor")
    binary_sensor = RoutinelyLogger("binary_sensor")
