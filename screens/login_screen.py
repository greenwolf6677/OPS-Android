"""
OPS Login Screen
شاشة تسجيل الدخول لنظام OPS
"""

from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, BooleanProperty
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.logger import Logger

import sqlite3
import os
from database import get_db_connection


class LoginScreen(Screen):
    """شاشة تسجيل الدخول"""
    
    username = StringProperty("")
    password = StringProperty("")
    show_password = BooleanProperty(False)
    remember_me = BooleanProperty(False)
    error_message = StringProperty("")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user_id = None
        self.remember_file = "ops_remember.txt"
        
        # تحميل اسم المستخدم المحفوظ
        try:
            if os.path.exists(self.remember_file):
                with open(self.remember_file, 'r', encoding='utf-8') as f:
                    saved = f.read().strip()
                    if saved:
                        self.username = saved
                        self.remember_me = True
                        Logger.info(f"OPS Login: Loaded saved username: {saved}")
        except Exception as e:
            Logger.error(f"OPS Login: Error loading saved username - {e}")
    
    def on_enter(self):
        """عند دخول الشاشة"""
        self.error_message = ""
        Logger.info("OPS Login: Login screen entered")
    
    def toggle_password(self):
        """إظهار/إخفاء كلمة المرور"""
        self.show_password = not self.show_password
        Logger.debug(f"OPS Login: Password visibility toggled to {self.show_password}")
    
    def check_login(self):
        """التحقق من بيانات تسجيل الدخول"""
        if not self.username or not self.password:
            self.error_message = "يرجى إدخال اسم المستخدم وكلمة المرور"
            self.show_error_popup()
            return
        
        try:
            conn = get_db_connection()
            user = conn.execute(
                "SELECT id, username, full_name, role FROM users WHERE username = ? AND password = ?",
                (self.username, self.password)
            ).fetchone()
            conn.close()
            
            if user:
                self.user_id = user['id']
                
                # حفظ اسم المستخدم إذا تم الاختيار
                if self.remember_me:
                    try:
                        with open(self.remember_file, 'w', encoding='utf-8') as f:
                            f.write(self.username)
                        Logger.info(f"OPS Login: Saved username: {self.username}")
                    except Exception as e:
                        Logger.error(f"OPS Login: Error saving username - {e}")
                else:
                    try:
                        if os.path.exists(self.remember_file):
                            os.remove(self.remember_file)
                            Logger.info("OPS Login: Removed saved username")
                    except:
                        pass
                
                # تعيين المتغيرات العامة
                app = self.manager.app
                app.user_id = self.user_id
                app.user_role = user['role']
                app.user_name = user['full_name']
                
                Logger.info(f"OPS Login: User logged in - {user['username']} ({user['role']})")
                
                # الانتقال إلى لوحة التحكم
                self.manager.current = 'dashboard'
            else:
                self.error_message = "اسم المستخدم أو كلمة المرور غير صحيحة"
                self.show_error_popup()
                Logger.warning(f"OPS Login: Failed login attempt for user: {self.username}")
                
        except Exception as e:
            self.error_message = f"خطأ: {str(e)}"
            self.show_error_popup()
            Logger.error(f"OPS Login: Error during login - {e}")
    
    def show_error_popup(self):
        """عرض نافذة الخطأ"""
        if self.error_message:
            popup = Popup(
                title="خطأ",
                content=Label(text=self.error_message, font_name='ArabicFont'),
                size_hint=(0.8, 0.4),
                auto_dismiss=True
            )
            popup.open()