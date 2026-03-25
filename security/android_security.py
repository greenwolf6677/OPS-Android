import os
import hashlib
import uuid
import socket
import datetime
from kivy.utils import platform
from kivy.logger import Logger
from kivy.app import App

# تحديد مسار الترخيص - تم التعديل ليكون داخل مجلد بيانات التطبيق الآمن
if platform == 'android':
    from android.permissions import request_permissions, Permission
    # استخدام مجلد بيانات التطبيق الخاص لضمان الاستقرار في أندرويد 11+
    BASE_PATH = App.get_running_app().user_data_dir
    LICENSE_FOLDER = os.path.join(BASE_PATH, 'security_ops')
else:
    BASE_PATH = os.path.expanduser("~")
    LICENSE_FOLDER = os.path.join(BASE_PATH, '.ops_license')

LICENSE_FILE = os.path.join(LICENSE_FOLDER, 'license.dat')
LAST_RUN_FILE = os.path.join(LICENSE_FOLDER, 'timestamp.dat')

# إعدادات
TRIAL_DAYS = 14
ACTIVATION_SECRET = "OPS-2026-ANDROID-SECRET-777"
FERNET_KEY = b'YJ-k0lYk6dA7Cw4nX3hYJ7ZQdQkX3pxVp_nJ8QvI2XY='

os.makedirs(LICENSE_FOLDER, exist_ok=True)

# محاولة تحميل التشفير
try:
    from cryptography.fernet import Fernet
    cipher_suite = Fernet(FERNET_KEY)
    ENCRYPTION_ENABLED = True
except ImportError:
    ENCRYPTION_ENABLED = False
    Logger.warning("OPS Security: Cryptography not installed, using base64 fallback")

def encrypt_data(data: str) -> bytes:
    if ENCRYPTION_ENABLED:
        return cipher_suite.encrypt(data.encode())
    import base64
    return base64.b64encode(data.encode())

def decrypt_data(data: bytes) -> str:
    try:
        if ENCRYPTION_ENABLED:
            return cipher_suite.decrypt(data).decode()
        import base64
        return base64.b64decode(data).decode()
    except:
        return ""

def get_machine_id():
    """جلب معرف فريد للجهاز (Android ID)"""
    if platform == 'android':
        try:
            from jnius import autoclass
            from android import mActivity
            Context = autoclass('android.content.Context')
            Settings = autoclass('android.provider.Settings$Secure')
            android_id = Settings.getString(mActivity.getContentResolver(), Settings.ANDROID_ID)
            if android_id:
                return hashlib.sha256(android_id.encode()).hexdigest()[:16].upper()
        except Exception as e:
            Logger.error(f"OPS Security: Jnius failed - {e}")
    
    # Fallback للمحاكي أو سطح المكتب
    fallback_id = str(uuid.getnode())
    return hashlib.sha256(fallback_id.encode()).hexdigest()[:16].upper()

def get_real_date():
    """جلب التاريخ من الإنترنت لتعطيل التلاعب"""
    import requests
    urls = ["https://worldtimeapi.org/api/ip", "https://date.nager.at/api/v2/publicholidays/2026/US"]
    for url in urls:
        try:
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                # محاولة استخراج التاريخ من header الاستجابة (أضمن وأسرع)
                date_str = response.headers.get('Date')
                return datetime.datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %Z').date()
        except:
            continue
    return datetime.date.today()

def check_license():
    machine_id = get_machine_id()
    today = get_real_date()

    # فحص التلاعب بالتاريخ
    if os.path.exists(LAST_RUN_FILE):
        with open(LAST_RUN_FILE, 'r') as f:
            try:
                last_date = datetime.datetime.strptime(f.read(), '%Y-%m-%d').date()
                if today < last_date:
                    return "invalid", 0, "تم اكتشاف تلاعب في تاريخ الجهاز!"
            except: pass

    with open(LAST_RUN_FILE, 'w') as f: f.write(str(today))

    if not os.path.exists(LICENSE_FILE):
        return "trial_new", TRIAL_DAYS, "نسخة تجريبية جديدة"

    try:
        with open(LICENSE_FILE, 'rb') as f:
            raw_data = f.read()
            decrypted = decrypt_data(raw_data)
            parts = decrypted.split('|')
            
            if len(parts) != 3: return "invalid", 0, "ملف ترخيص غير صالح"
            
            saved_date = datetime.datetime.strptime(parts[0], '%Y-%m-%d').date()
            saved_id = parts[1]
            status = parts[2]

            if saved_id != machine_id:
                return "invalid", 0, "الترخيص لا يخص هذا الجهاز"

            if status == "FULL":
                return "activated", -1, "النسخة كاملة"

            days_passed = (today - saved_date).days
            remaining = TRIAL_DAYS - days_passed
            
            if remaining <= 0:
                return "expired", 0, "انتهت الفترة التجريبية"
            return "trial", remaining, f"متبقي {remaining} يوم"
    except:
        return "invalid", 0, "خطأ في قراءة الترخيص"

def run_security():
    # سيتم استدعاء هذه الدالة من main.py
    res = check_license()
    if res[0] in ["activated", "trial", "trial_new"]:
        if res[0] == "trial_new":
            save_license_file("TRIAL")
        return True, res[2]
    return False, res[2]

def save_license_file(status):
    mid = get_machine_id()
    date_str = str(get_real_date())
    data = f"{date_str}|{mid}|{status}"
    with open(LICENSE_FILE, 'wb') as f:
        f.write(encrypt_data(data))

def activate_program(key):
    # كود التفعيل: OPS + أول 5 حروف من الـ ID + كلمة SECRET
    mid = get_machine_id()
    expected = hashlib.sha256((mid + ACTIVATION_SECRET).encode()).hexdigest()[:10].upper()
    if key.strip().upper() == expected:
        save_license_file("FULL")
        return True, "تم التفعيل بنجاح"
    return False, "كود غير صحيح"