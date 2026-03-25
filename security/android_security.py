"""
OPS Android Security Module
وحدة الحماية والترخيص لنظام Android
"""

import os
import sys
import hashlib
import uuid
import socket
import datetime
import json
import sqlite3
from kivy.utils import platform
from kivy.logger import Logger

# تحديد مسار الترخيص
if platform == 'android':
    from android.storage import primary_external_storage_path
    from android.permissions import request_permissions, Permission
    
    BASE_PATH = primary_external_storage_path()
    LICENSE_FOLDER = os.path.join(BASE_PATH, 'ops_license')
    
    # طلب الأذونات
    try:
        request_permissions([
            Permission.READ_EXTERNAL_STORAGE,
            Permission.WRITE_EXTERNAL_STORAGE
        ])
    except:
        pass
else:
    BASE_PATH = os.path.expanduser("~")
    LICENSE_FOLDER = os.path.join(BASE_PATH, '.ops_license')

LICENSE_FILE = os.path.join(LICENSE_FOLDER, 'license.dat')
BACKUP_FILE = os.path.join(LICENSE_FOLDER, 'license.bak')
LAST_RUN_FILE = os.path.join(LICENSE_FOLDER, 'last_run.dat')

# إعدادات البرنامج
APP_VERSION = "V 1.0.0"
TRIAL_DAYS = 14
ACTIVATION_SECRET = "OPS-2026-ANDROID-SECRET-777"

# مفتاح التشفير الثابت
FERNET_KEY = b'YJ-k0lYk6dA7Cw4nX3hYJ7ZQdQkX3pxVp_nJ8QvI2XY='

# إنشاء مجلد الترخيص
os.makedirs(LICENSE_FOLDER, exist_ok=True)


# ==================== تشفير وفك ====================
try:
    from cryptography.fernet import Fernet
    fernet = Fernet(FERNET_KEY)
    ENCRYPTION_AVAILABLE = True
    Logger.info("OPS Security: Encryption module loaded")
except ImportError:
    ENCRYPTION_AVAILABLE = False
    Logger.warning("OPS Security: Cryptography not available")


def encrypt_data(data: str) -> bytes:
    """تشفير البيانات"""
    if not ENCRYPTION_AVAILABLE:
        return data.encode()
    try:
        return fernet.encrypt(data.encode())
    except Exception as e:
        Logger.error(f"OPS Security: Encryption error - {e}")
        return data.encode()


def decrypt_data(data: bytes) -> str:
    """فك تشفير البيانات"""
    if not ENCRYPTION_AVAILABLE:
        return data.decode()
    try:
        return fernet.decrypt(data).decode()
    except Exception as e:
        Logger.error(f"OPS Security: Decryption error - {e}")
        return ""


# ==================== Machine ID (محسن للأندرويد) ====================
def get_machine_id():
    """الحصول على معرف فريد للجهاز"""
    try:
        if platform == 'android':
            # على Android، نستخدم Android ID
            try:
                from jnius import autoclass
                from android import mActivity
                
                Settings = autoclass('android.provider.Settings')
                Secure = autoclass('android.provider.Settings$Secure')
                android_id = Secure.getString(mActivity.getContentResolver(), 
                                              Settings.Secure.ANDROID_ID)
                
                if android_id:
                    machine_id = hashlib.sha256(android_id.encode()).hexdigest()[:16]
                else:
                    # البديل: استخدام UUID
                    machine_id = hashlib.sha256(str(uuid.getnode()).encode()).hexdigest()[:16]
            except:
                machine_id = hashlib.sha256(str(uuid.getnode()).encode()).hexdigest()[:16]
        else:
            # على Windows/Linux
            cpu = hashlib.sha256(str(uuid.getnode()).encode()).hexdigest()
            hostname = hashlib.sha256(socket.gethostname().encode()).hexdigest()
            machine_id = hashlib.sha256((cpu + hostname).encode()).hexdigest()[:16]
        
        Logger.info(f"OPS Security: Machine ID generated")
        return machine_id
        
    except Exception as e:
        Logger.error(f"OPS Security: Error getting machine ID - {e}")
        return "DEFAULT-MACHINE"


# ==================== حماية التاريخ ====================
def get_real_date():
    """الحصول على التاريخ الحقيقي"""
    try:
        # محاولة الحصول على التاريخ من الإنترنت
        import requests
        response = requests.get("https://worldtimeapi.org/api/ip", timeout=5)
        data = response.json()
        return datetime.datetime.strptime(data["utc_datetime"][:10], "%Y-%m-%d").date()
    except:
        # إذا فشل، نستخدم التاريخ المحلي
        return datetime.date.today()


