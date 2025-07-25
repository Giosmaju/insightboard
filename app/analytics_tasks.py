import datetime
from datetime import date, timedelta
from app.models import User, Entry, Analytics
from sqlalchemy import func
from app import db

def week_summary_all_users():
    print("Running weekly summary task...")
    users = User.query.all()
    for user in users:
        summary = Analytics.week_summary(user.id)

        # Skip if user has no tasks this week
        if "note" in summary:
            continue

        analytic_entry = Analytics(
            user_id=user.id,
            week_start=date.today() - timedelta(days=date.today().weekday() + 7),  # previous Monday
            week_end=date.today() - timedelta(days=date.today().weekday() + 1),    # previous Sunday
            tasks_scheduled=summary["scheduled"],
            tasks_completed=summary["completed"],
            tasks_in_progress=summary["in_progress"],
            average_rating=float(summary["average_rating"]),
            average_task_duration=float(summary["average_task_duration"]),
            most_active_day = summary["most_active_day"],
            top_category=summary["top_category"]
        )

        db.session.add(analytic_entry)
        print(f"User ID {user.id} summary saved.")

    db.session.commit()
    
