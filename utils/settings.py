"""
OPS Settings Manager
إدارة إعدادات المحل
"""

import os
import json
from kivy.utils import platform
from kivy.logger import Logger

if platform == 'android':
    from android.storage import primary_external_storage_path
    BASE_PATH = primary_external_storage_path()
    SETTINGS_DIR = os.path.join(BASE_PATH, 'ops_data')
else:
    BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    SETTINGS_DIR = BASE_PATH

SETTINGS_FILE = os.path.join(SETTINGS_DIR, 'store_settings.json')
IMAGES_DIR = os.path.join(SETTINGS_DIR, 'product_images')

# إنشاء مجلد الصور إذا لم يكن موجوداً
os.makedirs(IMAGES_DIR, exist_ok=True)

DEFAULT_SETTINGS = {
    "store_name": "أبو الكايد مول",
    "store_logo": "",
    "store_phone": "",
    "store_address": "",
    "tax_number": "",
    "receipt_footer": "شكراً لتعاملكم معنا",
    "currency": "₪"
}


def load_settings():
    """تحميل إعدادات المحل"""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return DEFAULT_SETTINGS.copy()
    return DEFAULT_SETTINGS.copy()


def save_settings(settings):
    """حفظ إعدادات المحل"""
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)
        Logger.info("OPS Settings: Settings saved")
    except Exception as e:
        Logger.error(f"OPS Settings: Error saving settings - {e}")


def get_store_name():
    """الحصول على اسم المحل"""
    return load_settings().get("store_name", DEFAULT_SETTINGS["store_name"])


def get_currency():
    """الحصول على رمز العملة"""
    return load_settings().get("currency", DEFAULT_SETTINGS["currency"])