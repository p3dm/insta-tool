from datetime import datetime, timezone as utc_timezone

from apscheduler.schedulers.background import BackgroundScheduler


def get_system_timezone():
    """Read the timezone from the computer running the app, not the build PC."""
    return datetime.now().astimezone().tzinfo or utc_timezone.utc


scheduler = BackgroundScheduler(timezone=get_system_timezone())
