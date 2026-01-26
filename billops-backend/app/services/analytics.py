"""
Analytics and instrumentation for BillOps.

Provides event tracking, metrics collection, and logging for business operations.
"""

import logging
import json
from datetime import datetime, timezone
from typing import Any, Optional, Dict
from enum import Enum
from functools import wraps
import time

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Analytics event types."""

    # User events
    USER_REGISTERED = "user.registered"
    USER_LOGGED_IN = "user.logged_in"
    USER_UPDATED = "user.updated"

    # Client events
    CLIENT_CREATED = "client.created"
    CLIENT_UPDATED = "client.updated"
    CLIENT_DELETED = "client.deleted"

    # Project events
    PROJECT_CREATED = "project.created"
    PROJECT_UPDATED = "project.updated"
    PROJECT_CLOSED = "project.closed"

    # Time entry events
    TIME_ENTRY_CREATED = "time_entry.created"
    TIME_ENTRY_UPDATED = "time_entry.updated"
    TIME_ENTRY_DELETED = "time_entry.deleted"
    TIME_ENTRY_BILLED = "time_entry.billed"

    # Invoice events
    INVOICE_CREATED = "invoice.created"
    INVOICE_SENT = "invoice.sent"
    INVOICE_PAID = "invoice.paid"
    INVOICE_OVERDUE = "invoice.overdue"
    INVOICE_CANCELLED = "invoice.cancelled"

    # Payment events
    PAYMENT_RECEIVED = "payment.received"
    PAYMENT_FAILED = "payment.failed"
    PAYMENT_REFUNDED = "payment.refunded"

    # Billing events
    BILLING_RULE_CREATED = "billing_rule.created"
    BILLING_RULE_UPDATED = "billing_rule.updated"
    OVERTIME_DETECTED = "overtime.detected"

    # Integration events
    INTEGRATION_CONNECTED = "integration.connected"
    INTEGRATION_SYNCED = "integration.synced"
    INTEGRATION_SYNC_FAILED = "integration.sync_failed"
    INTEGRATION_DISCONNECTED = "integration.disconnected"

    # Task events
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"

    # API events
    API_CALL = "api.call"
    API_ERROR = "api.error"
    API_SLOW = "api.slow"

    # System events
    SYSTEM_ERROR = "system.error"
    SYSTEM_WARNING = "system.warning"


class AnalyticsEvent:
    """Represents an analytics event."""

    def __init__(
        self,
        event_type: EventType,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Create analytics event.

        Args:
            event_type: Type of event
            user_id: User performing action
            resource_type: Type of resource (invoice, client, etc.)
            resource_id: ID of resource
            metadata: Additional event data
        """
        self.event_type = event_type
        self.user_id = user_id
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.metadata = metadata or {}
        self.timestamp = datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        """Convert event to dictionary."""
        return {
            "event_type": self.event_type.value,
            "user_id": self.user_id,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }

    def __str__(self) -> str:
        """String representation."""
        return json.dumps(self.to_dict(), indent=2)


