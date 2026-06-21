from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.domain import DiscoveryRun

def check_data_freshness(db: Session, threshold_hours: int = 24) -> dict:
    """
    Checks the last successful job discovery run to assess market intelligence freshness.
    Returns recommendations and status indicators.
    """
    latest_run = db.query(DiscoveryRun).filter(
        DiscoveryRun.status == "Success"
    ).order_by(DiscoveryRun.completed_at.desc()).first()

    if not latest_run:
        return {
            "refresh_recommended": True,
            "last_run": None,
            "last_source": "None",
            "last_imported_count": 0,
            "status_label": "No Data",
            "status_color": "rose",
            "age_text": "Never refreshed"
        }

    time_elapsed = datetime.utcnow() - latest_run.completed_at
    refresh_recommended = time_elapsed > timedelta(hours=threshold_hours)
    
    # Format a human-friendly age string
    hours_elapsed = int(time_elapsed.total_seconds() / 3600)
    if hours_elapsed == 0:
        minutes_elapsed = int(time_elapsed.total_seconds() / 60)
        age_text = f"{minutes_elapsed} minutes ago"
    elif hours_elapsed < 24:
        age_text = f"{hours_elapsed} hours ago"
    else:
        days_elapsed = hours_elapsed // 24
        age_text = f"{days_elapsed} days ago"

    return {
        "refresh_recommended": refresh_recommended,
        "last_run": latest_run.completed_at,
        "last_source": latest_run.source,
        "last_imported_count": latest_run.records_imported,
        "status_label": "Stale" if refresh_recommended else "Fresh",
        "status_color": "amber" if refresh_recommended else "emerald",
        "age_text": age_text
    }
