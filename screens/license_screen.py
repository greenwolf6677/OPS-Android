"""
OPS License Screen
شاشة الترخيص والتفعيل لنظام Android
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.properties import StringProperty, BooleanProperty
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.core.clipboard import Clipboard

from security.android_security import get_license_info, activate_program, generate_activation_code


class LicenseScreen(Screen):
    """شاشة الترخيص والتفعيل"""
    
    status_text = StringProperty("")
    status_color = StringProperty("00aa44")
    machine_id = StringProperty("")
    app_version = StringProperty("V 1.0.0")
    message = StringProperty("")
    activation_code = StringProperty("")
    show_code = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.load_license_info()
    
    def on_enter(self):
        """عند دخول الشاشة"""
        self.load_license_info()
        Logger.info("OPS License: Screen entered")
    
    def load_license_info(self):
        """تحميل معلومات الترخيص"""
        info = get_license_info()
        
        self.machine_id = info['machine_id']
        self.app_version = info['app_version']
        self.message = info['message']
        
        if info['status'] == 'activated':
            self.status_text = "✅ النسخة مفعلة مدى الحياة"
            self.status_color = "00aa44"
        elif info['status'] == 'trial':
            self.status_text = f"⏳ نسخة تجريبية - متبقي {info['days_left']} يوم"
            self.status_color = "ffaa00"
        elif info['status'] == 'expired':
            self.status_text = "❌ انتهت النسخة التجريبية"
            self.status_color = "ff4444"
        else:
            self.status_text = f"⚠️ {info['message']}"
            self.status_color = "ff4444"
        
        Logger.info(f"OPS License: Status - {self.status_text}")
    
    def activate(self):
        """تفعيل البرنامج"""
        if not self.activation_code:
            self.show_popup("تنبيه", "الرجاء إدخال كود التفعيل")
            return
        
        success, msg = activate_program(self.activation_code)
        
        if success:
            self.status_text = "✅ النسخة مفعلة مدى الحياة"
            self.status_color = "00aa44"
            self.show_popup("نجاح", msg)
            # العودة للشاشة الرئيسية بعد 2 ثانية
            Clock.schedule_once(lambda dt: self.go_to_dashboard(), 2)
        else:
            self.show_popup("خطأ", msg)
    
    def go_to_dashboard(self):
        """الانتقال إلى لوحة التحكم"""
        self.manager.current = 'dashboard'
    
    def copy_machine_id(self):
        """نسخ Machine ID"""
        Clipboard.copy(self.machine_id)
        self.show_popup("نجاح", "تم نسخ Machine ID")
    
    def show_code_toggle(self):
        """إظهار/إخفاء كود التفعيل"""
        self.show_code = not self.show_code
    
    def show_popup(self, title, message):
        """عرض نافذة منبثقة"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=message, font_name='ArabicFont', halign='center', text_size=(400, None)))
        
        btn = Button(text="موافق", size_hint_y=0.3, font_name='ArabicFont')
        popup = Popup(title=title, content=content, size_hint=(0.7, 0.4))
        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        
        popup.open()