"""
OPS Supplier Invoices Screen
شاشة عرض فواتير المورد
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.logger import Logger

import sqlite3
from datetime import datetime
from database import get_db_connection

# استيراد دوال PDF
try:
    from utils.pdf_generator import create_purchase_invoice_pdf
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    Logger.warning("OPS Supplier Invoices: PDF generator not available")


class InvoiceItem(BoxLayout):
    """عنصر فاتورة في القائمة"""
    purchase_id = NumericProperty(0)
    date = StringProperty("")
    total = NumericProperty(0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 45
        self.padding = [5, 5]
        self.spacing = 5


class InvoiceDetailItem(BoxLayout):
    """عنصر تفاصيل فاتورة في القائمة"""
    name = StringProperty("")
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


class InvoicesRecycleView(RecycleView):
    """عرض قائمة الفواتير"""
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
    """عرض تفاصيل الفاتورة"""
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


class SupplierInvoicesScreen(Screen):
    """شاشة عرض فواتير المورد"""
    
    supplier_id = NumericProperty(0)
    supplier_name = StringProperty("")
    selected_invoice_id = NumericProperty(0)
    selected_invoice_total = NumericProperty(0)
    loading = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def set_supplier(self, supplier_id, supplier_name):
        """تعيين المورد وعرض فواتيره"""
        self.supplier_id = supplier_id
        self.supplier_name = supplier_name
        self.load_invoices()
    
    def on_enter(self):
        """عند دخول الشاشة"""
        if self.supplier_id:
            self.load_invoices()
    
    def load_invoices(self):
        """تحميل فواتير المورد"""
        self.loading = True
        try:
            self.invoices_list.data = []
            
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            c.execute("""
                SELECT id, date, total FROM purchases 
                WHERE supplier_id = ? 
                ORDER BY date DESC
            """, (self.supplier_id,))
            
            invoices = c.fetchall()
            conn.close()
            
            data = []
            for row in invoices:
                data.append({
                    'purchase_id': row['id'],
                    'date': row['date'],
                    'total': row['total']
                })
            
            self.invoices_list.data = data
            Logger.info(f"OPS Supplier Invoices: Loaded {len(data)} invoices")
            
        except Exception as e:
            Logger.error(f"OPS Supplier Invoices: Error loading invoices - {e}")
            self.show_popup("خطأ", f"حدث خطأ: {str(e)}")
        finally:
            self.loading = False
    
    def load_invoice_details(self, purchase_id, total):
        """تحميل تفاصيل الفاتورة المحددة"""
        self.selected_invoice_id = purchase_id
        self.selected_invoice_total = total
        self.loading = True
        
        try:
            self.details_list.data = []
            
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            c.execute("""
                SELECT pi.quantity, pi.buy_price, pi.subtotal, p.name 
                FROM purchase_items pi 
                LEFT JOIN products p ON pi.barcode = p.barcode 
                WHERE pi.purchase_id = ?
            """, (purchase_id,))
            
            items = c.fetchall()
            conn.close()
            
            data = []
            for row in items:
                data.append({
                    'name': row['name'] or "منتج غير معروف",
                    'quantity': row['quantity'],
                    'price': row['buy_price'],
                    'subtotal': row['subtotal']
                })
            
            self.details_list.data = data
            Logger.info(f"OPS Supplier Invoices: Loaded {len(data)} items")
            
        except Exception as e:
            Logger.error(f"OPS Supplier Invoices: Error loading details - {e}")
            self.show_popup("خطأ", f"حدث خطأ: {str(e)}")
        finally:
            self.loading = False
    
    def print_invoice(self):
        """طباعة الفاتورة PDF"""
        if not self.selected_invoice_id:
            self.show_popup("تنبيه", "اختر فاتورة أولاً")
            return
        
        if not PDF_AVAILABLE:
            self.show_popup("تنبيه", "خدمة الطباعة غير متوفرة حالياً")
            return
        
        try:
            self.loading = True
            
            # جمع بيانات الفاتورة
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            # جلب معلومات الفاتورة
            c.execute("""
                SELECT id, date, total FROM purchases WHERE id = ?
            """, (self.selected_invoice_id,))
            purchase = c.fetchone()
            
            # جلب تفاصيل الأصناف
            c.execute("""
                SELECT pi.quantity, pi.buy_price, pi.subtotal, p.name 
                FROM purchase_items pi 
                LEFT JOIN products p ON pi.barcode = p.barcode 
                WHERE pi.purchase_id = ?
            """, (self.selected_invoice_id,))
            items = c.fetchall()
            conn.close()
            
            items_data = []
            for item in items:
                items_data.append({
                    'name': item['name'] or "منتج غير معروف",
                    'quantity': item['quantity'],
                    'price': item['buy_price'],
                    'subtotal': item['subtotal']
                })
            
            # إنشاء PDF
            result = create_purchase_invoice_pdf(
                self.supplier_name,
                purchase,
                items_data
            )
            
            self.loading = False
            
            if result:
                self.show_popup("نجاح", "تم إنشاء الفاتورة بنجاح\nسيتم فتحها تلقائياً")
            else:
                self.show_popup("خطأ", "فشل إنشاء الفاتورة")
                
        except Exception as e:
            self.loading = False
            Logger.error(f"OPS Supplier Invoices: Error printing invoice - {e}")
            self.show_popup("خطأ", f"حدث خطأ: {str(e)}")
    
    def go_back(self):
        """العودة لشاشة الموردين"""
        self.manager.current = 'suppliers'
    
    def show_popup(self, title, message):
        """عرض نافذة منبثقة"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=message, font_name='ArabicFont', halign='center', text_size=(400, None)))
        
        btn = Button(text="موافق", size_hint_y=0.3, font_name='ArabicFont')
        popup = Popup(title=title, content=content, size_hint=(0.8, 0.5))
        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        
        popup.open()