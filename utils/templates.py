# utils/templates.py
from fastapi.templating import Jinja2Templates
from datetime import datetime

templates = Jinja2Templates(directory="templates")

def datetimeformat(value):
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            return value
    return value.strftime("%d/%m/%Y")

def currencyformat(value):
    try:
        return "{:,.0f} đ".format(float(value))
    except (ValueError, TypeError):
        return str(value)

templates.env.filters["datetimeformat"] = datetimeformat
templates.env.filters["currencyformat"] = currencyformat