from models.dashboard_sql import fetch_kpi, fetch_charts, fetch_warnings, fetch_activities
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.ERROR)

def get_kpi_data():
    try:
        current_date = datetime.now()
        expiry_threshold = current_date + timedelta(days=7)
        return fetch_kpi(expiry_threshold)
    except Exception as e:
        logging.error(f"Error fetching KPI: {str(e)}")
        raise Exception(f"Error fetching KPI: {str(e)}")

def get_charts_data():
    try:
        current_date = datetime.now()
        six_months_ago = current_date - timedelta(days=180)
        one_month_ago = current_date - timedelta(days=30)
        result = fetch_charts(six_months_ago, one_month_ago)
        return {
            "pie": {"labels": result["pie_labels"], "data": result["pie_values"]},
            "line": {"labels": result["line_labels"], "inbound": result["inbound_data"], "outbound": result["outbound_data"]},
            "bar": {"labels": result["bar_labels"], "data": result["bar_values"]},
            "stacked": {"labels": result["stacked_labels"], "data": result["stacked_values"]}
        }
    except Exception as e:
        logging.error(f"Error fetching charts: {str(e)}")
        raise Exception(f"Error fetching charts: {str(e)}")

def get_warnings_data():
    try:
        current_date = datetime.now()
        expiry_threshold = current_date + timedelta(days=7)
        activities = fetch_activities()
        last_date = datetime.fromisoformat(activities[0]["date"]).date() if activities else current_date.date()
        return fetch_warnings(expiry_threshold, last_date)  # Sửa lỗi: fetchologique_warnings -> fetch_warnings
    except Exception as e:
        logging.error(f"Error fetching warnings: {str(e)}")
        raise Exception(f"Error fetching warnings: {str(e)}")

def get_activities_data():
    try:
        return fetch_activities()
    except Exception as e:
        logging.error(f"Error fetching activities: {str(e)}")
        raise Exception(f"Error fetching activities: {str(e)}")