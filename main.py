"""
OPS (Orders Processing System) - Android Version
نظام معالجة الطلبات - إصدار أندرويد
الإصدار 1.0.0
"""

import os
import sys
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.resources import resource_add_path
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.utils import platform
from kivy.core.text import LabelBase
from kivy.logger import Logger

# إعدادات التطبيق
APP_NAME = "OPS"
APP_VERSION = "1.0.0"
APP_TITLE = "OPS - Orders Processing System"

# تحديد المسار الأساسي
if platform == 'android':
    from android.permissions import request_permissions, Permission
    from android.storage import primary_external_storage_path
    from jnius import autoclass
    
    # طلب الأذونات
    request_permissions([
        Permission.READ_EXTERNAL_STORAGE,
        Permission.WRITE_EXTERNAL_STORAGE,
        Permission.INTERNET
    ])
    
    BASE_PATH = primary_external_storage_path()
    Logger.info(f"OPS: Running on Android, base path: {BASE_PATH}")
else:
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))
    Logger.info(f"OPS: Running on Desktop, base path: {BASE_PATH}")

# إضافة مسار الخط العربي
FONT_PATH = os.path.join(BASE_PATH, 'assets', 'fonts', 'arial.ttf')
if os.path.exists(FONT_PATH):
    LabelBase.register(name='ArabicFont', fn_regular=FONT_PATH)
    DEFAULT_FONT = 'ArabicFont'
    Logger.info("OPS: Arabic font loaded successfully")
else:
    DEFAULT_FONT = 'Roboto'
    Logger.warning("OPS: Arabic font not found, using default font")

# تحميل ملفات KV
KV_PATH = os.path.join(BASE_PATH, 'kv')
if os.path.exists(KV_PATH):
    for kv_file in os.listdir(KV_PATH):
        if kv_file.endswith('.kv'):
            kv_full_path = os.path.join(KV_PATH, kv_file)
            try:
                Builder.load_file(kv_full_path)
                Logger.info(f"OPS: Loaded KV file: {kv_file}")
            except Exception as e:
                Logger.error(f"OPS: Failed to load {kv_file}: {e}")

# استيراد الشاشات
from screens.login_screen import LoginScreen
from screens.dashboard_screen import DashboardScreen
from screens.orders_screen import OrdersScreen          # بدلاً من SalesScreen
from screens.products_screen import ProductsScreen
from screens.customers_screen import CustomersScreen
from screens.returns_screen import ReturnsScreen
from screens.reports_screen import ReportsScreen, DailySalesReportScreen
from screens.about_page_screen import AboutPageScreen
from screens.purchases_screen import PurchasesScreen
from screens.suppliers_screen import SuppliersScreen
from screens.users_management_screen import UsersManagementScreen   # بدلاً من SettingsScreen
from screens.license_screen import LicenseScreen

# شاشات التقارير الإضافية
from screens.top_products_report_screen import TopProductsReportScreen
from screens.bottom_products_report_screen import BottomProductsReportScreen
from screens.profit_report_screen import ProfitReportScreen
from screens.debt_report_screen import DebtReportScreen
from screens.sales_by_user_report_screen import SalesByUserReportScreen
from screens.payment_method_report_screen import PaymentMethodReportScreen
from screens.purchases_report_screen import PurchasesReportScreen
from screens.inventory_report_screen import InventoryReportScreen

# شاشات الزبائن الفرعية
from screens.customer_invoices_screen import CustomerInvoicesScreen
from screens.customer_payments_screen import CustomerPaymentsScreen
from screens.customer_account_screen import CustomerAccountScreen

# شاشات الموردين الفرعية
from screens.supplier_invoices_screen import SupplierInvoicesScreen
from screens.supplier_payments_screen import SupplierPaymentsScreen
from screens.supplier_account_screen import SupplierAccountScreen

# استيراد الـ Widgets
from widgets import CartItem, CustomButton, IconButton, ActionButton, DataTable

# استيراد وحدة الأمان
from security.android_security import run_security, get_license_info

# استيراد قاعدة البيانات
from database import init_db, get_db_connection, get_user_permissions


