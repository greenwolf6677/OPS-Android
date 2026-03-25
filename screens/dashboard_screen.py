"""
OPS Dashboard Screen
شاشة لوحة التحكم الرئيسية
"""

from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, ListProperty
from kivy.clock import Clock
from datetime import datetime
from kivy.logger import Logger


class DashboardScreen(Screen):
    """شاشة لوحة التحكم الرئيسية"""
    
    user_name = StringProperty("")
    current_time = StringProperty("")
    store_name = StringProperty("OPS - Orders Processing System")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.update_time()
        Clock.schedule_interval(self.update_time, 1)
    
    def on_enter(self):
        """عند دخول الشاشة"""
        # الحصول على اسم المستخدم
        from kivy.app import App
        app = App.get_running_app()
        self.user_name = app.user_name if hasattr(app, 'user_name') else "مستخدم"
        Logger.info("OPS Dashboard: Screen entered")
    
    def update_time(self, dt=None):
        """تحديث الوقت"""
        self.current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def go_to_screen(self, screen_name):
        """الانتقال إلى شاشة محددة"""
        if screen_name in self.manager.screen_names:
            self.manager.current = screen_name
        else:
            Logger.warning(f"Dashboard: Screen '{screen_name}' not found")
    
    def logout(self):
        """تسجيل الخروج"""
        self.manager.current = 'login'
    
    def open_orders(self):
        """فتح شاشة الطلبيات"""
        self.go_to_screen('orders')
    
    def open_products(self):
        """فتح شاشة المنتجات"""
        self.go_to_screen('products')
    
    def open_customers(self):
        """فتح شاشة الزبائن"""
        self.go_to_screen('customers')
    
    def open_returns(self):
        """فتح شاشة المرتجعات"""
        self.go_to_screen('returns')
    
    def open_reports(self):
        """فتح شاشة التقارير"""
        self.go_to_screen('reports')
    
    def open_suppliers(self):
        """فتح شاشة الموردين"""
        self.go_to_screen('suppliers')
    
    def open_purchases(self):
        """فتح شاشة المشتريات"""
        self.go_to_screen('purchases')
    
    def open_settings(self):
        """فتح شاشة الإعدادات"""
        self.go_to_screen('users_management')
    
    def open_about(self):
        """فتح شاشة حول البرنامج"""
        self.go_to_screen('about')