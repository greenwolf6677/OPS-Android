"""
OPS Orders Screen
شاشة نظام الطلبيات الرئيسية
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
from kivy.uix.image import AsyncImage
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, ListProperty, ObjectProperty
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.utils import platform
from kivy.core.window import Window
from kivy.animation import Animation

import sqlite3
import os
import random
from datetime import datetime, date, timedelta
from database import get_db_connection
from utils.settings import load_settings, get_currency, IMAGES_DIR
from utils.pdf_generator import create_invoice_pdf

# استيراد شاشات فرعية
from screens.customers_screen import CustomersScreen
from screens.products_screen import ProductsScreen


class CartItem(BoxLayout):
    """عنصر في سلة المشتريات"""
    barcode = StringProperty("")
    name = StringProperty("")
    price = NumericProperty(0)
    qty = NumericProperty(1)
    subtotal = NumericProperty(0)
    item_id = NumericProperty(0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 60
        self.padding = [5, 5]
        self.spacing = 5


class ProductCard(BoxLayout):
    """بطاقة منتج في عرض الشبكة"""
    barcode = StringProperty("")
    name = StringProperty("")
    price = NumericProperty(0)
    quantity = NumericProperty(0)
    image_path = StringProperty("")
    category_name = StringProperty("")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (None, None)
        self.width = 280
        self.height = 380
        self.padding = [8, 8]
        self.spacing = 5


class CartRecycleView(RecycleView):
    """عرض سلة المشتريات"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data = []
        self.layout_manager = RecycleBoxLayout(
            default_size=(None, 60),
            default_size_hint=(1, None),
            size_hint_y=None,
            height=self.minimum_height,
            orientation='vertical'
        )
        self.add_widget(self.layout_manager)