class OPSApp(App):
    """التطبيق الرئيسي لنظام OPS"""
    
    def build(self):
        # فحص الترخيص أولاً
        is_valid, license_message = run_security()
        
        # إعدادات النافذة
        if platform == 'android':
            Window.fullscreen = 'auto'
        else:
            Window.clearcolor = (0.95, 0.95, 0.95, 1)
            Window.size = (1200, 800)
        
        # إنشاء مدير الشاشات
        self.screen_manager = ScreenManager()
        
        # إضافة شاشة الترخيص (تضاف دائماً)
        self.screen_manager.add_widget(LicenseScreen(name='license'))
        
        if not is_valid:
            # إذا كان الترخيص غير صالح، نعرض شاشة الترخيص فقط
            Logger.warning(f"OPS: Invalid license - {license_message}")
            self.screen_manager.current = 'license'
        else:
            # إضافة باقي الشاشات (فقط إذا كان الترخيص صالحاً)
            self.screen_manager.add_widget(LoginScreen(name='login'))
            self.screen_manager.add_widget(DashboardScreen(name='dashboard'))
            self.screen_manager.add_widget(OrdersScreen(name='orders'))           # الطلبيات
            self.screen_manager.add_widget(ProductsScreen(name='products'))
            self.screen_manager.add_widget(CustomersScreen(name='customers'))
            self.screen_manager.add_widget(ReturnsScreen(name='returns'))
            self.screen_manager.add_widget(ReportsScreen(name='reports'))
            self.screen_manager.add_widget(UsersManagementScreen(name='users_management'))  # الإدارة والإعدادات
            self.screen_manager.add_widget(AboutPageScreen(name='about'))
            self.screen_manager.add_widget(PurchasesScreen(name='purchases'))
            self.screen_manager.add_widget(SuppliersScreen(name='suppliers'))
            
            # شاشات التقارير
            self.screen_manager.add_widget(DailySalesReportScreen(name='daily_sales_report'))
            self.screen_manager.add_widget(TopProductsReportScreen(name='top_products_report'))
            self.screen_manager.add_widget(BottomProductsReportScreen(name='bottom_products_report'))
            self.screen_manager.add_widget(ProfitReportScreen(name='profit_report'))
            self.screen_manager.add_widget(DebtReportScreen(name='debt_report'))
            self.screen_manager.add_widget(SalesByUserReportScreen(name='sales_by_user_report'))
            self.screen_manager.add_widget(PaymentMethodReportScreen(name='payment_method_report'))
            self.screen_manager.add_widget(PurchasesReportScreen(name='purchases_report'))
            self.screen_manager.add_widget(InventoryReportScreen(name='inventory_report'))
            
            # شاشات الزبائن الفرعية
            self.screen_manager.add_widget(CustomerInvoicesScreen(name='customer_invoices'))
            self.screen_manager.add_widget(CustomerPaymentsScreen(name='customer_payments'))
            self.screen_manager.add_widget(CustomerAccountScreen(name='customer_account'))
            
            # شاشات الموردين الفرعية
            self.screen_manager.add_widget(SupplierInvoicesScreen(name='supplier_invoices'))
            self.screen_manager.add_widget(SupplierPaymentsScreen(name='supplier_payments'))
            self.screen_manager.add_widget(SupplierAccountScreen(name='supplier_account'))
            
            # شاشة البداية
            self.screen_manager.current = 'login'
            
            Logger.info(f"OPS: License OK - Starting application")
        
        # تعيين المتغيرات العامة
        self.user_id = None
        self.user_role = None
        self.user_name = None
        
        return self.screen_manager
    
    def on_start(self):
        """عند بدء التطبيق"""
        Logger.info(f"{APP_TITLE} - Starting application")
        
        # تهيئة قاعدة البيانات (فقط إذا كان الترخيص صالحاً)
        try:
            init_db()
            Logger.info("OPS: Database initialized successfully")
        except Exception as e:
            Logger.error(f"OPS: Database initialization failed: {e}")
    
    def on_stop(self):
        """عند إغلاق التطبيق"""
        Logger.info(f"{APP_TITLE} - Closing application")
    
    def get_permissions(self):
        """الحصول على صلاحيات المستخدم الحالي"""
        if self.user_id:
            return get_user_permissions(self.user_id)
        return {
            'sales': True,
            'customers': True,
            'returns': True,
            'products': False,
            'reports': False,
            'settings': False,
            'users': False
        }


if __name__ == '__main__':
    OPSApp().run()