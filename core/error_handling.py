"""
==========================================================
JARVIS - PhD-Level Error Handling System
==========================================================
Structured error types, propagation, and recovery strategies
Based on Railway-Oriented Programming and Result types
==========================================================
"""

from typing import Optional, Any, Callable, TypeVar, Generic
from dataclasses import dataclass
from enum import Enum
import logging
import traceback
from datetime import datetime

logger = logging.getLogger(__name__)

T = TypeVar('T')
E = TypeVar('E')


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"           # Recoverable, no user impact
    MEDIUM = "medium"     # Degraded functionality
    HIGH = "high"         # Service disruption
    CRITICAL = "critical" # System failure


class ErrorCategory(Enum):
    """Error categories for classification"""
    NETWORK = "network"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    PROCESSING = "processing"
    EXTERNAL_API = "external_api"
    DATABASE = "database"
    MEMORY = "memory"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


@dataclass
class JarvisError:
    """Structured error type"""
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    details: Optional[str] = None
    user_message: Optional[str] = None
    timestamp: datetime = None
    traceback: Optional[str] = None
    context: Optional[dict] = None
    recoverable: bool = True

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

        if self.user_message is None:
            self.user_message = self._generate_user_message()

    def _generate_user_message(self) -> str:
        """Generate user-friendly error message"""
        if self.severity == ErrorSeverity.CRITICAL:
            return "⚠️ JARVIS is experiencing critical issues. Please try again later."
        elif self.severity == ErrorSeverity.HIGH:
            return "⚠️ I'm having trouble processing your request. Please try again."
        elif self.severity == ErrorSeverity.MEDIUM:
            return "⚠️ I encountered an issue but I'm working on it. Please wait a moment."
        else:
            return "⚠️ Minor issue detected, continuing..."

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "category": self.category.value,
            "severity": self.severity.value,
            "message": self.message,
            "details": self.details,
            "user_message": self.user_message,
            "timestamp": self.timestamp.isoformat(),
            "recoverable": self.recoverable,
            "context": self.context
        }


class Result(Generic[T, E]):
    """
    Result type for Railway-Oriented Programming
    Either Success(value) or Failure(error)
    """

    def __init__(self, value: Optional[T] = None, error: Optional[E] = None):
        self._value = value
        self._error = error
        self._is_success = error is None

    @staticmethod
    def success(value: T) -> 'Result[T, E]':
        """Create success result"""
        return Result(value=value)

    @staticmethod
    def failure(error: E) -> 'Result[T, E]':
        """Create failure result"""
        return Result(error=error)

    def is_success(self) -> bool:
        """Check if result is success"""
        return self._is_success

    def is_failure(self) -> bool:
        """Check if result is failure"""
        return not self._is_success

    def unwrap(self) -> T:
        """Get value or raise exception"""
        if self._is_success:
            return self._value
        raise ValueError(f"Called unwrap on failure: {self._error}")

    def unwrap_or(self, default: T) -> T:
        """Get value or default"""
        return self._value if self._is_success else default

    def unwrap_error(self) -> E:
        """Get error or raise exception"""
        if not self._is_success:
            return self._error
        raise ValueError("Called unwrap_error on success")

    def map(self, fn: Callable[[T], Any]) -> 'Result':
        """Map success value"""
        if self._is_success:
            try:
                return Result.success(fn(self._value))
            except Exception as e:
                return Result.failure(e)
        return self

    def map_error(self, fn: Callable[[E], Any]) -> 'Result':
        """Map error value"""
        if not self._is_success:
            return Result.failure(fn(self._error))
        return self

    def and_then(self, fn: Callable[[T], 'Result']) -> 'Result':
        """Chain operations (flatMap)"""
        if self._is_success:
            try:
                return fn(self._value)
            except Exception as e:
                return Result.failure(e)
        return self


