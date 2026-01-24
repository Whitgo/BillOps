"""
Time-capture heuristics module.

Implements activity grouping, merging, and intelligent time entry creation.
"""
from datetime import datetime, timezone
from typing import NamedTuple

from app.services.time_capture.classifier import SourceClassifier, ActivityType
from app.services.time_capture.detector import IdleDetector


class SuggestedTimeEntry(NamedTuple):
    """Suggested time entry created from activity signals."""
    started_at: datetime
    ended_at: datetime
    activity_type: str
    confidence: float
    context_data: dict
    description: str | None
    should_verify: bool


class ActivityHeuristics:
    """Applies heuristics to group activities."""
    
    FOCUSED_WORK_WEIGHT = 0.9
    MEETING_WEIGHT = 0.85
    RESEARCH_WEIGHT = 0.75
    COMMUNICATION_WEIGHT = 0.7
    UNCERTAIN_THRESHOLD = 0.5
    
    @staticmethod
    def group_activities(
        signals: list[dict],
        idle_threshold_minutes: int = 5,
        max_merge_idle_minutes: int = 10,
    ) -> list[list[dict]]:
        """Group activity signals into coherent sessions."""
        if not signals:
            return []
        
        work_signals = [s for s in signals if SourceClassifier.is_work_related(s)]
        if not work_signals:
            return []
        
        idle_periods = IdleDetector.detect_idle_periods(work_signals, idle_threshold_minutes)
        _, breaks = IdleDetector.filter_idle_periods(idle_periods, max_merge_idle_minutes)
        
        groups = []
        current_group = []
        
        for signal in work_signals:
            in_break = False
            for break_idle in breaks:
                if break_idle.start_time <= signal["timestamp"] <= break_idle.end_time:
                    in_break = True
                    break
            
            if in_break and current_group:
                groups.append(current_group)
                current_group = []
            else:
                current_group.append(signal)
        
        if current_group:
            groups.append(current_group)
        
        return groups
    
    @staticmethod
    def calculate_confidence(signals: list[dict]) -> float:
        """Calculate confidence score for a group of signals."""
        if not signals:
            return 0.0
        
        activity_types = [SourceClassifier.classify_signal(s) for s in signals]
        type_counts = {}
        for at in activity_types:
            type_counts[at] = type_counts.get(at, 0) + 1
        
        if len(type_counts) == 1:
            consistency_score = 1.0
        else:
            max_count = max(type_counts.values())
            consistency_score = max_count / len(signals)
        
        dominant_type = max(type_counts.items(), key=lambda x: x[1])[0]
        type_multiplier = {
            ActivityType.FOCUSED_WORK: ActivityHeuristics.FOCUSED_WORK_WEIGHT,
            ActivityType.MEETING: ActivityHeuristics.MEETING_WEIGHT,
            ActivityType.RESEARCH: ActivityHeuristics.RESEARCH_WEIGHT,
            ActivityType.COMMUNICATION: ActivityHeuristics.COMMUNICATION_WEIGHT,
        }.get(dominant_type, ActivityHeuristics.UNCERTAIN_THRESHOLD)
        
        return consistency_score * type_multiplier
    
    @staticmethod
    def create_suggested_entry(
        signals: list[dict],
        activity_type: str | None = None,
    ) -> SuggestedTimeEntry | None:
        """Create a suggested time entry from a group of signals."""
        if not signals:
            return None
        
        sorted_signals = sorted(signals, key=lambda x: x["timestamp"])
        started_at = sorted_signals[0]["timestamp"]
        ended_at = sorted_signals[-1]["timestamp"]
        
        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=timezone.utc)
        if ended_at.tzinfo is None:
            ended_at = ended_at.replace(tzinfo=timezone.utc)
        
        confidence = ActivityHeuristics.calculate_confidence(signals)
        should_verify = confidence < ActivityHeuristics.UNCERTAIN_THRESHOLD
        
        context_data = SourceClassifier.get_context_data(signals)
        
        primary_activity = context_data.get("primary_activity")
        # Use detected primary activity type when available
        resolved_activity_type = primary_activity or activity_type or "work"
        apps = context_data.get("applications", [])
        description = f"{primary_activity}: {', '.join(apps[:3])}" if apps else primary_activity
        
        return SuggestedTimeEntry(
            started_at=started_at,
            ended_at=ended_at,
            activity_type=resolved_activity_type,
            confidence=confidence,
            context_data=context_data,
            description=description,
            should_verify=should_verify,
        )
    
    @staticmethod
    def generate_time_entries(
        signals: list[dict],
        idle_threshold_minutes: int = 5,
        max_merge_idle_minutes: int = 10,
    ) -> list[SuggestedTimeEntry]:
        """Generate suggested time entries from raw activity signals."""
        groups = ActivityHeuristics.group_activities(
            signals,
            idle_threshold_minutes,
            max_merge_idle_minutes,
        )
        
        entries = []
        for group in groups:
            if entry := ActivityHeuristics.create_suggested_entry(group):
                entries.append(entry)
        
        return entries
