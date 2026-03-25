"""
OPS Payment Method Report Screen
شاشة تقرير المبيعات حسب طريقة الدفع
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.logger import Logger

import sqlite3
from datetime import datetime, date, timedelta
from database import get_db_connection


class PaymentMethodItem(BoxLayout):
    """عنصر طريقة دفع في القائمة"""
    method = StringProperty("")
    total_sales = NumericProperty(0)
    total_amount = NumericProperty(0)
    percentage = NumericProperty(0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 50
        self.padding = [5, 5]
        self.spacing = 5


class InvoiceDetailItem(BoxLayout):
    """عنصر تفاصيل فاتورة في القائمة"""
    date = StringProperty("")
    invoice_id = StringProperty("")
    customer = StringProperty("")
    total = NumericProperty(0)
    items_count = NumericProperty(0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 40
        self.padding = [5, 5]
        self.spacing = 5


class PaymentMethodRecycleView(RecycleView):
    """عرض قائمة طرق الدفع"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data = []
        self.layout_manager = RecycleBoxLayout(
            default_size=(None, 50),
            default_size_hint=(1, None),
            size_hint_y=None,
            height=self.minimum_height,
            orientation='vertical'
        )
        self.add_widget(self.layout_manager)


class InvoiceDetailsRecycleView(RecycleView):
    """عرض تفاصيل الفواتير"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data = []
        self.layout_manager = RecycleBoxLayout(
            default_size=(None, 40),
            default_size_hint=(1, None),
            size_hint_y=None,
            height=self.minimum_height,
            orientation='vertical'
        )
        self.add_widget(self.layout_manager)


class PaymentMethodReportScreen(Screen):
    """شاشة تقرير المبيعات حسب طريقة الدفع"""
    
    # متغيرات الفلترة
    start_date = StringProperty("")
    end_date = StringProperty("")
    
    # حالة التحميل
    loading = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        today = date.today()
        self.start_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
        self.end_date = today.strftime("%Y-%m-%d")
        self.load_report()
    
    def on_enter(self):
        """عند دخول الشاشة"""
        self.load_report()
        Logger.info("OPS Payment Method Report: Screen entered")
    
    def open_start_date_picker(self):
        """فتح منتقي تاريخ البداية"""
        self._open_date_picker(is_start=True)
    
    def open_end_date_picker(self):
        """فتح منتقي تاريخ النهاية"""
        self._open_date_picker(is_start=False)
    
    def _open_date_picker(self, is_start=True):
        """فتح منتقي التاريخ"""
        from kivy.uix.calendar import CalendarWidget
        
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        calendar = CalendarWidget()
        content.add_widget(calendar)
        
        buttons = BoxLayout(size_hint_y=None, height=50, spacing=10)
        btn_ok = Button(text="تأكيد", font_name='ArabicFont', background_color=(0.2, 0.6, 0.2, 1))
        btn_cancel = Button(text="إلغاء", font_name='ArabicFont', background_color=(0.6, 0.2, 0.2, 1))
        buttons.add_widget(btn_ok)
        buttons.add_widget(btn_cancel)
        content.add_widget(buttons)
        
        popup = Popup(title="اختر التاريخ", content=content, size_hint=(0.8, 0.8))
        
        def set_date(instance):
            selected_date = calendar.get_selected_date()
            if selected_date:
                if is_start:
                    self.start_date = selected_date.strftime("%Y-%m-%d")
                else:
                    self.end_date = selected_date.strftime("%Y-%m-%d")
            popup.dismiss()
        
        btn_ok.bind(on_press=set_date)
        btn_cancel.bind(on_press=popup.dismiss)
        
        popup.open()
    
    def load_report(self):
        """تحميل بيانات التقرير"""
        self.loading = True
        try:
            self.payment_methods_list.data = []
            self.invoice_details_list.data = []
            
            start = self.start_date
            end = self.end_date
            
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            query = """
                SELECT 
                    payment_method,
                    COUNT(DISTINCT invoice_id) as total_sales,
                    SUM(total) as total_amount,
                    (SUM(total) * 100.0 / (SELECT SUM(total) FROM sales WHERE date(date) BETWEEN date(?) AND date(?))) as percentage
                FROM sales
                WHERE date(date) BETWEEN date(?) AND date(?)
                GROUP BY payment_method
                ORDER BY total_amount DESC
            """
            c.execute(query, (start, end, start, end))
            results = c.fetchall()
            
            data = []
            for row in results:
                data.append({
                    'method': row['payment_method'],
                    'total_sales': row['total_sales'],
                    'total_amount': row['total_amount'],
                    'percentage': row['percentage'] or 0
                })
            
            self.payment_methods_list.data = data
            Logger.info(f"OPS Payment Method Report: Loaded {len(data)} payment methods")
            
            conn.close()
            
        except Exception as e:
            Logger.error(f"OPS Payment Method Report: Error loading report - {e}")
            self.show_popup("خطأ", f"حدث خطأ: {str(e)}")
        finally:
            self.loading = False
    
    def load_invoice_details(self, payment_method):
        """تحميل تفاصيل فواتير طريقة الدفع المحددة"""
        try:
            start = self.start_date
            end = self.end_date
            
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            query = """
                SELECT 
                    date,
                    invoice_id,
                    COALESCE(c.name, 'غير محدد') as customer_name,
                    SUM(total) as total,
                    COUNT(DISTINCT barcode) as items_count
                FROM sales s
                LEFT JOIN customers c ON s.customer_id = c.id
                WHERE payment_method = ? AND date(date) BETWEEN date(?) AND date(?)
                GROUP BY invoice_id
                ORDER BY date DESC
                LIMIT 50
            """
            c.execute(query, (payment_method, start, end))
            details = c.fetchall()
            
            data = []
            for row in details:
                data.append({
                    'date': row['date'],
                    'invoice_id': row['invoice_id'],
                    'customer': row['customer_name'],
                    'total': row['total'],
                    'items_count': row['items_count']
                })
            
            self.invoice_details_list.data = data
            conn.close()
            
        except Exception as e:
            Logger.error(f"OPS Payment Method Report: Error loading invoice details - {e}")
    
    def on_method_select(self, method):
        """عند اختيار طريقة دفع من القائمة"""
        self.load_invoice_details(method)
    
    def go_back(self):
        """العودة لشاشة التقارير الرئيسية"""
        self.manager.current = 'reports'
    
    def show_popup(self, title, message):
        """عرض نافذة منبثقة"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=message, font_name='ArabicFont', halign='center', text_size=(400, None)))
        
        btn = Button(text="موافق", size_hint_y=0.3, font_name='ArabicFont')
        popup = Popup(title=title, content=content, size_hint=(0.8, 0.5))
        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        
        popup.open()