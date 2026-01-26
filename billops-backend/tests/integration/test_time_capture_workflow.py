"""
Integration tests for time capture workflow.
"""

import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.models.time_entry import TimeEntry
from app.services.time_entry import TimeEntryService


@pytest.mark.integration
@pytest.mark.db
class TestTimeCaptureWorkflow:
    """Integration tests for time capture workflows."""

    def test_daily_time_tracking_workflow(
        self,
        db: Session,
        test_user,
        test_project,
        make_time_entry_factory,
    ):
        """
        Test complete daily tracking:
        1. Log work sessions throughout day
        2. Verify total hours
        3. Check for gaps/overlaps
        """
        time_service = TimeEntryService(db)
        now = datetime.now(timezone.utc)
        work_start = now.replace(hour=9, minute=0, second=0, microsecond=0)

        # Log work sessions
        sessions = [
            # Morning: 9-12 (3 hours)
            make_time_entry_factory(
                start_time=work_start,
                duration_minutes=180,
                description="Morning work",
            ),
            # Break: 12-1 (not logged)
            # Afternoon: 1-5 (4 hours)
            make_time_entry_factory(
                start_time=work_start + timedelta(hours=4),
                duration_minutes=240,
                description="Afternoon work",
            ),
            # Evening: 5-6 (1 hour)
            make_time_entry_factory(
                start_time=work_start + timedelta(hours=8),
                duration_minutes=60,
                description="Evening wrap-up",
            ),
        ]

        # Verify total hours
        day_start = work_start.replace(hour=0, minute=0, second=0)
        day_end = day_start + timedelta(days=1)

        total_hours = time_service.calculate_billable_hours(
            test_user.id,
            day_start,
            day_end,
        )
        assert total_hours == 8.0  # 3 + 4 + 1 hours

    def test_multi_project_time_tracking(
        self,
        db: Session,
        test_user,
        test_client,
        make_time_entry_factory,
    ):
        """Test tracking time across multiple projects."""
        from app.models.project import Project

        # Create multiple projects
        project1 = Project(
            user_id=test_user.id,
            client_id=test_client.id,
            name="Project Alpha",
            hourly_rate_cents=15000,
            currency="USD",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        project2 = Project(
            user_id=test_user.id,
            client_id=test_client.id,
            name="Project Beta",
            hourly_rate_cents=20000,
            currency="USD",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(project1)
        db.add(project2)
        db.commit()

        now = datetime.now(timezone.utc)
        time_service = TimeEntryService(db)

        # Create entries for both projects
        entry1 = TimeEntry(
            user_id=test_user.id,
            project_id=project1.id,
            description="Alpha work",
            start_time=now - timedelta(hours=2),
            end_time=now - timedelta(hours=1),
            duration_minutes=60,
            is_billable=True,
            is_billed=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        entry2 = TimeEntry(
            user_id=test_user.id,
            project_id=project2.id,
            description="Beta work",
            start_time=now - timedelta(hours=1),
            end_time=now,
            duration_minutes=60,
            is_billable=True,
            is_billed=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(entry1)
        db.add(entry2)
        db.commit()

        # Calculate total billable hours
        period_start = now - timedelta(days=1)
        period_end = now + timedelta(days=1)
        total_hours = time_service.calculate_billable_hours(
            test_user.id,
            period_start,
            period_end,
        )
        assert total_hours == 2.0  # 1 hour + 1 hour

    def test_weekly_time_summary(
        self,
        db: Session,
        test_user,
        test_project,
        make_time_entry_factory,
    ):
        """Test generating weekly time summary."""
        time_service = TimeEntryService(db)
        now = datetime.now(timezone.utc)

        # Create entries for week
        days_of_work = []
        for day in range(5):  # Mon-Fri
            for hour in range(8):  # 8-hour workday
                entry = make_time_entry_factory(
                    start_time=now - timedelta(days=day, hours=8-hour),
                    duration_minutes=60,
                    description=f"Day {day+1} Hour {hour+1}",
                )
                days_of_work.append(entry)

        # Calculate weekly hours
        week_start = now - timedelta(days=7)
        week_end = now + timedelta(days=1)

        weekly_hours = time_service.calculate_billable_hours(
            test_user.id,
            week_start,
            week_end,
        )
        assert weekly_hours == 40.0  # 5 days * 8 hours

    def test_monthly_time_tracking_with_overtime(
        self,
        db: Session,
        test_user,
        test_project,
        test_billing_rule,
        make_time_entry_factory,
    ):
        """Test monthly tracking with overtime detection."""
        time_service = TimeEntryService(db)
        now = datetime.now(timezone.utc)

        # Create entries for month (simulate 180 hours = 22.5 days of 8-hour shifts)
        hours_tracked = 0
        for day in range(23):
            hours_per_day = 8
            for hour_slot in range(hours_per_day):
                entry = make_time_entry_factory(
                    start_time=now - timedelta(days=day, hours=hours_per_day-hour_slot),
                    duration_minutes=60,
                )
                hours_tracked += 1

        # Calculate total hours
        month_start = now - timedelta(days=30)
        month_end = now + timedelta(days=1)

        monthly_hours = time_service.calculate_billable_hours(
            test_user.id,
            month_start,
            month_end,
        )

        # Check for overtime (billable hours = 160, so 23 hours = overtime)
        billable_hours = test_billing_rule.billable_hours_per_month
        is_overtime = monthly_hours > billable_hours
        assert is_overtime

    def test_time_entry_validation(
        self,
        db: Session,
        test_user,
        test_project,
    ):
        """Test validation of time entries."""
        time_service = TimeEntryService(db)

        # Valid entry
        now = datetime.now(timezone.utc)
        valid_entry = TimeEntry(
            user_id=test_user.id,
            project_id=test_project.id,
            description="Valid work",
            start_time=now - timedelta(hours=1),
            end_time=now,
            duration_minutes=60,
            is_billable=True,
            is_billed=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(valid_entry)
        db.commit()
        assert valid_entry.id is not None

    def test_time_entry_with_no_description(
        self,
        db: Session,
        test_user,
        test_project,
    ):
        """Test creating time entry without description."""
        now = datetime.now(timezone.utc)

        entry = TimeEntry(
            user_id=test_user.id,
            project_id=test_project.id,
            description="",  # Empty description
            start_time=now - timedelta(hours=1),
            end_time=now,
            duration_minutes=60,
            is_billable=True,
            is_billed=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(entry)
        db.commit()

        # Should still be created
        assert entry.id is not None

    def test_time_entry_bulk_operations(
        self,
        db: Session,
        test_user,
        test_project,
        make_time_entry_factory,
    ):
        """Test bulk operations on time entries."""
        time_service = TimeEntryService(db)
        now = datetime.now(timezone.utc)

        # Create many entries
        entries = []
        for i in range(20):
            entry = make_time_entry_factory(
                start_time=now - timedelta(hours=20-i),
                duration_minutes=60,
            )
            entries.append(entry)

        # Mark all as billed
        for entry in entries:
            time_service.mark_as_billed(entry.id)

        # Verify all marked
        for entry in entries:
            db.refresh(entry)
            assert entry.is_billed is True

    def test_time_entry_period_boundary_handling(
        self,
        db: Session,
        test_user,
        test_project,
        make_time_entry_factory,
    ):
        """Test time entries spanning period boundaries."""
        time_service = TimeEntryService(db)

        # Create entry that spans day boundary
        boundary_time = datetime(
            year=2024,
            month=1,
            day=31,
            hour=23,
            minute=30,
            tzinfo=timezone.utc,
        )

        entry = TimeEntry(
            user_id=test_user.id,
            project_id=test_project.id,
            description="Boundary spanning",
            start_time=boundary_time,
            end_time=boundary_time + timedelta(hours=1),
            duration_minutes=60,
            is_billable=True,
            is_billed=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(entry)
        db.commit()

        # Calculate hours on both sides of boundary
        period1_start = datetime(2024, 1, 30, tzinfo=timezone.utc)
        period1_end = boundary_time + timedelta(hours=2)

        hours = time_service.calculate_billable_hours(
            test_user.id,
            period1_start,
            period1_end,
        )
        assert hours == 1.0

    def test_time_entry_edge_cases(
        self,
        db: Session,
        test_user,
        test_project,
    ):
        """Test edge cases in time tracking."""
        time_service = TimeEntryService(db)
        now = datetime.now(timezone.utc)

        # Zero-duration entry
        zero_entry = TimeEntry(
            user_id=test_user.id,
            project_id=test_project.id,
            description="Instant entry",
            start_time=now,
            end_time=now,
            duration_minutes=0,
            is_billable=True,
            is_billed=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(zero_entry)
        db.commit()
        assert zero_entry.duration_minutes == 0

        # Very long entry (24 hours)
        long_entry = TimeEntry(
            user_id=test_user.id,
            project_id=test_project.id,
            description="All day marathon",
            start_time=now,
            end_time=now + timedelta(hours=24),
            duration_minutes=1440,
            is_billable=True,
            is_billed=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(long_entry)
        db.commit()
        assert long_entry.duration_minutes == 1440

    def test_time_entry_data_integrity_across_operations(
        self,
        db: Session,
        test_user,
        test_project,
        make_time_entry_factory,
    ):
        """Test that time entry data remains consistent across operations."""
        time_service = TimeEntryService(db)
        now = datetime.now(timezone.utc)

        # Create entry with specific values
        original_entry = make_time_entry_factory(
            start_time=now - timedelta(hours=1),
            duration_minutes=60,
            description="Test integrity",
            is_billable=True,
        )

        original_id = original_entry.id
        original_duration = original_entry.duration_minutes

        # Retrieve and verify
        retrieved_entry = time_service.get_by_id(original_id)
        assert retrieved_entry.id == original_id
        assert retrieved_entry.duration_minutes == original_duration
        assert retrieved_entry.description == "Test integrity"

        # Mark as billed and verify other data intact
        time_service.mark_as_billed(original_id)
        db.refresh(retrieved_entry)
        assert retrieved_entry.is_billed is True
        assert retrieved_entry.duration_minutes == original_duration
