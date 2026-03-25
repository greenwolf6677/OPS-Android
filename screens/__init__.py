"""
OPS Screens Module
"""

from .login_screen import LoginScreen
from .dashboard_screen import DashboardScreen
from .orders_screen import OrdersScreen
from .products_screen import ProductsScreen
from .customers_screen import CustomersScreen
from .returns_screen import ReturnsScreen
from .reports_screen import ReportsScreen, DailySalesReportScreen
from .about_page_screen import AboutPageScreen
from .purchases_screen import PurchasesScreen
from .suppliers_screen import SuppliersScreen
from .users_management_screen import UsersManagementScreen  # هذا هو مكان الإعدادات
from .license_screen import LicenseScreen

# شاشات التقارير الإضافية
from .top_products_report_screen import TopProductsReportScreen
from .bottom_products_report_screen import BottomProductsReportScreen
from .profit_report_screen import ProfitReportScreen
from .debt_report_screen import DebtReportScreen
from .sales_by_user_report_screen import SalesByUserReportScreen
from .payment_method_report_screen import PaymentMethodReportScreen
from .purchases_report_screen import PurchasesReportScreen
from .inventory_report_screen import InventoryReportScreen

# شاشات الزبائن الفرعية
from .customer_invoices_screen import CustomerInvoicesScreen
from .customer_payments_screen import CustomerPaymentsScreen
from .customer_account_screen import CustomerAccountScreen

# شاشات الموردين الفرعية
from .supplier_invoices_screen import SupplierInvoicesScreen
from .supplier_payments_screen import SupplierPaymentsScreen
from .supplier_account_screen import SupplierAccountScreen


__all__ = [
    # الشاشات الرئيسية
    'LoginScreen',
    'DashboardScreen',
    'OrdersScreen',
    'ProductsScreen',
    'CustomersScreen',
    'ReturnsScreen',
    'ReportsScreen',
    'DailySalesReportScreen',
    'AboutPageScreen',
    'PurchasesScreen',
    'SuppliersScreen',
    'UsersManagementScreen',  # الإدارة والإعدادات
    'LicenseScreen',
    
    # تقارير إضافية
    'TopProductsReportScreen',
    'BottomProductsReportScreen',
    'ProfitReportScreen',
    'DebtReportScreen',
    'SalesByUserReportScreen',
    'PaymentMethodReportScreen',
    'PurchasesReportScreen',
    'InventoryReportScreen',
    
    # شاشات الزبائن الفرعية
    'CustomerInvoicesScreen',
    'CustomerPaymentsScreen',
    'CustomerAccountScreen',
    
    # شاشات الموردين الفرعية
    'SupplierInvoicesScreen',
    'SupplierPaymentsScreen',
    'SupplierAccountScreen',
]