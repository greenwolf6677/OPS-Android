"""
OPS Customer Invoices Screen
شاشة عرض فواتير الزبون لنظام OPS
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.properties import StringProperty, NumericProperty, ObjectProperty
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.core.clipboard import Clipboard

import sqlite3
from datetime import datetime
from database import get_db_connection


class InvoiceItem(BoxLayout):
    """عنصر فاتورة في القائمة"""
    invoice_id = StringProperty("")
    date = StringProperty("")
    total = StringProperty("")
    payment_method = StringProperty("")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 50
        self.padding = [5, 5]
        self.spacing = 5


class InvoicesRecycleView(RecycleView):
    """عرض قائمة الفواتير"""
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


class CustomerInvoicesScreen(Screen):
    """شاشة عرض فواتير الزبون"""
    
    customer_id = NumericProperty(0)
    customer_name = StringProperty("")
    selected_invoice_id = StringProperty("")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.invoices_data = []
        
    def set_customer(self, customer_id, customer_name):
        """تعيين الزبون وعرض فواتيره"""
        self.customer_id = customer_id
        self.customer_name = customer_name
        self.load_invoices()
        
    def on_enter(self):
        """عند دخول الشاشة"""
        if self.customer_id:
            self.load_invoices()
    
    def load_invoices(self):
        """تحميل فواتير الزبون"""
        try:
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            c.execute("""
                SELECT invoice_id, date, SUM(total) as total, payment_method 
                FROM sales 
                WHERE customer_id = ? 
                GROUP BY invoice_id
                ORDER BY date DESC
            """, (self.customer_id,))
            
            invoices = c.fetchall()
            conn.close()
            
            data = []
            for row in invoices:
                data.append({
                    'invoice_id': row['invoice_id'],
                    'date': row['date'],
                    'total': f"{row['total']:.2f} ₪",
                    'payment_method': row['payment_method']
                })
            
            self.invoices_list.data = data
            self.invoices_data = data
            Logger.info(f"OPS Customer Invoices: Loaded {len(data)} invoices for customer {self.customer_name}")
            
        except Exception as e:
            Logger.error(f"OPS Customer Invoices: Error loading invoices - {e}")
            self.show_popup("خطأ", f"حدث خطأ: {str(e)}")
    
    def select_invoice(self, invoice_id):
        """تحديد فاتورة لعرض تفاصيلها"""
        self.selected_invoice_id = invoice_id
        self.load_invoice_details()
    
    def load_invoice_details(self):
        """تحميل تفاصيل الفاتورة المحددة"""
        if not self.selected_invoice_id:
            return
        
        try:
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            c.execute("""
                SELECT s.quantity, s.price, s.total, COALESCE(p.name, 'منتج غير معروف') as name 
                FROM sales s 
                LEFT JOIN products p ON s.barcode = p.barcode 
                WHERE s.invoice_id = ?
            """, (self.selected_invoice_id,))
            
            details = c.fetchall()
            conn.close()
            
            # عرض التفاصيل في popup
            self.show_invoice_details_popup(details)
            
        except Exception as e:
            Logger.error(f"OPS Customer Invoices: Error loading invoice details - {e}")
            self.show_popup("خطأ", f"حدث خطأ: {str(e)}")
    
    def show_invoice_details_popup(self, details):
        """عرض نافذة تفاصيل الفاتورة"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # رأس الجدول
        header = BoxLayout(size_hint_y=None, height=40, spacing=5)
        header.add_widget(Label(text="اسم المنتج", font_name='ArabicFont', size_hint_x=0.5))
        header.add_widget(Label(text="الكمية", font_name='ArabicFont', size_hint_x=0.15))
        header.add_widget(Label(text="السعر", font_name='ArabicFont', size_hint_x=0.15))
        header.add_widget(Label(text="الإجمالي", font_name='ArabicFont', size_hint_x=0.2))
        content.add_widget(header)
        
        # بيانات التفاصيل
        for row in details:
            item_row = BoxLayout(size_hint_y=None, height=35, spacing=5)
            item_row.add_widget(Label(text=row['name'], font_name='ArabicFont', size_hint_x=0.5, halign='right'))
            item_row.add_widget(Label(text=str(row['quantity']), font_name='ArabicFont', size_hint_x=0.15))
            item_row.add_widget(Label(text=f"{row['price']:.2f}", font_name='ArabicFont', size_hint_x=0.15))
            item_row.add_widget(Label(text=f"{row['total']:.2f}", font_name='ArabicFont', size_hint_x=0.2))
            content.add_widget(item_row)
        
        # زر الإغلاق
        btn = Button(text="إغلاق", size_hint_y=0.1, font_name='ArabicFont')
        popup = Popup(title=f"تفاصيل الفاتورة {self.selected_invoice_id}", 
                      content=content, size_hint=(0.8, 0.8))
        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        
        popup.open()
    
    def go_back(self):
        """العودة لشاشة الزبائن"""
        self.manager.current = 'customers'
    
    def show_popup(self, title, message):
        """عرض نافذة منبثقة"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=message, font_name='ArabicFont', halign='center'))
        
        btn = Button(text="موافق", size_hint_y=0.3, font_name='ArabicFont')
        popup = Popup(title=title, content=content, size_hint=(0.7, 0.4))
        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        
        popup.open()