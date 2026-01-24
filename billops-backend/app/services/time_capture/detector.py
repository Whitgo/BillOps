"""
Idle detection module for time entry processing.

Detects idle periods based on activity signals and configurable thresholds.
"""
from datetime import datetime, timedelta, timezone
from typing import NamedTuple


class IdleSignal(NamedTuple):
    """Represents an idle period."""
    start_time: datetime
    end_time: datetime
    idle_minutes: int
    reason: str  # "no_activity", "inactivity_threshold", "manual_break"


class IdleDetector:
    """Detects idle periods in activity signals."""
    
    # Default idle threshold in minutes
    DEFAULT_IDLE_THRESHOLD = 5
    
    # Maximum idle period to merge with surrounding activities (in minutes)
    MAX_MERGE_IDLE = 10
    
    @staticmethod
    def detect_idle_periods(
        activity_signals: list[dict],
        idle_threshold_minutes: int = DEFAULT_IDLE_THRESHOLD,
    ) -> list[IdleSignal]:
        """
        Detect idle periods from activity signals.
        
        Args:
            activity_signals: List of activity dicts with 'timestamp' and 'type' keys
            idle_threshold_minutes: Minutes of inactivity to mark as idle
            
        Returns:
            List of detected idle periods
        """
        if not activity_signals or len(activity_signals) < 2:
            return []
        
        # Sort signals by timestamp
        sorted_signals = sorted(activity_signals, key=lambda x: x["timestamp"])
        idle_periods = []
        
        for i in range(len(sorted_signals) - 1):
            current = sorted_signals[i]
            next_signal = sorted_signals[i + 1]
            
            current_time = current["timestamp"]
            next_time = next_signal["timestamp"]
            
            # Ensure timestamps are timezone-aware
            if current_time.tzinfo is None:
                current_time = current_time.replace(tzinfo=timezone.utc)
            if next_time.tzinfo is None:
                next_time = next_time.replace(tzinfo=timezone.utc)
            
            gap = next_time - current_time
            gap_minutes = gap.total_seconds() / 60
            
            if gap_minutes >= idle_threshold_minutes:
                idle_periods.append(
                    IdleSignal(
                        start_time=current_time,
                        end_time=next_time,
                        idle_minutes=int(gap_minutes),
                        reason="inactivity_threshold",
                    )
                )
        
        return idle_periods
    
    @staticmethod
    def should_merge_with_idle(
        gap_minutes: int,
        max_merge_idle: int = MAX_MERGE_IDLE,
    ) -> bool:
        """
        Determine if an idle gap should be merged with surrounding activities.
        
        Args:
            gap_minutes: Length of idle gap in minutes
            max_merge_idle: Maximum idle period to merge
            
        Returns:
            True if gap should be merged, False if it should be a break
        """
        return gap_minutes <= max_merge_idle
    
    @staticmethod
    def filter_idle_periods(
        idle_periods: list[IdleSignal],
        max_merge_idle: int = MAX_MERGE_IDLE,
    ) -> tuple[list[IdleSignal], list[IdleSignal]]:
        """
        Separate idle periods into those that should be merged vs those that are breaks.
        
        Args:
            idle_periods: All detected idle periods
            max_merge_idle: Maximum idle to merge
            
        Returns:
            Tuple of (mergeable_idles, break_idles)
        """
        mergeable = []
        breaks = []
        
        for idle in idle_periods:
            if IdleDetector.should_merge_with_idle(idle.idle_minutes, max_merge_idle):
                mergeable.append(idle)
            else:
                breaks.append(idle)
        
        return mergeable, breaks
