"""
OPS Purchases Report Screen
شاشة تقرير المشتريات
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
from kivy.logger import Logger

import sqlite3
from datetime import datetime, date, timedelta
from database import get_db_connection


class PurchaseItem(BoxLayout):
    """عنصر فاتورة شراء في القائمة"""
    date = StringProperty("")
    supplier = StringProperty("")
    total = NumericProperty(0)
    items_count = NumericProperty(0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 45
        self.padding = [5, 5]
        self.spacing = 5


class PurchaseDetailItem(BoxLayout):
    """عنصر تفاصيل فاتورة شراء في القائمة"""
    purchase_id = NumericProperty(0)
    product = StringProperty("")
    quantity = NumericProperty(0)
    price = NumericProperty(0)
    subtotal = NumericProperty(0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 40
        self.padding = [5, 5]
        self.spacing = 5


class PurchasesRecycleView(RecycleView):
    """عرض قائمة المشتريات"""
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


class PurchaseDetailsRecycleView(RecycleView):
    """عرض تفاصيل المشتريات"""
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


class PurchasesReportScreen(Screen):
    """شاشة تقرير المشتريات"""
    
    # متغيرات الفلترة
    start_date = StringProperty("")
    end_date = StringProperty("")
    
    # متغيرات الإحصائيات
    total_purchases = StringProperty("₪ 0.00")
    total_items = StringProperty("0")
    total_invoices = StringProperty("0")
    
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
        Logger.info("OPS Purchases Report: Screen entered")
    
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
            self.purchases_list.data = []
            self.purchase_details_list.data = []
            
            start = self.start_date
            end = self.end_date
            
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            query = """
                SELECT 
                    p.id,
                    p.date,
                    s.name as supplier_name,
                    p.total,
                    (SELECT COUNT(*) FROM purchase_items WHERE purchase_id = p.id) as items_count
                FROM purchases p
                LEFT JOIN suppliers s ON p.supplier_id = s.id
                WHERE date(p.date) BETWEEN date(?) AND date(?)
                ORDER BY p.date DESC
            """
            c.execute(query, (start, end))
            purchases = c.fetchall()
            
            data = []
            total_purchases_sum = 0
            total_items_sum = 0
            total_invoices_sum = 0
            
            for row in purchases:
                data.append({
                    'date': row['date'],
                    'supplier': row['supplier_name'] or "غير محدد",
                    'total': row['total'],
                    'items_count': row['items_count']
                })
                total_purchases_sum += row['total']
                total_items_sum += row['items_count']
                total_invoices_sum += 1
            
            self.purchases_list.data = data
            self.total_purchases = f"₪ {total_purchases_sum:.2f}"
            self.total_items = str(total_items_sum)
            self.total_invoices = str(total_invoices_sum)
            
            conn.close()
            Logger.info(f"OPS Purchases Report: Loaded {len(data)} purchases")
            
        except Exception as e:
            Logger.error(f"OPS Purchases Report: Error loading report - {e}")
            self.show_popup("خطأ", f"حدث خطأ: {str(e)}")
        finally:
            self.loading = False
    
    def load_purchase_details(self, purchase_date, purchase_total):
        """تحميل تفاصيل فاتورة الشراء"""
        try:
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            # البحث عن purchase_id باستخدام التاريخ
            query = """
                SELECT 
                    pi.purchase_id,
                    p.name as product_name,
                    pi.quantity,
                    pi.buy_price,
                    pi.subtotal
                FROM purchase_items pi
                LEFT JOIN products p ON pi.barcode = p.barcode
                WHERE pi.purchase_id = (
                    SELECT id FROM purchases WHERE date = ? AND total = ? LIMIT 1
                )
                ORDER BY pi.id
            """
            c.execute(query, (purchase_date, purchase_total))
            details = c.fetchall()
            
            data = []
            for row in details:
                data.append({
                    'purchase_id': row['purchase_id'],
                    'product': row['product_name'] or "منتج غير معروف",
                    'quantity': row['quantity'],
                    'price': row['buy_price'],
                    'subtotal': row['subtotal']
                })
            
            self.purchase_details_list.data = data
            conn.close()
            
        except Exception as e:
            Logger.error(f"OPS Purchases Report: Error loading purchase details - {e}")
    
    def on_purchase_select(self, purchase_date, purchase_total):
        """عند اختيار فاتورة شراء من القائمة"""
        self.load_purchase_details(purchase_date, purchase_total)
    
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