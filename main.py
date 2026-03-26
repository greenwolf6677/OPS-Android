"""
OPS (Orders Processing System) - Android Version
نظام معالجة الطلبات - إصدار أندرويد 2026
المعدل ليحتوي على نظام اقتناص الأخطاء (Error Catcher)
"""

import os
import traceback
import sys
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.core.window import Window
from kivy.resources import resource_add_path
from kivy.lang import Builder
from kivy.utils import platform
from kivy.core.text import LabelBase
from kivy.logger import Logger
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

# مكتبات معالجة اللغة العربية
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
except ImportError:
    Logger.warning("OPS: Arabic reshaper or bidi not found.")

# إعدادات التطبيق
APP_NAME = "OPS"
APP_VERSION = "1.0.0"

# --- تعديل الأذونات لأندرويد الحديث ---
if platform == 'android':
    from android.permissions import request_permissions, Permission
    request_permissions([
        Permission.INTERNET,
        Permission.CAMERA,
        Permission.READ_EXTERNAL_STORAGE,
        Permission.WRITE_EXTERNAL_STORAGE
    ])

BASE_PATH = os.path.dirname(os.path.abspath(__file__))

# إضافة مسارات الموارد
resource_add_path(BASE_PATH)
resource_add_path(os.path.join(BASE_PATH, 'kv'))
resource_add_path(os.path.join(BASE_PATH, 'assets'))

# تسجيل الخط العربي
FONT_PATH = os.path.join(BASE_PATH, 'assets', 'fonts', 'arial.ttf')
if os.path.exists(FONT_PATH):
    try:
        LabelBase.register(name='ArabicFont', fn_regular=FONT_PATH)
        Logger.info("OPS: Arabic font registered successfully.")
    except Exception as e:
        Logger.error(f"OPS: Font registration failed: {e}")

# تحميل ملفات KV تلقائياً
KV_PATH = os.path.join(BASE_PATH, 'kv')
if os.path.exists(KV_PATH):
    for kv_file in sorted(os.listdir(KV_PATH)):
        if kv_file.endswith('.kv'):
            try:
                Builder.load_file(os.path.join(KV_PATH, kv_file))
            except Exception as e:
                Logger.error(f"OPS: Error loading {kv_file}: {e}")

# استيراد المكونات
from database import init_db
from security.android_security import run_security
from screens.login_screen import LoginScreen
from screens.dashboard_screen import DashboardScreen
from screens.orders_screen import OrdersScreen
from screens.products_screen import ProductsScreen
from screens.customers_screen import CustomersScreen
from screens.returns_screen import ReturnsScreen
from screens.reports_screen import ReportsScreen, DailySalesReportScreen
from screens.about_page_screen import AboutPageScreen
from screens.purchases_screen import PurchasesScreen
from screens.suppliers_screen import SuppliersScreen
from screens.users_management_screen import UsersManagementScreen
from screens.license_screen import LicenseScreen

# استيراد شاشات التقارير والزبائن والموردين
from screens.top_products_report_screen import TopProductsReportScreen
from screens.bottom_products_report_screen import BottomProductsReportScreen
from screens.profit_report_screen import ProfitReportScreen
from screens.debt_report_screen import DebtReportScreen
from screens.sales_by_user_report_screen import SalesByUserReportScreen
from screens.payment_method_report_screen import PaymentMethodReportScreen
from screens.purchases_report_screen import PurchasesReportScreen
from screens.inventory_report_screen import Inventory_report_screen
from screens.customer_invoices_screen import CustomerInvoicesScreen
from screens.customer_payments_screen import CustomerPaymentsScreen
from screens.customer_account_screen import CustomerAccountScreen
from screens.supplier_invoices_screen import SupplierInvoicesScreen
from screens.supplier_payments_screen import SupplierPaymentsScreen
from screens.supplier_account_screen import SupplierAccountScreen

class OPSApp(App):
    def build(self):
        try:
            is_valid, _ = run_security()
        except:
            is_valid = False 

        if platform == 'android':
            Window.fullscreen = 'auto'
        else:
            Window.size = (1200, 800)

        self.screen_manager = ScreenManager()
        
        screens_list = [
            (LicenseScreen, 'license'),
            (LoginScreen, 'login'),
            (DashboardScreen, 'dashboard'),
            (OrdersScreen, 'orders'),
            (ProductsScreen, 'products'),
            (CustomersScreen, 'customers'),
            (ReturnsScreen, 'returns'),
            (ReportsScreen, 'reports'),
            (UsersManagementScreen, 'users_management'),
            (AboutPageScreen, 'about'),
            (PurchasesScreen, 'purchases'),
            (SuppliersScreen, 'suppliers'),
            (DailySalesReportScreen, 'daily_sales_report'),
            (TopProductsReportScreen, 'top_products_report'),
            (BottomProductsReportScreen, 'bottom_products_report'),
            (ProfitReportScreen, 'profit_report'),
            (DebtReportScreen, 'debt_report'),
            (SalesByUserReportScreen, 'sales_by_user_report'),
            (PaymentMethodReportScreen, 'payment_method_report'),
            (PurchasesReportScreen, 'purchases_report'),
            (Inventory_report_screen, 'inventory_report'),
            (CustomerInvoicesScreen, 'customer_invoices'),
            (CustomerPaymentsScreen, 'customer_payments'),
            (CustomerAccountScreen, 'customer_account'),
            (SupplierInvoicesScreen, 'supplier_invoices'),
            (SupplierPaymentsScreen, 'supplier_payments'),
            (SupplierAccountScreen, 'supplier_account')
        ]

        for screen_class, s_name in screens_list:
            self.screen_manager.add_widget(screen_class(name=s_name))

        self.screen_manager.current = 'login' if is_valid else 'license'
        return self.screen_manager

    def on_start(self):
        try:
            init_db()
            Logger.info("OPS: Database initialized on start.")
        except Exception as e:
            Logger.error(f"OPS: Database initialization failed: {e}")

def show_critical_error(error_text):
    """دالة طوارئ لعرض الخطأ التقني على شاشة الهاتف مباشرة"""
    Logger.error(f"OPS_FATAL: {error_text}")
    
    # محاولة بناء واجهة بسيطة جداً لعرض الخطأ
    root = ScrollView(size_hint=(1, 1))
    content = Label(
        text=f"CRITICAL ERROR:\n\n{error_text}",
        size_hint_y=None,
        color=(1, 0, 0, 1),
        font_size='14sp',
        halign='left',
        valign='top',
        padding=(20, 20)
    )
    content.bind(texture_size=content.setter('size'))
    root.add_widget(content)
    
    # تشغيل تطبيق طوارئ لعرض الخطأ فقط
    class ErrorApp(App):
        def build(self):
            return root
    
    ErrorApp().run()

if __name__ == '__main__':
    try:
        OPSApp().run()
    except Exception:
        # التقاط الخطأ الكامل وتحويله لنص
        error_info = traceback.format_exc()
        # إظهار نافذة الخطأ بدلاً من الخروج الصامت
        show_critical_error(error_info)