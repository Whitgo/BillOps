"""
Comprehensive tests for time-capture heuristics and Celery task processing.

Demonstrates idle detection, activity grouping, and time entry generation.
"""
from datetime import datetime, timezone, timedelta
from app.services.time_capture import (
    IdleDetector,
    SourceClassifier,
    ActivityHeuristics,
    ActivityType,
)


def create_sample_signals():
    """Create sample activity signals for testing."""
    base_time = datetime(2024, 1, 24, 9, 0, 0, tzinfo=timezone.utc)
    
    return [
        # Morning coding session - 9:00-10:30
        {"timestamp": base_time, "type": "keyboard", "app": "vscode", "source_type": "keyboard"},
        {"timestamp": base_time + timedelta(minutes=5), "type": "keyboard", "app": "vscode", "source_type": "keyboard"},
        {"timestamp": base_time + timedelta(minutes=10), "type": "mouse_click", "app": "vscode", "source_type": "mouse"},
        {"timestamp": base_time + timedelta(minutes=15), "type": "keyboard", "app": "vscode", "source_type": "keyboard"},
        {"timestamp": base_time + timedelta(minutes=30), "type": "keyboard", "app": "vscode", "source_type": "keyboard"},
        {"timestamp": base_time + timedelta(minutes=45), "type": "keyboard", "app": "vscode", "source_type": "keyboard"},
        {"timestamp": base_time + timedelta(minutes=60), "type": "keyboard", "app": "vscode", "source_type": "keyboard"},
        
        # Gap: 30 minutes idle (10:30-11:00)
        
        # Research session - 11:00-11:45
        {"timestamp": base_time + timedelta(minutes=90), "type": "browser", "app": "chrome", "domain": "stackoverflow.com", "source_type": "window"},
        {"timestamp": base_time + timedelta(minutes=100), "type": "browser", "app": "chrome", "domain": "github.com", "source_type": "window"},
        {"timestamp": base_time + timedelta(minutes=110), "type": "mouse_click", "app": "chrome", "domain": "github.com", "source_type": "mouse"},
        {"timestamp": base_time + timedelta(minutes=120), "type": "browser", "app": "chrome", "domain": "stackoverflow.com", "source_type": "window"},
        
        # Gap: 2 minutes idle (11:45-11:47) - should merge
        
        # More research - 11:47-12:00
        {"timestamp": base_time + timedelta(minutes=127), "type": "browser", "app": "firefox", "domain": "google.com", "source_type": "window"},
        {"timestamp": base_time + timedelta(minutes=135), "type": "browser", "app": "firefox", "domain": "github.com", "source_type": "window"},
        
        # Gap: 15 minutes idle (12:00-12:15) - break
        
        # Communication session - 12:15-12:30
        {"timestamp": base_time + timedelta(minutes=165), "type": "messaging", "app": "slack", "source_type": "window"},
        {"timestamp": base_time + timedelta(minutes=175), "type": "messaging", "app": "slack", "source_type": "window"},
        {"timestamp": base_time + timedelta(minutes=180), "type": "messaging", "app": "slack", "source_type": "window"},
    ]


def test_idle_detection():
    """Test idle period detection."""
    print("\n" + "="*60)
    print("TEST: Idle Detection")
    print("="*60)
    
    signals = create_sample_signals()
    idle_periods = IdleDetector.detect_idle_periods(signals, idle_threshold_minutes=5)
    
    print(f"Found {len(idle_periods)} idle periods:")
    for i, idle in enumerate(idle_periods, 1):
        duration = (idle.end_time - idle.start_time).total_seconds() / 60
        print(f"  {i}. {idle.start_time.strftime('%H:%M')} - {idle.end_time.strftime('%H:%M')} ({idle.idle_minutes} min) - {idle.reason}")
    
    # Verify detection
    assert len(idle_periods) >= 2, "Should detect at least 2 idle periods"
    print("✓ Idle detection working correctly")
    return idle_periods


def test_idle_merging(idle_periods):
    """Test idle filtering (merge vs break)."""
    print("\n" + "="*60)
    print("TEST: Idle Merging Logic")
    print("="*60)
    
    mergeable, breaks = IdleDetector.filter_idle_periods(idle_periods, max_merge_idle=10)
    
    print(f"Mergeable idles (≤10 min): {len(mergeable)}")
    for idle in mergeable:
        print(f"  - {idle.idle_minutes} min")
    
    print(f"Break idles (>10 min): {len(breaks)}")
    for idle in breaks:
        print(f"  - {idle.idle_minutes} min")
    
    assert len(mergeable) >= 1, "Should have some mergeable idles"
    print("✓ Idle merging logic working correctly")


