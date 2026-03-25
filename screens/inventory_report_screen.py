"""
OPS Inventory Movement Report Screen
شاشة تقرير حركة المخزون
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.logger import Logger

import sqlite3
from datetime import datetime, date, timedelta
from database import get_db_connection


class InventoryMovementItem(BoxLayout):
    """عنصر حركة مخزون في القائمة"""
    date = StringProperty("")
    product = StringProperty("")
    type = StringProperty("")
    qty = NumericProperty(0)
    price = NumericProperty(0)
    total = NumericProperty(0)
    reference = StringProperty("")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 45
        self.padding = [5, 5]
        self.spacing = 5


class InventoryRecycleView(RecycleView):
    """عرض قائمة حركات المخزون"""
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


class InventoryReportScreen(Screen):
    """شاشة تقرير حركة المخزون"""
    
    # متغيرات الفلترة
    start_date = StringProperty("")
    end_date = StringProperty("")
    product_filter = StringProperty("")
    
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
        Logger.info("OPS Inventory Report: Screen entered")
    
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
            self.movements_list.data = []
            
            start = self.start_date
            end = self.end_date
            product_filter = self.product_filter.strip()
            
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            data = []
            
            # جلب حركات المبيعات
            sales_query = """
                SELECT 
                    s.date,
                    COALESCE(p.name, 'منتج غير معروف') as product_name,
                    'مبيعات' as type,
                    s.quantity as qty,
                    s.price,
                    s.total,
                    c.name as reference
                FROM sales s
                LEFT JOIN products p ON s.barcode = p.barcode
                LEFT JOIN customers c ON s.customer_id = c.id
                WHERE date(s.date) BETWEEN date(?) AND date(?)
            """
            params = [start, end]
            if product_filter:
                sales_query += " AND p.name LIKE ?"
                params.append(f"%{product_filter}%")
            
            c.execute(sales_query, params)
            for row in c.fetchall():
                data.append({
                    'date': row['date'],
                    'product': row['product_name'],
                    'type': row['type'],
                    'qty': row['qty'],
                    'price': row['price'],
                    'total': row['total'],
                    'reference': row['reference'] or "غير محدد"
                })
            
            # جلب حركات المشتريات
            purchases_query = """
                SELECT 
                    p.date,
                    pr.name as product_name,
                    'مشتريات' as type,
                    pi.quantity as qty,
                    pi.buy_price as price,
                    pi.subtotal as total,
                    s.name as reference
                FROM purchase_items pi
                JOIN purchases p ON pi.purchase_id = p.id
                LEFT JOIN products pr ON pi.barcode = pr.barcode
                LEFT JOIN suppliers s ON p.supplier_id = s.id
                WHERE date(p.date) BETWEEN date(?) AND date(?)
            """
            params2 = [start, end]
            if product_filter:
                purchases_query += " AND pr.name LIKE ?"
                params2.append(f"%{product_filter}%")
            
            c.execute(purchases_query, params2)
            for row in c.fetchall():
                data.append({
                    'date': row['date'],
                    'product': row['product_name'] or "منتج غير معروف",
                    'type': row['type'],
                    'qty': row['qty'],
                    'price': row['price'],
                    'total': row['total'],
                    'reference': row['reference'] or "غير محدد"
                })
            
            # ترتيب حسب التاريخ
            data.sort(key=lambda x: x['date'], reverse=True)
            
            # تحويل البيانات إلى صيغة العرض
            display_data = []
            for item in data:
                display_data.append({
                    'date': item['date'],
                    'product': item['product'],
                    'type': item['type'],
                    'qty': item['qty'],
                    'price': item['price'],
                    'total': item['total'],
                    'reference': item['reference']
                })
            
            self.movements_list.data = display_data
            conn.close()
            Logger.info(f"OPS Inventory Report: Loaded {len(display_data)} movements")
            
        except Exception as e:
            Logger.error(f"OPS Inventory Report: Error loading report - {e}")
            self.show_popup("خطأ", f"حدث خطأ: {str(e)}")
        finally:
            self.loading = False
    
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