"""
Source and activity classification module.
"""
from enum import Enum


class ActivitySource(str, Enum):
    KEYBOARD = "keyboard"
    MOUSE = "mouse"
    WINDOW = "window"
    APPLICATION = "application"
    UNKNOWN = "unknown"


class ActivityType(str, Enum):
    FOCUSED_WORK = "focused_work"
    RESEARCH = "research"
    MEETING = "meeting"
    COMMUNICATION = "communication"
    ADMIN = "admin"
    PERSONAL = "personal"
    IDLE = "idle"


class SourceClassifier:
    """Classifies activity signals by source and type."""
    
    WORK_APPLICATIONS = {
        "vscode": ActivityType.FOCUSED_WORK,
        "jetbrains": ActivityType.FOCUSED_WORK,
        "sublime": ActivityType.FOCUSED_WORK,
        "chrome": ActivityType.RESEARCH,
        "firefox": ActivityType.RESEARCH,
        "zoom": ActivityType.MEETING,
        "teams": ActivityType.MEETING,
        "slack": ActivityType.COMMUNICATION,
    }
    
    WORK_DOMAINS = {
        "github.com",
        "stackoverflow.com",
        "trello.com",
        "slack.com",
    }
    
    @staticmethod
    def classify_signal(signal: dict) -> ActivityType:
        app = signal.get("app", "").lower()
        if app in SourceClassifier.WORK_APPLICATIONS:
            return SourceClassifier.WORK_APPLICATIONS[app]
        
        domain = signal.get("domain", "").lower()
        for work_domain in SourceClassifier.WORK_DOMAINS:
            if work_domain in domain:
                return ActivityType.RESEARCH
        
        signal_type = signal.get("type", "").lower()
        if "keyboard" in signal_type:
            return ActivityType.FOCUSED_WORK
        
        return ActivityType.PERSONAL
    
    @staticmethod
    def classify_source(signal: dict) -> ActivitySource:
        source = signal.get("source_type", "").lower()
        if "keyboard" in source:
            return ActivitySource.KEYBOARD
        elif "mouse" in source:
            return ActivitySource.MOUSE
        elif "window" in source:
            return ActivitySource.WINDOW
        return ActivitySource.UNKNOWN
    
    @staticmethod
    def is_work_related(signal: dict) -> bool:
        activity_type = SourceClassifier.classify_signal(signal)
        return activity_type != ActivityType.PERSONAL
    
    @staticmethod
    def get_context_data(signals: list[dict]) -> dict:
        apps = set()
        domains = set()
        activity_types = {}
        
        for signal in signals:
            if app := signal.get("app"):
                apps.add(app.lower())
            if domain := signal.get("domain"):
                domains.add(domain.lower())
            activity_type = SourceClassifier.classify_signal(signal)
            activity_types[activity_type.value] = activity_types.get(activity_type.value, 0) + 1
        
        return {
            "applications": sorted(list(apps)),
            "domains": sorted(list(domains)),
            "activity_distribution": activity_types,
            "primary_activity": max(activity_types.items(), key=lambda x: x[1])[0] if activity_types else None,
        }
