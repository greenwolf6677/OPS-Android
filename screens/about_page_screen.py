"""
OPS About & Activation Page
صفحة حول البرنامج والتفعيل لنظام OPS
"""

import os
import sys
import hashlib
import uuid
import socket
import datetime
import json
import requests
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.properties import StringProperty, NumericProperty
from kivy.clock import Clock
from kivy.utils import platform
from kivy.logger import Logger
from kivy.core.clipboard import Clipboard

# إعدادات البرنامج
APP_VERSION = "V 1.0.0"
TRIAL_DAYS = 14

# تحديد مسار ملفات الترخيص
if platform == 'android':
    from android.storage import primary_external_storage_path
    LICENSE_FOLDER = os.path.join(primary_external_storage_path(), 'ops_license')
else:
    LICENSE_FOLDER = os.path.join(os.path.expanduser("~"), ".ops_license")

LICENSE_FILE = os.path.join(LICENSE_FOLDER, "license.dat")
BACKUP_FILE = os.path.join(LICENSE_FOLDER, "license.bak")

FERNET_KEY = b'YJ-k0lYk6dA7Cw4nX3hYJ7ZQdQkX3pxVp_nJ8QvI2XY='
from cryptography.fernet import Fernet
fernet = Fernet(FERNET_KEY)
ACTIVATION_SECRET = "OPS-2026-SECRET-777"


class AboutPageScreen(Screen):
    """صفحة حول البرنامج والتفعيل"""
    
    status_text = StringProperty("")
    status_color = StringProperty("")
    machine_id = StringProperty("")
    activation_code = StringProperty("")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.machine_id = self.get_machine_id()
        self.load_license_status()
        
        # إنشاء مجلد الترخيص إذا لم يكن موجوداً
        os.makedirs(LICENSE_FOLDER, exist_ok=True)
        
        Logger.info(f"OPS About: License folder: {LICENSE_FOLDER}")
    
    def get_machine_id(self):
        """الحصول على معرف الجهاز الفريد"""
        try:
            # استخدام UUID للجهاز
            machine_id = hashlib.sha256(str(uuid.getnode()).encode()).hexdigest()[:16]
            # إضافة اسم المضيف
            hostname = hashlib.sha256(socket.gethostname().encode()).hexdigest()[:8]
            machine_id = hashlib.sha256((machine_id + hostname).encode()).hexdigest()[:16]
            return machine_id
        except Exception as e:
            Logger.error(f"OPS About: Error getting machine ID - {e}")
            return "DEFAULT-MACHINE"
    
    def encrypt(self, data: str) -> bytes:
        """تشفير البيانات"""
        try:
            return fernet.encrypt(data.encode())
        except Exception as e:
            Logger.error(f"OPS About: Encryption error - {e}")
            return b""
    
    def decrypt(self, data: bytes) -> str:
        """فك تشفير البيانات"""
        try:
            return fernet.decrypt(data).decode()
        except Exception as e:
            Logger.error(f"OPS About: Decryption error - {e}")
            return ""
    
    def save_license(self, status="TRIAL"):
        """حفظ حالة الترخيص"""
        try:
            today = str(datetime.date.today())
            content = f"{today}\n{self.machine_id}\n{status}"
            data_enc = self.encrypt(content)
            with open(LICENSE_FILE, "wb") as f:
                f.write(data_enc)
            with open(BACKUP_FILE, "wb") as f:
                f.write(data_enc)
            Logger.info(f"OPS About: License saved with status: {status}")
            return True
        except Exception as e:
            Logger.error(f"OPS About: Error saving license - {e}")
            return False
    
    def load_license_status(self):
        """تحميل حالة الترخيص"""
        if not os.path.exists(LICENSE_FILE):
            self.save_license("TRIAL")
            self.status_text = f"نسخة تجريبية - متبقي {TRIAL_DAYS} يوم"
            self.status_color = "#ffd700"
            return
        
        try:
            with open(LICENSE_FILE, "rb") as f:
                lines = self.decrypt(f.read()).splitlines()
            
            if len(lines) < 3:
                self.status_text = "الترخيص تالف"
                self.status_color = "#ff5555"
                return
            
            if lines[1] != self.machine_id:
                self.status_text = "الجهاز غير مرخص"
                self.status_color = "#ff5555"
                return
            
            if lines[2] == "ACTIVATED":
                self.status_text = "النسخة مفعلة مدى الحياة"
                self.status_color = "#28a745"
                return
            
            # حساب الأيام المتبقية
            try:
                start_date = datetime.datetime.strptime(lines[0], "%Y-%m-%d").date()
                days_used = (datetime.date.today() - start_date).days
                days_left = TRIAL_DAYS - days_used
                
                if days_left > 0:
                    self.status_text = f"نسخة تجريبية - متبقي {days_left} يوم"
                    self.status_color = "#ffd700"
                else:
                    self.status_text = "انتهت النسخة التجريبية"
                    self.status_color = "#ff5555"
            except:
                self.status_text = "خطأ في قراءة التاريخ"
                self.status_color = "#ff5555"
                
        except Exception as e:
            Logger.error(f"OPS About: Error loading license - {e}")
            self.status_text = "الترخيص غير صالح"
            self.status_color = "#ff5555"
    
    def generate_activation_code(self):
        """توليد كود التفعيل"""
        code = hashlib.sha256((ACTIVATION_SECRET + self.machine_id).encode()).hexdigest()[:12].upper()
        return code
    
    def activate_program(self, key):
        """تفعيل البرنامج"""
        expected = self.generate_activation_code()
        if key.strip().upper() == expected:
            self.save_license("ACTIVATED")
            self.load_license_status()
            return True, "تم تفعيل البرنامج بنجاح!\nالنسخة الآن دائمة."
        return False, "كود التفعيل غير صحيح!"
    
    def copy_machine_id(self):
        """نسخ Machine ID إلى الحافظة"""
        try:
            Clipboard.copy(self.machine_id)
            self.show_popup("نجاح", "تم نسخ Machine ID!")
            Logger.info("OPS About: Machine ID copied to clipboard")
        except Exception as e:
            Logger.error(f"OPS About: Error copying - {e}")
            self.show_popup("خطأ", "فشل النسخ")
    
    def show_popup(self, title, message):
        """عرض نافذة منبثقة"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=message, font_name='ArabicFont', halign='center'))
        
        btn = Button(text="موافق", size_hint_y=0.3, font_name='ArabicFont')
        popup = Popup(title=title, content=content, size_hint=(0.7, 0.4))
        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        
        popup.open()
    
    def build_ui(self):
        """بناء واجهة المستخدم (سيتم تنفيذها من KV)"""
        pass