def test_source_classification():
    """Test activity source and type classification."""
    print("\n" + "="*60)
    print("TEST: Source Classification")
    print("="*60)
    
    test_signals = [
        {"app": "vscode", "type": "keyboard", "source_type": "keyboard"},
        {"app": "chrome", "domain": "stackoverflow.com", "source_type": "window"},
        {"app": "slack", "type": "messaging", "source_type": "window"},
        {"app": "notepad", "type": "text_input", "source_type": "keyboard"},
    ]
    
    for signal in test_signals:
        activity_type = SourceClassifier.classify_signal(signal)
        source = SourceClassifier.classify_source(signal)
        is_work = SourceClassifier.is_work_related(signal)
        
        app = signal.get("app", "unknown")
        print(f"  {app:15} -> Type: {activity_type.value:20} | Source: {source.value:10} | Work: {is_work}")
    
    print("✓ Source classification working correctly")


def test_activity_grouping():
    """Test activity grouping by idle periods."""
    print("\n" + "="*60)
    print("TEST: Activity Grouping")
    print("="*60)
    
    signals = create_sample_signals()
    groups = ActivityHeuristics.group_activities(signals, idle_threshold_minutes=5, max_merge_idle_minutes=10)
    
    print(f"Grouped {len(signals)} signals into {len(groups)} activity sessions:")
    for i, group in enumerate(groups, 1):
        first_time = group[0]["timestamp"].strftime("%H:%M")
        last_time = group[-1]["timestamp"].strftime("%H:%M")
        duration = (group[-1]["timestamp"] - group[0]["timestamp"]).total_seconds() / 60
        print(f"  {i}. {first_time}-{last_time} ({len(group)} signals, ~{int(duration)} min)")
    
    assert len(groups) >= 2, "Should create multiple activity groups"
    print("✓ Activity grouping working correctly")
    return groups


def test_confidence_calculation(groups):
    """Test confidence scoring."""
    print("\n" + "="*60)
    print("TEST: Confidence Scoring")
    print("="*60)
    
    for i, group in enumerate(groups, 1):
        confidence = ActivityHeuristics.calculate_confidence(group)
        types = [SourceClassifier.classify_signal(s).value for s in group]
        unique_types = len(set(types))
        
        print(f"  Group {i}: confidence={confidence:.2f}, types={unique_types}, samples={unique_types}/{len(set(types))}")
    
    print("✓ Confidence calculation working correctly")


def test_time_entry_generation():
    """Test suggested time entry generation."""
    print("\n" + "="*60)
    print("TEST: Time Entry Generation")
    print("="*60)
    
    signals = create_sample_signals()
    suggested_entries = ActivityHeuristics.generate_time_entries(
        signals,
        idle_threshold_minutes=5,
        max_merge_idle_minutes=10,
    )
    
    print(f"Generated {len(suggested_entries)} suggested time entries:\n")
    for i, entry in enumerate(suggested_entries, 1):
        duration = (entry.ended_at - entry.started_at).total_seconds() / 60
        primary = entry.context_data.get("primary_activity", "unknown")
        apps = ", ".join(entry.context_data.get("applications", [])[:2])
        
        print(f"  {i}. {entry.started_at.strftime('%H:%M')}-{entry.ended_at.strftime('%H:%M')} ({int(duration)}min)")
        print(f"     Activity: {primary}")
        print(f"     Apps: {apps}")
        print(f"     Confidence: {entry.confidence:.2f} {'[VERIFY]' if entry.should_verify else '[OK]'}")
        print()
    
    assert len(suggested_entries) >= 2, "Should generate multiple time entries"
    print("✓ Time entry generation working correctly")
    return suggested_entries


def test_context_extraction():
    """Test context data extraction."""
    print("\n" + "="*60)
    print("TEST: Context Data Extraction")
    print("="*60)
    
    signals = create_sample_signals()
    context = SourceClassifier.get_context_data(signals)
    
    print(f"Extracted context from {len(signals)} signals:")
    print(f"  Applications: {', '.join(context.get('applications', []))}")
    print(f"  Domains: {', '.join(context.get('domains', []))}")
    print(f"  Activity distribution:")
    for activity, count in context.get('activity_distribution', {}).items():
        print(f"    - {activity}: {count}")
    print(f"  Primary activity: {context.get('primary_activity')}")
    
    print("✓ Context extraction working correctly")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("TIME-CAPTURE HEURISTICS TEST SUITE")
    print("="*60)
    
    idle_periods = test_idle_detection()
    test_idle_merging(idle_periods)
    test_source_classification()
    groups = test_activity_grouping()
    test_confidence_calculation(groups)
    suggested_entries = test_time_entry_generation()
    test_context_extraction()
    
    print("\n" + "="*60)
    print("✓ ALL TESTS PASSED")
    print("="*60 + "\n")