class OrdersScreen(Screen):
    """شاشة الطلبيات الرئيسية"""
    
    # متغيرات السلة
    cart = ListProperty([])
    cart_count = NumericProperty(0)
    cart_total = NumericProperty(0)
    discount = NumericProperty(0)
    net_total = NumericProperty(0)
    
    # متغيرات الطلب
    customer_name = StringProperty("غير محدد")
    customer_id = NumericProperty(0)
    payment_method = StringProperty("كاش")
    
    # متغيرات الشيكات
    show_check_fields = BooleanProperty(False)
    check_owner = StringProperty("")
    check_bank = StringProperty("")
    check_number = StringProperty("")
    check_due_date = StringProperty("")
    
    # متغيرات البحث والتصفية
    search_text = StringProperty("")
    selected_category = StringProperty("الكل")
    default_qty = NumericProperty(1)
    
    # قوائم
    categories_list = ListProperty(["الكل"])
    products_list = ListProperty([])
    customers_list = ListProperty(["غير محدد"])
    customers_dict = {}
    
    # حالة التحميل
    loading = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.settings = load_settings()
        self.currency = get_currency()
        self.load_categories()
        self.load_customers()
        self.load_products()
        
        # تعيين التاريخ الافتراضي للشيك
        self.check_due_date = date.today().strftime("%Y-%m-%d")
    
    def on_enter(self):
        """عند دخول الشاشة"""
        self.load_products()
        Logger.info("OPS Orders: Screen entered")
    
    def load_categories(self):
        """تحميل التصنيفات"""
        try:
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT name FROM categories ORDER BY name")
            categories = ["الكل"] + [row[0] for row in c.fetchall()]
            conn.close()
            self.categories_list = categories
            Logger.info(f"OPS Orders: Loaded {len(categories)-1} categories")
        except Exception as e:
            Logger.error(f"OPS Orders: Error loading categories - {e}")
    
    def load_customers(self):
        """تحميل الزبائن"""
        try:
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT id, name FROM customers ORDER BY name")
            customers = c.fetchall()
            conn.close()
            
            self.customers_list = ["غير محدد"]
            for row in customers:
                self.customers_list.append(row['name'])
                self.customers_dict[row['name']] = row['id']
            
            Logger.info(f"OPS Orders: Loaded {len(customers)} customers")
        except Exception as e:
            Logger.error(f"OPS Orders: Error loading customers - {e}")
    
    def load_products(self):
        """تحميل المنتجات"""
        self.loading = True
        try:
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            query = """
                SELECT p.barcode, p.name, p.buy_price, p.sell_price, p.quantity, 
                       p.category_id, p.image_path, c.name as category_name
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE 1=1
            """
            params = []
            
            if self.search_text:
                query += " AND (p.name LIKE ? OR p.barcode LIKE ?)"
                params.extend([f'%{self.search_text}%', f'%{self.search_text}%'])
            
            if self.selected_category != "الكل":
                query += " AND c.name = ?"
                params.append(self.selected_category)
            
            query += " ORDER BY p.name"
            
            c.execute(query, params)
            products = c.fetchall()
            conn.close()
            
            data = []
            for row in products:
                data.append({
                    'barcode': row['barcode'],
                    'name': row['name'],
                    'price': row['sell_price'] or 0,
                    'quantity': row['quantity'] or 0,
                    'image_path': row['image_path'] or "",
                    'category_name': row['category_name'] or ""
                })
            
            self.products_list = data
            Logger.info(f"OPS Orders: Loaded {len(data)} products")
            
        except Exception as e:
            Logger.error(f"OPS Orders: Error loading products - {e}")
        finally:
            self.loading = False
    
    def update_cart(self):
        """تحديث السلة والإجماليات"""
        subtotal = sum(item['subtotal'] for item in self.cart)
        self.cart_total = subtotal
        self.cart_count = len(self.cart)
        
        net = subtotal - self.discount
        if net < 0:
            net = 0
        self.net_total = net
    
    def add_to_cart(self, product, qty=None):
        """إضافة منتج للسلة"""
        if qty is None:
            qty = self.default_qty
        
        # التحقق من الكمية المتاحة
        if qty > product['quantity']:
            self.show_popup("تنبيه", f"الكمية المتاحة: {product['quantity']}")
            return
        
        # البحث عن المنتج في السلة
        for item in self.cart:
            if item['barcode'] == product['barcode']:
                item['qty'] += qty
                item['subtotal'] = item['qty'] * item['price']
                self.update_cart()
                self.refresh_cart_display()
                self.show_notification(f"✅ تم تحديث كمية {product['name']}")
                return
        
        # إضافة منتج جديد
        new_item = {
            'barcode': product['barcode'],
            'name': product['name'],
            'price': product['price'],
            'qty': qty,
            'subtotal': qty * product['price']
        }
        self.cart.append(new_item)
        self.update_cart()
        self.refresh_cart_display()
        self.show_notification(f"✅ تم إضافة {product['name']} إلى السلة")
    
    def remove_from_cart(self, item_id):
        """حذف منتج من السلة"""
        for i, item in enumerate(self.cart):
            if i == item_id:
                del self.cart[i]
                break
        self.update_cart()
        self.refresh_cart_display()
    
    def refresh_cart_display(self):
        """تحديث عرض السلة"""
        data = []
        for i, item in enumerate(self.cart):
            data.append({
                'barcode': item['barcode'],
                'name': item['name'],
                'price': item['price'],
                'qty': item['qty'],
                'subtotal': item['subtotal'],
                'item_id': i
            })
        self.cart_list.data = data
    
    def on_payment_method_change(self, method):
        """عند تغيير طريقة الدفع"""
        self.payment_method = method
        self.show_check_fields = (method == "شيكات")
    
    def on_customer_change(self, name):
        """عند تغيير الزبون"""
        self.customer_name = name
        if name != "غير محدد":
            self.customer_id = self.customers_dict.get(name, 0)
        else:
            self.customer_id = 0
    
    def new_order(self):
        """بدء طلبية جديدة"""
        self.cart = []
        self.discount = 0
        self.customer_name = "غير محدد"
        self.customer_id = 0
        self.payment_method = "كاش"
        self.show_check_fields = False
        self.check_owner = ""
        self.check_bank = ""
        self.check_number = ""
        self.check_due_date = date.today().strftime("%Y-%m-%d")
        self.update_cart()
        self.refresh_cart_display()
        self.show_notification("🔄 طلبية جديدة")
    
    def confirm_order(self):
        """تأكيد الطلب"""
        if not self.cart:
            self.show_popup("تنبيه", "السلة فارغة")
            return
        
        # التحقق من معلومات الشيك
        if self.payment_method == "شيكات" and not self.check_owner:
            self.show_popup("تنبيه", "الرجاء إدخال اسم صاحب الشيك")
            return
        
        # حفظ الطلب
        order_id = self.save_order()
        if not order_id:
            return
        
        # تحويل الطلب إلى فاتورة
        invoice_id = datetime.now().strftime("%Y%m%d%H%M%S") + str(order_id)
        
        if self.process_sales(invoice_id, order_id):
            self.show_popup("نجاح", f"✅ تم تأكيد الطلبية بنجاح\nرقم الفاتورة: {invoice_id}")
            self.new_order()
            self.load_products()
            self.load_customers()
    
    def save_order(self):
        """حفظ الطلب في جدول orders"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute("""
                INSERT INTO orders (order_date, customer_id, total, discount, net_total, payment_method, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                self.customer_id,
                self.cart_total,
                self.discount,
                self.net_total,
                self.payment_method,
                'pending'
            ))
            
            order_id = c.lastrowid
            
            for item in self.cart:
                c.execute("""
                    INSERT INTO order_items (order_id, barcode, name, price, quantity, subtotal)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (order_id, item['barcode'], item['name'], item['price'], item['qty'], item['subtotal']))
            
            if self.payment_method == "شيكات" and self.check_owner:
                c.execute("""
                    INSERT INTO checks (order_id, check_number, owner_name, bank_name, due_date, amount, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (order_id, self.check_number, self.check_owner, self.check_bank,
                      self.check_due_date, self.net_total, 'pending'))
            
            conn.commit()
            conn.close()
            
            return order_id
            
        except Exception as e:
            Logger.error(f"OPS Orders: Error saving order - {e}")
            self.show_popup("خطأ", f"حدث خطأ: {str(e)}")
            return None
    
    def process_sales(self, invoice_id, order_id):
        """معالجة المبيعات وتحديث المخزون"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cust_id = self.customer_id
            pay_method = self.payment_method
            
            for item in self.cart:
                c.execute("""
                    INSERT INTO sales
                    (invoice_id, customer_id, barcode, quantity, price, total, date, payment_method)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (invoice_id, cust_id, item['barcode'], item['qty'], 
                      item['price'], item['subtotal'], current_date, pay_method))
                
                if item['barcode'] != "سريع":
                    c.execute("""
                        UPDATE products
                        SET quantity = quantity - ?
                        WHERE barcode = ?
                    """, (item['qty'], item['barcode']))
            
            if pay_method == "دين" and cust_id != 0:
                c.execute("""
                    UPDATE customers
                    SET balance = balance + ?
                    WHERE id = ?
                """, (self.net_total, cust_id))
            
            c.execute("UPDATE orders SET status = 'confirmed' WHERE id = ?", (order_id,))
            
            conn.commit()
            conn.close()
            
            # طباعة الفاتورة
            create_invoice_pdf(invoice_id, order_id, self.settings)
            
            return True
            
        except Exception as e:
            Logger.error(f"OPS Orders: Error processing sales - {e}")
            self.show_popup("خطأ", f"حدث خطأ: {str(e)}")
            return False
    
    def show_notification(self, message, duration=2):
        """إظهار إشعار مؤقت"""
        # سيتم تنفيذها في KV
        pass
    
    def show_popup(self, title, message):
        """عرض نافذة منبثقة"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=message, font_name='ArabicFont', halign='center', text_size=(400, None)))
        
        btn = Button(text="موافق", size_hint_y=0.3, font_name='ArabicFont')
        popup = Popup(title=title, content=content, size_hint=(0.8, 0.5))
        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        
        popup.open()
    
    def go_back(self):
        """العودة للشاشة الرئيسية"""
        self.manager.current = 'dashboard'