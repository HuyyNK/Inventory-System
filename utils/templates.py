from fastapi.templating import Jinja2Templates
from datetime import datetime
import locale

# Đặt locale để sử dụng dấu chấm làm phân cách hàng nghìn (thay vì dấu phẩy)
locale.setlocale(locale.LC_ALL, 'vi_VN.UTF-8')  # Sử dụng locale Việt Nam

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
        # Chuyển đổi value thành float và định dạng với locale Việt Nam
        return locale.format_string("%.0f đ", float(value), grouping=True)
    except (ValueError, TypeError):
        return str(value)

templates.env.filters["datetimeformat"] = datetimeformat
templates.env.filters["currencyformat"] = currencyformat