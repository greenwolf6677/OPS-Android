from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty
from kivy.clock import Clock
from datetime import datetime
from kivy.logger import Logger
from kivy.app import App

class DashboardScreen(Screen):
    user_name = StringProperty("")
    current_time = StringProperty("")
    store_name = StringProperty("OPS - Orders Processing System")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # تحديث الوقت فوراً ثم كل ثانية
        self.update_time()
        Clock.schedule_interval(self.update_time, 1)
    
    def on_enter(self):
        """تحديث بيانات المستخدم عند الدخول للشاشة"""
        app = App.get_running_app()
        self.user_name = getattr(app, 'user_name', "مستخدم")
        Logger.info("Dashboard: Screen active")
    
    def update_time(self, dt=None):
        self.current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def go_to_screen(self, screen_name):
        """الدالة الموحدة للانتقال بين الشاشات"""
        try:
            if screen_name in self.manager.screen_names:
                self.manager.current = screen_name
            else:
                Logger.error(f"Dashboard: Screen '{screen_name}' not found!")
        except Exception as e:
            Logger.error(f"Dashboard Navigation Error: {e}")

    def logout(self):
        self.go_to_screen('login')