"""
OPS Returns Screen
شاشة إدارة المرتجعات لنظام OPS
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, ObjectProperty
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.utils import platform

import sqlite3
import os
from datetime import datetime
from database import get_db_connection

# استيراد دوال الطباعة
try:
    from utils.pdf_generator import create_return_receipt
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    Logger.warning("OPS Returns: PDF generator not available")


class ReturnItem(BoxLayout):
    """عنصر صنف في قائمة المرتجعات"""
    selected = BooleanProperty(False)
    name = StringProperty("")
    available_qty = NumericProperty(0)
    return_qty = NumericProperty(0)
    price = NumericProperty(0)
    subtotal = NumericProperty(0)
    sale_id = NumericProperty(0)
    barcode = StringProperty("")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 50
        self.padding = [5, 5]
        self.spacing = 5


class ReturnsRecycleView(RecycleView):
    """عرض قائمة الأصناف المراد إرجاعها"""
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


class ReturnsScreen(Screen):
    """شاشة إدارة المرتجعات"""
    
    # متغيرات الزبون
    customer_id = NumericProperty(0)
    customer_name = StringProperty("")
    customers_list = []
    customers_dict = {}
    
    # متغيرات الفاتورة
    invoice_id = StringProperty("")
    invoices_list = []
    
    # متغيرات المرتجع
    return_amount = StringProperty("0.00")
    reason = StringProperty("")
    
    # حالة التحميل
    loading = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.load_customers()
    
    def on_enter(self):
        """عند دخول الشاشة"""
        self.load_customers()
        Logger.info("OPS Returns: Screen entered")
    
    def load_customers(self):
        """تحميل قائمة الزبائن"""
        try:
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT id, name FROM customers ORDER BY name")
            customers = c.fetchall()
            conn.close()
            
            self.customers_list = ["اختر الزبون"]
            for row in customers:
                self.customers_list.append(row['name'])
                self.customers_dict[row['name']] = row['id']
            
            Logger.info(f"OPS Returns: Loaded {len(customers)} customers")
            
        except Exception as e:
            Logger.error(f"OPS Returns: Error loading customers - {e}")
            self.show_popup("خطأ", f"حدث خطأ: {str(e)}")
    
    def on_customer_select(self, customer_name):
        """عند اختيار الزبون"""
        if customer_name == "اختر الزبون" or not customer_name:
            self.customer_id = 0
            self.customer_name = ""
            self.invoices_list = []
            self.invoice_id = ""
            return
        
        self.customer_id = self.customers_dict.get(customer_name, 0)
        self.customer_name = customer_name
        
        if self.customer_id:
            self.load_customer_invoices()
    
    def load_customer_invoices(self):
        """تحميل فواتير الزبون"""
        if self.customer_id == 0:
            return
        
        self.loading = True
        try:
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            # جلب الفواتير التي تحتوي على أصناف لم ترجع بالكامل
            c.execute("""
                SELECT DISTINCT s.invoice_id, s.date 
                FROM sales s
                WHERE s.customer_id = ?
                GROUP BY s.invoice_id
                HAVING SUM(s.quantity) > COALESCE(SUM(s.returned_qty), 0)
                ORDER BY s.date DESC
            """, (self.customer_id,))
            
            self.invoices_list = ["اختر الفاتورة"]
            for row in c.fetchall():
                self.invoices_list.append(row['invoice_id'])
            
            conn.close()
            Logger.info(f"OPS Returns: Loaded {len(self.invoices_list)-1} invoices")
            
        except Exception as e:
            Logger.error(f"OPS Returns: Error loading invoices - {e}")
            self.show_popup("خطأ", f"فشل تحميل الفواتير: {str(e)}")
        finally:
            self.loading = False
    
    def load_invoice_items(self):
        """تحميل أصناف الفاتورة المحددة"""
        if not self.invoice_id or self.invoice_id == "اختر الفاتورة":
            self.show_popup("تنبيه", "الرجاء اختيار رقم الفاتورة")
            return
        
        self.loading = True
        try:
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            c.execute("""
                SELECT s.id, s.barcode, 
                       COALESCE(p.name, 'صنف سريع') as item_name, 
                       s.quantity, 
                       s.price,
                       s.total,
                       COALESCE(s.returned_qty, 0) as already_returned
                FROM sales s 
                LEFT JOIN products p ON s.barcode = p.barcode 
                WHERE s.invoice_id = ?
            """, (self.invoice_id,))
            
            rows = c.fetchall()
            conn.close()
            
            if not rows:
                self.show_popup("معلومات", "لا توجد أصناف في هذه الفاتورة")
                self.returns_list.data = []
                self.loading = False
                return
            
            data = []
            for row in rows:
                available = row['quantity'] - row['already_returned']
                if available > 0:
                    data.append({
                        'selected': False,
                        'name': row['item_name'],
                        'available_qty': available,
                        'return_qty': 0,
                        'price': row['price'],
                        'subtotal': 0,
                        'sale_id': row['id'],
                        'barcode': row['barcode']
                    })
            
            self.returns_list.data = data
            
            if len(data) == 0:
                self.show_popup("معلومات", "جميع أصناف هذه الفاتورة تم إرجاعها مسبقاً")
            
            self.update_total_amount()
            Logger.info(f"OPS Returns: Loaded {len(data)} items")
            
        except Exception as e:
            Logger.error(f"OPS Returns: Error loading invoice items - {e}")
            self.show_popup("خطأ", f"فشل تحميل الأصناف: {str(e)}")
        finally:
            self.loading = False
    
    def update_return_qty(self, index, new_qty):
        """تحديث كمية المرتجع لصنف معين"""
        data = self.returns_list.data
        if index < len(data):
            item = data[index]
            max_qty = item['available_qty']
            
            if new_qty > max_qty:
                new_qty = max_qty
                self.show_popup("تنبيه", f"الحد الأقصى للكمية: {max_qty}")
            
            item['return_qty'] = new_qty
            item['selected'] = new_qty > 0
            item['subtotal'] = new_qty * item['price']
            
            self.returns_list.data = data
            self.update_total_amount()
    
    def toggle_select(self, index):
        """تبديل تحديد صنف"""
        data = self.returns_list.data
        if index < len(data):
            item = data[index]
            if not item['selected']:
                # تحديد الصنف مع وضع الكمية القصوى
                item['selected'] = True
                item['return_qty'] = item['available_qty']
                item['subtotal'] = item['return_qty'] * item['price']
            else:
                # إلغاء تحديد الصنف
                item['selected'] = False
                item['return_qty'] = 0
                item['subtotal'] = 0
            
            self.returns_list.data = data
            self.update_total_amount()
    
    def update_total_amount(self):
        """تحديث إجمالي المبلغ المسترد"""
        total = 0.0
        for item in self.returns_list.data:
            if item['selected'] and item['return_qty'] > 0:
                total += item['subtotal']
        self.return_amount = f"{total:.2f}"
    
    def process_return(self):
        """تنفيذ عملية المرتجع"""
        # التحقق من وجود أصناف محددة
        items_to_return = []
        for item in self.returns_list.data:
            if item['selected'] and item['return_qty'] > 0:
                items_to_return.append(item)
        
        if not items_to_return:
            self.show_popup("تنبيه", "الرجاء تحديد الأصناف المراد إرجاعها")
            return
        
        if self.customer_id == 0:
            self.show_popup("تنبيه", "الرجاء اختيار الزبون")
            return
        
        total_amount = float(self.return_amount)
        
        # تأكيد العملية
        confirm_msg = (
            f"الزبون: {self.customer_name}\n"
            f"عدد الأصناف: {len(items_to_return)}\n"
            f"المبلغ المسترد: {total_amount:.2f} ₪\n\n"
            f"هل أنت متأكد من تنفيذ المرتجع؟"
        )
        
        self.show_confirmation_popup("تأكيد المرتجع", confirm_msg, 
                                      lambda: self._execute_return(items_to_return, total_amount))
    
    def _execute_return(self, items_to_return, total_amount):
        """تنفيذ المرتجع بعد التأكيد"""
        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            for item in items_to_return:
                sale_id = item['sale_id']
                barcode = item['barcode']
                qty_returned = item['return_qty']
                amount = item['subtotal']
                
                # إعادة الكمية للمخزون (إذا لم يكن صنف سريع)
                if barcode != "سريع":
                    cur.execute("""
                        UPDATE products 
                        SET quantity = quantity + ? 
                        WHERE barcode = ?
                    """, (qty_returned, barcode))
                
                # تحديث كمية المرتجعات في الفاتورة
                cur.execute("""
                    UPDATE sales 
                    SET returned_qty = COALESCE(returned_qty, 0) + ? 
                    WHERE id = ?
                """, (qty_returned, sale_id))
                
                # تسجيل المرتجع في جدول returns
                cur.execute("""
                    INSERT INTO returns 
                    (original_sale_id, barcode, quantity, return_amount, return_date, reason, customer_id) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    sale_id, 
                    barcode, 
                    qty_returned, 
                    amount, 
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                    self.reason.strip(),
                    self.customer_id
                ))
            
            # تحديث رصيد الزبون (خصم المبلغ)
            cur.execute("""
                UPDATE customers 
                SET balance = balance - ? 
                WHERE id = ?
            """, (total_amount, self.customer_id))
            
            conn.commit()
            
            # طباعة وصل المرتجع
            if PDF_AVAILABLE:
                create_return_receipt(
                    self.customer_name,
                    items_to_return,
                    f"{total_amount:.2f}",
                    self.reason.strip()
                )
            
            self.show_popup(
                "نجاح", 
                f"✅ تم تنفيذ المرتجع بنجاح\n\n"
                f"الزبون: {self.customer_name}\n"
                f"المبلغ المسترد: {total_amount:.2f} ₪\n"
                f"تم خصم المبلغ من رصيد الزبون"
            )
            
            # إعادة تعيين الشاشة
            self.customer_name = ""
            self.customer_id = 0
            self.invoice_id = ""
            self.reason = ""
            self.return_amount = "0.00"
            self.returns_list.data = []
            
        except Exception as e:
            if conn:
                conn.rollback()
            Logger.error(f"OPS Returns: Error processing return - {e}")
            self.show_popup("خطأ", f"فشل تنفيذ المرتجع: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def go_back(self):
        """العودة للشاشة الرئيسية"""
        self.manager.current = 'dashboard'
    
    def show_popup(self, title, message):
        """عرض نافذة منبثقة"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=message, font_name='ArabicFont', halign='center', text_size=(400, None)))
        
        btn = Button(text="موافق", size_hint_y=0.3, font_name='ArabicFont')
        popup = Popup(title=title, content=content, size_hint=(0.8, 0.5))
        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        
        popup.open()
    
    def show_confirmation_popup(self, title, message, on_confirm):
        """عرض نافذة تأكيد"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=message, font_name='ArabicFont', halign='center', text_size=(400, None)))
        
        buttons = BoxLayout(size_hint_y=0.3, spacing=10)
        btn_yes = Button(text="نعم", font_name='ArabicFont', background_color=(0.2, 0.6, 0.2, 1))
        btn_no = Button(text="لا", font_name='ArabicFont', background_color=(0.6, 0.2, 0.2, 1))
        buttons.add_widget(btn_yes)
        buttons.add_widget(btn_no)
        content.add_widget(buttons)
        
        popup = Popup(title=title, content=content, size_hint=(0.7, 0.5))
        
        def yes_action(instance):
            popup.dismiss()
            on_confirm()
        
        btn_yes.bind(on_press=yes_action)
        btn_no.bind(on_press=popup.dismiss)
        
        popup.open()