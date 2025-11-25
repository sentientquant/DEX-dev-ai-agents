"""
Result type for consistent error handling across the trading system

Eliminates inconsistent error response shapes and ensures all error paths
have the required fields.

Usage:
    def risky_operation() -> Result[SuccessType]:
        try:
            data = do_something()
            return success(data)
        except Exception as e:
            return failure(error=str(e), error_type=type(e).__name__)

    # Caller
    result = risky_operation()
    if result.is_success():
        data = result.value  # Type: SuccessType
        # Use data safely
    else:
        print(f"Error: {result.error}")  # Always available in Failure
"""

from typing import TypeVar, Generic, Union, Optional, Dict, Any
from dataclasses import dataclass, field

T = TypeVar('T')


@dataclass
class Success(Generic[T]):
    """
    Successful operation with typed value

    All Success results have a .value property containing the result
    """
    value: T

    def is_success(self) -> bool:
        """Check if this is a success result"""
        return True

    def is_failure(self) -> bool:
        """Check if this is a failure result"""
        return False

    def unwrap(self) -> T:
        """Get the value (safe because this is Success)"""
        return self.value

    def unwrap_or(self, default: T) -> T:
        """Get value or default (returns value for Success)"""
        return self.value


@dataclass
class Failure:
    """
    Failed operation with error details

    All Failure results have .error and .error_type properties
    Optional .details dict for additional context
    """
    error: str
    error_type: str = 'unknown'
    details: Optional[Dict[str, Any]] = field(default_factory=dict)

    def is_success(self) -> bool:
        """Check if this is a success result"""
        return False

    def is_failure(self) -> bool:
        """Check if this is a failure result"""
        return True

    def unwrap(self) -> None:
        """Cannot unwrap a Failure - raises exception"""
        raise ValueError(f"Cannot unwrap Failure: {self.error}")

    def unwrap_or(self, default: T) -> T:
        """Get value or default (returns default for Failure)"""
        return default


# Type alias for readability
Result = Union[Success[T], Failure]


# Helper functions for cleaner code
def success(value: T) -> Success[T]:
    """
    Create a success result

    Usage:
        return success(SignalVerificationResult(...))
    """
    return Success(value)


def failure(error: str, error_type: str = 'unknown', **details: Any) -> Failure:
    """
    Create a failure result

    Usage:
        return failure(
            error="Verification failed",
            error_type="VerificationError",
            provider="anthropic",
            status_code=500
        )
    """
    return Failure(
        error=error,
        error_type=error_type,
        details=details if details else None
    )
