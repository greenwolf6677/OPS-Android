"""
OPS Helper Functions
دوال مساعدة عامة لنظام OPS
"""

import re
import uuid
import random
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP


# ==================== التنسيق ====================

def format_currency(amount, currency="₪", decimals=2):
    """
    تنسيق المبلغ مع رمز العملة
    مثال: format_currency(100.5) -> "100.50 ₪"
    """
    try:
        amount = float(amount)
        formatted = f"{amount:.{decimals}f}"
        return f"{formatted} {currency}"
    except (ValueError, TypeError):
        return f"0.00 {currency}"


def format_date(date_obj, format_str="%Y-%m-%d"):
    """تنسيق التاريخ"""
    if not date_obj:
        return ""
    try:
        if isinstance(date_obj, str):
            date_obj = datetime.strptime(date_obj, "%Y-%m-%d")
        return date_obj.strftime(format_str)
    except:
        return str(date_obj)


def format_datetime(dt_obj, format_str="%Y-%m-%d %H:%M"):
    """تنسيق التاريخ والوقت"""
    if not dt_obj:
        return ""
    try:
        if isinstance(dt_obj, str):
            dt_obj = datetime.strptime(dt_obj, "%Y-%m-%d %H:%M:%S")
        return dt_obj.strftime(format_str)
    except:
        return str(dt_obj)


# ==================== توليد المعرفات ====================

def generate_id(prefix="", length=8):
    """توليد معرف فريد"""
    random_id = str(uuid.uuid4()).replace('-', '')[:length]
    if prefix:
        return f"{prefix}_{random_id}"
    return random_id


def generate_barcode(length=12):
    """توليد باركود عشوائي"""
    return ''.join([str(random.randint(0, 9)) for _ in range(length)])


# ==================== التحقق من الصحة ====================

def validate_email(email):
    """التحقق من صحة البريد الإلكتروني"""
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email)) if email else False


def validate_phone(phone, country="SA"):
    """التحقق من صحة رقم الهاتف"""
    patterns = {
        'SA': r'^05[0-9]{8}$',
        'EG': r'^01[0-9]{9}$',
        'JO': r'^07[0-9]{8}$',
        'PS': r'^05[0-9]{8}$',
    }
    pattern = patterns.get(country, r'^[0-9]{10,15}$')
    return bool(re.match(pattern, phone)) if phone else False


# ==================== معالجة النصوص ====================

def truncate_text(text, max_length=50, suffix="..."):
    """قص النص إذا تجاوز الحد الأقصى"""
    if not text:
        return ""
    text = str(text)
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def sanitize_input(text, allow_spaces=True, allow_special=False):
    """تنظيف النص من الأحرف غير المرغوب فيها"""
    if not text:
        return ""
    text = str(text)
    if not allow_special:
        text = re.sub(r'[^\w\s]', '', text)
    if not allow_spaces:
        text = text.replace(' ', '')
    return text.strip()


# ==================== الحسابات ====================

def calculate_percentage(value, total, decimals=2):
    """حساب النسبة المئوية"""
    if not total:
        return 0.0
    try:
        percentage = (value / total) * 100
        return round(percentage, decimals)
    except (ValueError, TypeError):
        return 0.0


def calculate_discount(price, discount_percent, decimals=2):
    """حساب السعر بعد الخصم"""
    try:
        discount_amount = price * (discount_percent / 100)
        return round(price - discount_amount, decimals)
    except (ValueError, TypeError):
        return price


def safe_divide(a, b, default=0):
    """قسمة آمنة (تجنب القسمة على صفر)"""
    try:
        if b == 0:
            return default
        return a / b
    except (ValueError, TypeError):
        return default


def round_number(number, decimals=2, method='half_up'):
    """تقريب الأرقام بطريقة محددة"""
    try:
        number = float(number)
        if method == 'half_up':
            quantize = Decimal('0.' + '0' * decimals)
            return float(Decimal(str(number)).quantize(quantize, rounding=ROUND_HALF_UP))
        return round(number, decimals)
    except (ValueError, TypeError):
        return 0.0


# ==================== التحقق من الأنواع ====================

def is_number(value):
    """التحقق من أن القيمة رقم"""
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False


def is_integer(value):
    """التحقق من أن القيمة عدد صحيح"""
    try:
        return float(value).is_integer()
    except (ValueError, TypeError):
        return False


def is_float(value):
    """التحقق من أن القيمة عدد عشري"""
    try:
        float(value)
        return '.' in str(value)
    except (ValueError, TypeError):
        return False


# ==================== التاريخ والوقت ====================

def get_current_time(format_str="%H:%M:%S"):
    """الحصول على الوقت الحالي"""
    return datetime.now().strftime(format_str)


def get_current_date(format_str="%Y-%m-%d"):
    """الحصول على التاريخ الحالي"""
    return datetime.now().strftime(format_str)


def time_ago(dt, now=None):
    """حساب الوقت المنقضي منذ التاريخ"""
    if not dt:
        return ""
    
    if isinstance(dt, str):
        try:
            dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
        except:
            return str(dt)
    
    if not now:
        now = datetime.now()
    
    diff = now - dt
    
    seconds = diff.total_seconds()
    minutes = seconds / 60
    hours = minutes / 60
    days = hours / 24
    weeks = days / 7
    months = days / 30
    years = days / 365
    
    if years >= 1:
        return f"منذ {int(years)} سنة"
    elif months >= 1:
        return f"منذ {int(months)} شهر"
    elif weeks >= 1:
        return f"منذ {int(weeks)} أسبوع"
    elif days >= 1:
        return f"منذ {int(days)} يوم"
    elif hours >= 1:
        return f"منذ {int(hours)} ساعة"
    elif minutes >= 1:
        return f"منذ {int(minutes)} دقيقة"
    else:
        return "منذ لحظات"


# ==================== تحويل البيانات ====================

def dict_to_list(data, keys=None):
    """تحويل قاموس إلى قائمة"""
    if not data:
        return []
    if keys:
        return [data.get(key) for key in keys]
    return list(data.values())


def list_to_dict(data, keys):
    """تحويل قائمة إلى قاموس"""
    if not data or not keys:
        return {}
    return dict(zip(keys, data))


def group_by(items, key_func):
    """تجميع العناصر حسب دالة"""
    groups = {}
    for item in items:
        key = key_func(item)
        if key not in groups:
            groups[key] = []
        groups[key].append(item)
    return groups


def sort_by_key(items, key, reverse=False):
    """ترتيب العناصر حسب مفتاح"""
    return sorted(items, key=lambda x: x.get(key) if isinstance(x, dict) else getattr(x, key, None), reverse=reverse)


def filter_by_value(items, key, value):
    """تصفية العناصر حسب قيمة"""
    return [item for item in items if (item.get(key) if isinstance(item, dict) else getattr(item, key, None)) == value]