def check_date_tamper():
    """التحقق من عدم التلاعب بالتاريخ"""
    try:
        today = get_real_date()
        
        if not os.path.exists(LAST_RUN_FILE):
            with open(LAST_RUN_FILE, "w") as f:
                f.write(str(today))
            return True
        
        with open(LAST_RUN_FILE, "r") as f:
            last_date = datetime.datetime.strptime(f.read().strip(), "%Y-%m-%d").date()
        
        # إذا كان التاريخ الحالي أقل من آخر تشغيل، فهناك تلاعب
        if today < last_date:
            Logger.warning("OPS Security: Date tampering detected!")
            return False
        
        # تحديث آخر تشغيل
        with open(LAST_RUN_FILE, "w") as f:
            f.write(str(today))
        return True
        
    except Exception as e:
        Logger.error(f"OPS Security: Error checking date - {e}")
        return True


# ==================== نظام الترخيص ====================
def save_license(status="TRIAL"):
    """حفظ حالة الترخيص"""
    try:
        machine_id = get_machine_id()
        today = str(get_real_date())
        content = f"{today}\n{machine_id}\n{status}"
        data_enc = encrypt_data(content)
        
        with open(LICENSE_FILE, "wb") as f:
            f.write(data_enc)
        with open(BACKUP_FILE, "wb") as f:
            f.write(data_enc)
        
        Logger.info(f"OPS Security: License saved with status: {status}")
        return True
    except Exception as e:
        Logger.error(f"OPS Security: Error saving license - {e}")
        return False


def check_license():
    """التحقق من حالة الترخيص"""
    # التحقق من التاريخ أولاً
    if not check_date_tamper():
        return "invalid", 0, "تم اكتشاف تلاعب بالتاريخ!"
    
    machine_id = get_machine_id()
    
    if not os.path.exists(LICENSE_FILE):
        save_license("TRIAL")
        return "trial", TRIAL_DAYS, f"نسخة تجريبية - {TRIAL_DAYS} يوم"
    
    try:
        with open(LICENSE_FILE, "rb") as f:
            data = f.read()
            if not data:
                save_license("TRIAL")
                return "trial", TRIAL_DAYS, f"نسخة تجريبية - {TRIAL_DAYS} يوم"
            
            lines = decrypt_data(data).splitlines()
        
        if len(lines) < 3:
            return "invalid", 0, "ملف الترخيص تالف"
        
        if lines[1] != machine_id:
            return "invalid", 0, "هذا الجهاز غير مرخص"
        
        if lines[2] == "ACTIVATED":
            return "activated", -1, "النسخة مفعلة مدى الحياة"
        
        start_date = datetime.datetime.strptime(lines[0], "%Y-%m-%d").date()
        today = get_real_date()
        days_used = (today - start_date).days
        days_left = TRIAL_DAYS - days_used
        
        if days_left > 0:
            return "trial", days_left, f"نسخة تجريبية - متبقي {days_left} يوم"
        else:
            return "expired", 0, "انتهت النسخة التجريبية"
            
    except Exception as e:
        Logger.error(f"OPS Security: Error checking license - {e}")
        return "error", 0, f"خطأ: {str(e)}"


# ==================== توليد كود التفعيل ====================
def generate_activation_code():
    """توليد كود التفعيل بناءً على Machine ID"""
    machine_id = get_machine_id()
    code = hashlib.sha256((ACTIVATION_SECRET + machine_id).encode()).hexdigest()[:12].upper()
    return code


def activate_program(key: str):
    """تفعيل البرنامج"""
    expected = generate_activation_code()
    if key.strip().upper() == expected:
        save_license("ACTIVATED")
        return True, "تم تفعيل البرنامج بنجاح!\nالنسخة الآن دائمة."
    return False, "كود التفعيل غير صحيح!"


# ==================== دوال مساعدة ====================
def run_security():
    """تشغيل فحص الأمان عند بدء التطبيق"""
    status, days, message = check_license()
    
    Logger.info(f"OPS Security: License status - {status}")
    
    if status == "invalid" or status == "error":
        Logger.error(f"OPS Security: Invalid license - {message}")
        return False, message
    elif status == "expired":
        Logger.warning(f"OPS Security: License expired - {message}")
        return False, message
    else:
        Logger.info(f"OPS Security: License OK - {message}")
        return True, message


def get_license_info():
    """الحصول على معلومات الترخيص للعرض"""
    status, days, message = check_license()
    
    info = {
        'status': status,
        'days_left': days,
        'message': message,
        'machine_id': get_machine_id(),
        'app_version': APP_VERSION,
        'trial_days': TRIAL_DAYS
    }
    
    return info


def secure_db_connection(conn):
    """تشفير/فك تشفير قاعدة البيانات (اختياري)"""
    # يمكن إضافة تشفير لقاعدة البيانات هنا
    pass