class ErrorHandler:
    """
    PhD-Level Error Handler
    - Automatic error classification
    - Recovery strategies
    - Error aggregation
    - Telemetry
    """

    def __init__(self):
        self.error_history = []
        self.max_history = 1000

    def handle_exception(
        self,
        exception: Exception,
        context: Optional[dict] = None,
        user_facing: bool = True
    ) -> JarvisError:
        """
        Handle exception and convert to JarvisError
        """
        # Classify error
        category = self._classify_error(exception)
        severity = self._determine_severity(exception, category)

        # Create structured error
        error = JarvisError(
            category=category,
            severity=severity,
            message=str(exception),
            details=traceback.format_exc(),
            traceback=traceback.format_exc(),
            context=context,
            recoverable=self._is_recoverable(exception, category)
        )

        # Log error
        self._log_error(error)

        # Store in history
        self._store_error(error)

        return error

    def _classify_error(self, exception: Exception) -> ErrorCategory:
        """Classify error by type"""
        error_type = type(exception).__name__

        if 'Connection' in error_type or 'Network' in error_type:
            return ErrorCategory.NETWORK
        elif 'Auth' in error_type or 'Permission' in error_type:
            return ErrorCategory.AUTHENTICATION
        elif 'Validation' in error_type or 'ValueError' in error_type:
            return ErrorCategory.VALIDATION
        elif 'Timeout' in error_type:
            return ErrorCategory.TIMEOUT
        elif 'Memory' in error_type:
            return ErrorCategory.MEMORY
        elif 'API' in error_type or 'HTTP' in error_type:
            return ErrorCategory.EXTERNAL_API
        else:
            return ErrorCategory.UNKNOWN

    def _determine_severity(self, exception: Exception, category: ErrorCategory) -> ErrorSeverity:
        """Determine error severity"""
        # Critical errors
        if category == ErrorCategory.MEMORY:
            return ErrorSeverity.CRITICAL
        if isinstance(exception, (SystemError, MemoryError)):
            return ErrorSeverity.CRITICAL

        # High severity
        if category in [ErrorCategory.AUTHENTICATION, ErrorCategory.DATABASE]:
            return ErrorSeverity.HIGH

        # Medium severity
        if category in [ErrorCategory.NETWORK, ErrorCategory.EXTERNAL_API, ErrorCategory.TIMEOUT]:
            return ErrorSeverity.MEDIUM

        # Low severity
        return ErrorSeverity.LOW

    def _is_recoverable(self, exception: Exception, category: ErrorCategory) -> bool:
        """Check if error is recoverable"""
        # Non-recoverable errors
        if isinstance(exception, (SystemError, MemoryError)):
            return False

        if category == ErrorCategory.AUTHENTICATION:
            return False

        # Most errors are recoverable with retry
        return True

    def _log_error(self, error: JarvisError):
        """Log error with appropriate level"""
        log_message = f"[{error.category.value}] {error.message}"

        if error.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message, extra={"error": error.to_dict()})
        elif error.severity == ErrorSeverity.HIGH:
            logger.error(log_message, extra={"error": error.to_dict()})
        elif error.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message, extra={"error": error.to_dict()})
        else:
            logger.info(log_message, extra={"error": error.to_dict()})

    def _store_error(self, error: JarvisError):
        """Store error in history"""
        self.error_history.append(error)

        # Trim history if too large
        if len(self.error_history) > self.max_history:
            self.error_history = self.error_history[-self.max_history:]

    def get_error_stats(self) -> dict:
        """Get error statistics"""
        if not self.error_history:
            return {
                "total_errors": 0,
                "by_category": {},
                "by_severity": {},
                "recent_errors": []
            }

        # Count by category
        by_category = {}
        for error in self.error_history:
            cat = error.category.value
            by_category[cat] = by_category.get(cat, 0) + 1

        # Count by severity
        by_severity = {}
        for error in self.error_history:
            sev = error.severity.value
            by_severity[sev] = by_severity.get(sev, 0) + 1

        # Recent errors (last 10)
        recent = [e.to_dict() for e in self.error_history[-10:]]

        return {
            "total_errors": len(self.error_history),
            "by_category": by_category,
            "by_severity": by_severity,
            "recent_errors": recent
        }


# Global error handler instance
error_handler = ErrorHandler()


def safe_execute(fn: Callable, *args, **kwargs) -> Result:
    """
    Execute function safely and return Result
    """
    try:
        result = fn(*args, **kwargs)
        return Result.success(result)
    except Exception as e:
        error = error_handler.handle_exception(e, context={
            "function": fn.__name__,
            "args": str(args)[:100],
            "kwargs": str(kwargs)[:100]
        })
        return Result.failure(error)


async def safe_execute_async(fn: Callable, *args, **kwargs) -> Result:
    """
    Execute async function safely and return Result
    """
    try:
        result = await fn(*args, **kwargs)
        return Result.success(result)
    except Exception as e:
        error = error_handler.handle_exception(e, context={
            "function": fn.__name__,
            "args": str(args)[:100],
            "kwargs": str(kwargs)[:100]
        })
        return Result.failure(error)


# Test
if __name__ == "__main__":
    # Test error handling
    def failing_function():
        raise ValueError("Test error")

    result = safe_execute(failing_function)

    if result.is_failure():
        error = result.unwrap_error()
        print(f"Error: {error.message}")
        print(f"User message: {error.user_message}")
        print(f"Category: {error.category.value}")
        print(f"Severity: {error.severity.value}")

    # Test stats
    print("\nError Stats:")
    print(error_handler.get_error_stats())
