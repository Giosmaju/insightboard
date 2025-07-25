from apscheduler.schedulers.background import BackgroundScheduler
from app.analytics_tasks import week_summary_all_users
import atexit

def start_scheduler():
    scheduler = BackgroundScheduler(timezone="UTC")
    
    # Schedule your weekly task: every Monday at 00:00
    scheduler.add_job(
        func=week_summary_all_users,
        trigger='cron',
        day_of_week='mon',
        hour=0,
        minute=0,
        id='weekly_summary_task',
        replace_existing=True
    )

    scheduler.start()

    # Ensure the scheduler shuts down cleanly when the app exits
    atexit.register(lambda: scheduler.shutdown())
