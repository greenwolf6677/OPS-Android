"""
OPS Sales By User Report Screen
شاشة تقرير المبيعات حسب المستخدم
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.clock import Clock
from kivy.logger import Logger

import sqlite3
import re
from datetime import datetime, date, timedelta
from database import get_db_connection


class SalesByUserItem(BoxLayout):
    """عنصر مبيعات مستخدم في القائمة"""
    rank = NumericProperty(0)
    user_name = StringProperty("")
    invoices_count = NumericProperty(0)
    items_count = NumericProperty(0)
    total_sales = NumericProperty(0)
    avg_per_invoice = NumericProperty(0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 45
        self.padding = [5, 5]
        self.spacing = 5


class InvoiceDetailItem(BoxLayout):
    """عنصر تفاصيل فاتورة في القائمة"""
    date = StringProperty("")
    invoice_id = StringProperty("")
    total = NumericProperty(0)
    items_count = NumericProperty(0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 40
        self.padding = [5, 5]
        self.spacing = 5


class SalesByUserRecycleView(RecycleView):
    """عرض قائمة المبيعات حسب المستخدم"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data = []
        self.layout_manager = RecycleBoxLayout(
            default_size=(None, 45),
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


class SalesByUserReportScreen(Screen):
    """شاشة تقرير المبيعات حسب المستخدم"""
    
    # متغيرات الفلترة
    start_date = StringProperty("")
    end_date = StringProperty("")
    selected_user = StringProperty("جميع المستخدمين")
    
    # متغيرات الإحصائيات
    total_sales = StringProperty("₪ 0.00")
    total_invoices = StringProperty("0")
    total_items = StringProperty("0")
    
    # قائمة المستخدمين
    users_list = []
    users_dict = {}
    
    # حالة التحميل
    loading = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        today = date.today()
        self.start_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
        self.end_date = today.strftime("%Y-%m-%d")
        self.load_users()
        self.load_report()
    
    def on_enter(self):
        """عند دخول الشاشة"""
        self.load_report()
        Logger.info("OPS Sales By User Report: Screen entered")
    
    def load_users(self):
        """تحميل قائمة المستخدمين"""
        try:
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT id, username, full_name FROM users ORDER BY username")
            users = c.fetchall()
            conn.close()
            
            self.users_list = ["جميع المستخدمين"]
            for u in users:
                name = u['full_name'] or u['username']
                self.users_list.append(f"{name} (ID:{u['id']})")
                self.users_dict[name] = u['id']
            
            Logger.info(f"OPS Sales By User Report: Loaded {len(users)} users")
            
        except Exception as e:
            Logger.error(f"OPS Sales By User Report: Error loading users - {e}")
    
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
            self.users_list.data = []
            self.invoice_details_list.data = []
            
            start = self.start_date
            end = self.end_date
            
            # استخراج معرف المستخدم
            user_id = None
            if self.selected_user != "جميع المستخدمين":
                match = re.search(r'ID:(\d+)', self.selected_user)
                if match:
                    user_id = int(match.group(1))
            
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            query = """
                SELECT 
                    s.user_id,
                    COALESCE(u.full_name, u.username, 'غير معروف') as user_name,
                    COUNT(DISTINCT s.invoice_id) as invoices_count,
                    SUM(s.quantity) as items_count,
                    SUM(s.total) as total_sales
                FROM sales s
                LEFT JOIN users u ON s.user_id = u.id
                WHERE date(s.date) BETWEEN date(?) AND date(?)
            """
            params = [start, end]
            
            if user_id:
                query += " AND s.user_id = ?"
                params.append(user_id)
            
            query += " GROUP BY s.user_id ORDER BY total_sales DESC"
            
            try:
                c.execute(query, params)
                results = c.fetchall()
                
                data = []
                total_sales_sum = 0
                total_invoices_sum = 0
                total_items_sum = 0
                
                for i, row in enumerate(results, 1):
                    avg_per_invoice = row['total_sales'] / row['invoices_count'] if row['invoices_count'] > 0 else 0
                    data.append({
                        'rank': i,
                        'user_name': row['user_name'],
                        'invoices_count': row['invoices_count'],
                        'items_count': row['items_count'],
                        'total_sales': row['total_sales'],
                        'avg_per_invoice': avg_per_invoice
                    })
                    total_sales_sum += row['total_sales']
                    total_invoices_sum += row['invoices_count']
                    total_items_sum += row['items_count']
                
                self.users_list.data = data
                self.total_sales = f"₪ {total_sales_sum:.2f}"
                self.total_invoices = str(total_invoices_sum)
                self.total_items = str(total_items_sum)
                
                Logger.info(f"OPS Sales By User Report: Loaded {len(data)} users")
                
            except sqlite3.OperationalError as e:
                if "no such column: s.user_id" in str(e):
                    self.show_popup("تنبيه", "عمود user_id غير موجود في جدول sales. يرجى تحديث قاعدة البيانات.")
                else:
                    raise e
            
            conn.close()
            
        except Exception as e:
            Logger.error(f"OPS Sales By User Report: Error loading report - {e}")
            self.show_popup("خطأ", f"حدث خطأ: {str(e)}")
        finally:
            self.loading = False
    
    def on_user_select(self, user_name):
        """عند اختيار مستخدم من القائمة"""
        self.selected_user = user_name
        self.load_report()
    
    def load_invoice_details(self, user_name):
        """تحميل تفاصيل فواتير المستخدم"""
        try:
            # استخراج معرف المستخدم من الاسم
            user_id = None
            if user_name != "جميع المستخدمين":
                # البحث عن معرف المستخدم
                for u in self.users_list:
                    if u.startswith(user_name):
                        match = re.search(r'ID:(\d+)', u)
                        if match:
                            user_id = int(match.group(1))
                            break
            
            start = self.start_date
            end = self.end_date
            
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            if user_id:
                query = """
                    SELECT 
                        s.date,
                        s.invoice_id,
                        SUM(s.total) as total,
                        COUNT(s.barcode) as items_count
                    FROM sales s
                    WHERE s.user_id = ? AND date(s.date) BETWEEN date(?) AND date(?)
                    GROUP BY s.invoice_id
                    ORDER BY s.date DESC
                """
                c.execute(query, (user_id, start, end))
            else:
                query = """
                    SELECT 
                        date,
                        invoice_id,
                        SUM(total) as total,
                        COUNT(barcode) as items_count
                    FROM sales
                    WHERE date(date) BETWEEN date(?) AND date(?)
                    GROUP BY invoice_id
                    ORDER BY date DESC
                    LIMIT 50
                """
                c.execute(query, (start, end))
            
            details = c.fetchall()
            
            data = []
            for row in details:
                data.append({
                    'date': row['date'],
                    'invoice_id': row['invoice_id'],
                    'total': row['total'],
                    'items_count': row['items_count']
                })
            
            self.invoice_details_list.data = data
            conn.close()
            
        except Exception as e:
            Logger.error(f"OPS Sales By User Report: Error loading invoice details - {e}")
    
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