class Analytics:
    """Central analytics and instrumentation service."""

    def __init__(self):
        """Initialize analytics service."""
        self.logger = logging.getLogger(__name__)

    def track_event(self, event: AnalyticsEvent) -> None:
        """
        Track an analytics event.

        Args:
            event: Event to track
        """
        # Log event
        self.logger.info(f"EVENT: {event.event_type.value} - {event.to_dict()}")

        # Additional processing could go here:
        # - Send to analytics service (Mixpanel, Segment, etc.)
        # - Store in database
        # - Update metrics

    def track_user_action(
        self,
        event_type: EventType,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        **metadata,
    ) -> None:
        """
        Track a user action.

        Args:
            event_type: Type of event
            user_id: User ID
            resource_type: Type of resource
            resource_id: Resource ID
            **metadata: Additional metadata
        """
        event = AnalyticsEvent(
            event_type=event_type,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata=metadata,
        )
        self.track_event(event)

    def track_invoice_event(
        self,
        event_type: EventType,
        invoice_id: str,
        user_id: Optional[str] = None,
        **metadata,
    ) -> None:
        """Track invoice-related event."""
        self.track_user_action(
            event_type=event_type,
            user_id=user_id,
            resource_type="invoice",
            resource_id=invoice_id,
            **metadata,
        )

    def track_time_entry_event(
        self,
        event_type: EventType,
        time_entry_id: str,
        user_id: Optional[str] = None,
        **metadata,
    ) -> None:
        """Track time entry event."""
        self.track_user_action(
            event_type=event_type,
            user_id=user_id,
            resource_type="time_entry",
            resource_id=time_entry_id,
            **metadata,
        )

    def track_client_event(
        self,
        event_type: EventType,
        client_id: str,
        user_id: Optional[str] = None,
        **metadata,
    ) -> None:
        """Track client event."""
        self.track_user_action(
            event_type=event_type,
            user_id=user_id,
            resource_type="client",
            resource_id=client_id,
            **metadata,
        )

    def track_project_event(
        self,
        event_type: EventType,
        project_id: str,
        user_id: Optional[str] = None,
        **metadata,
    ) -> None:
        """Track project event."""
        self.track_user_action(
            event_type=event_type,
            user_id=user_id,
            resource_type="project",
            resource_id=project_id,
            **metadata,
        )

    def track_integration_event(
        self,
        event_type: EventType,
        integration_type: str,
        user_id: Optional[str] = None,
        **metadata,
    ) -> None:
        """Track integration event."""
        self.track_user_action(
            event_type=event_type,
            user_id=user_id,
            resource_type=f"integration_{integration_type}",
            **metadata,
        )

    def track_api_call(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: float,
        user_id: Optional[str] = None,
    ) -> None:
        """Track API call."""
        metadata = {
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "response_time_ms": response_time_ms,
        }

        event_type = EventType.API_ERROR if status_code >= 400 else EventType.API_CALL

        # Track as slow if > 1 second
        if response_time_ms > 1000:
            event_type = EventType.API_SLOW

        self.track_user_action(
            event_type=event_type,
            user_id=user_id,
            **metadata,
        )

    def track_error(
        self,
        error_type: str,
        error_message: str,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Track system error."""
        metadata = {
            "error_type": error_type,
            "error_message": error_message,
            "context": context or {},
        }
        self.track_user_action(
            event_type=EventType.SYSTEM_ERROR,
            user_id=user_id,
            **metadata,
        )


# Global analytics instance
_analytics: Optional[Analytics] = None


def get_analytics() -> Analytics:
    """Get or create analytics instance."""
    global _analytics
    if _analytics is None:
        _analytics = Analytics()
    return _analytics


# Decorator for tracking function execution
def track_execution(
    event_type: EventType,
    resource_type: Optional[str] = None,
):
    """
    Decorator to track function execution with timing.

    Args:
        event_type: Event type to track
        resource_type: Type of resource being operated on
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed_ms = (time.time() - start_time) * 1000

                # Extract IDs from function arguments if available
                user_id = kwargs.get("user_id")
                resource_id = kwargs.get("resource_id") or kwargs.get("id")

                analytics = get_analytics()
                analytics.track_user_action(
                    event_type=event_type,
                    user_id=user_id,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    function=func.__name__,
                    execution_time_ms=elapsed_ms,
                )
                return result
            except Exception as e:
                elapsed_ms = (time.time() - start_time) * 1000
                analytics = get_analytics()
                analytics.track_error(
                    error_type=type(e).__name__,
                    error_message=str(e),
                    context={"function": func.__name__, "execution_time_ms": elapsed_ms},
                )
                raise

        return wrapper

    return decorator


# Metrics collection
class Metrics:
    """Metrics collection and reporting."""

    def __init__(self):
        """Initialize metrics."""
        self.counters: Dict[str, int] = {}
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, list] = {}

    def increment_counter(self, name: str, value: int = 1) -> None:
        """Increment counter metric."""
        if name not in self.counters:
            self.counters[name] = 0
        self.counters[name] += value

    def set_gauge(self, name: str, value: float) -> None:
        """Set gauge metric."""
        self.gauges[name] = value

    def record_histogram(self, name: str, value: float) -> None:
        """Record histogram value."""
        if name not in self.histograms:
            self.histograms[name] = []
        self.histograms[name].append(value)

    def get_summary(self) -> dict:
        """Get metrics summary."""
        histogram_stats = {}
        for name, values in self.histograms.items():
            if values:
                histogram_stats[name] = {
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                    "count": len(values),
                }

        return {
            "counters": self.counters,
            "gauges": self.gauges,
            "histograms": histogram_stats,
        }


_metrics: Optional[Metrics] = None


def get_metrics() -> Metrics:
    """Get or create metrics instance."""
    global _metrics
    if _metrics is None:
        _metrics = Metrics()
    return _metrics
