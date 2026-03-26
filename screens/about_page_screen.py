import os
import hashlib
import uuid
import socket
import datetime
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.properties import StringProperty
from kivy.utils import platform
from kivy.logger import Logger
from kivy.core.clipboard import Clipboard

# تشفير البيانات - تأكد من تثبيت cryptography عبر pip
try:
    from cryptography.fernet import Fernet
except ImportError:
    Logger.error("OPS About: cryptography module not found. Run 'pip install cryptography'")

# إعدادات البرنامج
APP_VERSION = "V 1.0.0"
TRIAL_DAYS = 14
FERNET_KEY = b'YJ-k0lYk6dA7Cw4nX3hYJ7ZQdQkX3pxVp_nJ8QvI2XY='
fernet = Fernet(FERNET_KEY)
ACTIVATION_SECRET = "OPS-2026-SECRET-777"

# تحديد مسار ملفات الترخيص بشكل آمن للأندرويد
if platform == 'android':
    from android.storage import app_storage_path
    # استخدام app_storage_path بدلاً من primary_external لضمان الصلاحيات دون الحاجة لطلب إذن الوصول للملفات
    LICENSE_FOLDER = os.path.join(app_storage_path(), 'ops_license')
else:
    LICENSE_FOLDER = os.path.join(os.path.expanduser("~"), ".ops_license")

LICENSE_FILE = os.path.join(LICENSE_FOLDER, "license.dat")
BACKUP_FILE = os.path.join(LICENSE_FOLDER, "license.bak")

class AboutPageScreen(Screen):
    status_text = StringProperty("تحميل...")
    status_color = StringProperty("#ffffff")
    machine_id = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # إنشاء المجلد أولاً
        try:
            os.makedirs(LICENSE_FOLDER, exist_ok=True)
        except Exception as e:
            Logger.error(f"OPS About: Could not create license folder - {e}")

        self.machine_id = self.get_machine_id()
        self.load_license_status()

    def get_machine_id(self):
        """الحصول على معرف فريد للجهاز"""
        try:
            # دمج عدة معرفات لضمان ثبات الـ ID حتى لو تغير الـ IP أو الهوست
            node = str(uuid.getnode())
            combined = node + ACTIVATION_SECRET
            return hashlib.sha256(combined.encode()).hexdigest()[:16].upper()
        except:
            return "OPS-UNKNOWN-ID"

    def encrypt_data(self, data: str) -> bytes:
        return fernet.encrypt(data.encode())

    def decrypt_data(self, data: bytes) -> str:
        try:
            return fernet.decrypt(data).decode()
        except:
            return ""

    def save_license(self, status="TRIAL"):
        try:
            today = str(datetime.date.today())
            content = f"{today}\n{self.machine_id}\n{status}"
            data_enc = self.encrypt_data(content)
            
            for path in [LICENSE_FILE, BACKUP_FILE]:
                with open(path, "wb") as f:
                    f.write(data_enc)
            return True
        except Exception as e:
            Logger.error(f"OPS About: Save error - {e}")
            return False

    def load_license_status(self):
        if not os.path.exists(LICENSE_FILE):
            self.save_license("TRIAL")
            self.status_text = f"نسخة تجريبية - متبقي {TRIAL_DAYS} يوم"
            self.status_color = "#ffd700"
            return

        try:
            with open(LICENSE_FILE, "rb") as f:
                decrypted = self.decrypt_data(f.read())
                if not decrypted: raise ValueError("Decryption failed")
                lines = decrypted.splitlines()

            if lines[1] != self.machine_id:
                self.status_text = "الجهاز غير مرخص"
                self.status_color = "#ff5555"
                return

            if lines[2] == "ACTIVATED":
                self.status_text = "النسخة مفعلة مدى الحياة"
                self.status_color = "#28a745"
            else:
                start_date = datetime.datetime.strptime(lines[0], "%Y-%m-%d").date()
                days_used = (datetime.date.today() - start_date).days
                days_left = max(0, TRIAL_DAYS - days_used)
                
                if days_left > 0:
                    self.status_text = f"نسخة تجريبية - متبقي {days_left} يوم"
                    self.status_color = "#ffd700"
                else:
                    self.status_text = "انتهت النسخة التجريبية"
                    self.status_color = "#ff5555"
        except:
            self.status_text = "خطأ في الترخيص"
            self.status_color = "#ff5555"

    def activate_program(self, key):
        """التحقق من الكود وتفعيل البرنامج"""
        if not key:
            return False, "الرجاء إدخال كود"
            
        expected = hashlib.sha256((ACTIVATION_SECRET + self.machine_id).encode()).hexdigest()[:12].upper()
        
        if key.strip().upper() == expected:
            if self.save_license("ACTIVATED"):
                self.load_license_status()
                return True, "تم التفعيل بنجاح!"
            return False, "فشل حفظ ملف التفعيل"
        return False, "كود التفعيل غير صحيح!"

    def copy_machine_id(self):
        Clipboard.copy(self.machine_id)
        self.show_popup("نجاح", "تم نسخ المعرف!")

    def show_popup(self, title, message):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=message, font_name='ArabicFont', halign='center'))
        btn = Button(text="موافق", size_hint_y=0.3, font_name='ArabicFont')
        popup = Popup(title=title, content=content, size_hint=(0.7, 0.4))
        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        popup.open()