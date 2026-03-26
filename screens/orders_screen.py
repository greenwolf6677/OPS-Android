"""
OPS Orders Screen
شاشة نظام الطلبيات الرئيسية - النسخة الكاملة والمحسنة
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, ListProperty
from kivy.clock import Clock
from kivy.logger import Logger

import sqlite3
import os
from datetime import datetime, date

# استيراد الوظائف المساعدة من مشروعك
from database import get_db_connection
from utils.settings import load_settings, get_currency
from utils.pdf_generator import create_invoice_pdf

class CartItem(BoxLayout):
    """عنصر في سلة المشتريات - يتم التحكم به عبر RecycleView في KV"""
    barcode = StringProperty("")
    name = StringProperty("")
    price = NumericProperty(0)
    qty = NumericProperty(1)
    subtotal = NumericProperty(0)
    item_id = NumericProperty(0)

class ProductCard(BoxLayout):
    """بطاقة منتج في عرض الشبكة"""
    barcode = StringProperty("")
    name = StringProperty("")
    price = NumericProperty(0)
    quantity = NumericProperty(0)
    image_path = StringProperty("")
    category_name = StringProperty("")

class OrdersScreen(Screen):
    """شاشة الطلبيات الرئيسية"""
    
    # متغيرات السلة والإجماليات
    cart = ListProperty([])
    cart_total = NumericProperty(0)
    discount = NumericProperty(0)
    net_total = NumericProperty(0)
    
    # متغيرات الطلب والزبون
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
    
    # قوائم البيانات
    categories_list = ListProperty(["الكل"])
    customers_list = ListProperty(["غير محدد"])
    customers_dict = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.settings = load_settings()
        self.currency = get_currency()
        self.check_due_date = date.today().strftime("%Y-%m-%d")
        
        # تحميل البيانات الأولية عند تشغيل التطبيق
        Clock.schedule_once(self.initial_data_load, 0.5)

    def initial_data_load(self, dt):
        """تحميل البيانات عند بدء التشغيل"""
        self.load_categories()
        self.load_customers()
        self.load_products()

    def on_enter(self):
        """تحديث المنتجات عند الدخول للشاشة لضمان مزامنة المخزون"""
        self.load_products()
        Logger.info("OPS Orders: Screen updated on enter")

    def load_categories(self):
        try:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT name FROM categories ORDER BY name")
            rows = c.fetchall()
            self.categories_list = ["الكل"] + [row[0] for row in rows]
            conn.close()
        except Exception as e:
            Logger.error(f"OPS Orders: Error loading categories - {e}")

    def load_customers(self):
        try:
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT id, name FROM customers ORDER BY name")
            rows = c.fetchall()
            self.customers_list = ["غير محدد"]
            for row in rows:
                self.customers_list.append(row['name'])
                self.customers_dict[row['name']] = row['id']
            conn.close()
        except Exception as e:
            Logger.error(f"OPS Orders: Error loading customers - {e}")

    def load_products(self, *args):
        """تحميل المنتجات وتوليد البطاقات برمجياً داخل الشبكة"""
        try:
            # الوصول لشبكة المنتجات المعرفة في ملف KV
            grid = self.ids.products_grid
            grid.clear_widgets()
            
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            query = """
                SELECT p.*, c.name as category_name 
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
            
            for row in products:
                card = ProductCard(
                    barcode=row['barcode'],
                    name=row['name'],
                    price=row['sell_price'] or 0,
                    quantity=row['quantity'] or 0,
                    image_path=row['image_path'] or "",
                    category_name=row['category_name'] or "عام"
                )
                grid.add_widget(card)
                
            conn.close()
        except Exception as e:
            Logger.error(f"OPS Orders: Error loading products - {e}")

    def apply_discount_logic(self, value):
        """تحديث الخصم بأمان وتحديث الإجماليات"""
        try:
            self.discount = float(value) if value else 0.0
        except ValueError:
            self.discount = 0.0
        self.update_cart()

    def update_cart(self):
        """حساب إجماليات السلة"""
        self.cart_total = sum(item['subtotal'] for item in self.cart)
        self.net_total = max(0, self.cart_total - self.discount)

    def add_to_cart(self, product):
        """إضافة منتج للسلة أو تحديث الكمية إذا وجد"""
        qty = self.default_qty
        
        # التحقق من المخزون
        if qty > product['quantity']:
            self.show_popup("تنبيه", f"الكمية غير كافية! المتوفر: {product['quantity']}")
            return

        # البحث عن المنتج في السلة الحالية
        item_found = False
        for item in self.cart:
            if item['barcode'] == product['barcode']:
                item['qty'] += qty
                item['subtotal'] = item['qty'] * item['price']
                item_found = True
                break
        
        if not item_found:
            self.cart.append({
                'barcode': product['barcode'],
                'name': product['name'],
                'price': product['price'],
                'qty': qty,
                'subtotal': qty * product['price']
            })
            
        self.update_cart()
        self.refresh_cart_display()

    def remove_from_cart(self, index):
        """إزالة عنصر من السلة بناءً على ترتيبه"""
        if 0 <= index < len(self.cart):
            self.cart.pop(index)
            self.update_cart()
            self.refresh_cart_display()

    def refresh_cart_display(self):
        """تحديث الـ RecycleView ليعكس محتويات السلة"""
        self.ids.cart_list.data = [
            {
                'barcode': item['barcode'],
                'name': item['name'],
                'price': item['price'],
                'qty': item['qty'],
                'subtotal': item['subtotal'],
                'item_id': i
            } for i, item in enumerate(self.cart)
        ]

    def on_payment_method_change(self, method):
        self.payment_method = method
        self.show_check_fields = (method == "شيكات")

    def on_customer_change(self, name):
        self.customer_name = name
        self.customer_id = self.customers_dict.get(name, 0)

    def new_order(self):
        """تصفير الشاشة لطلب جديد"""
        self.cart = []
        self.discount = 0
        self.customer_name = "غير محدد"
        self.customer_id = 0
        self.payment_method = "كاش"
        self.show_check_fields = False
        self.update_cart()
        self.refresh_cart_display()

    def confirm_order(self):
        """عملية تأكيد الطلب وحفظه"""
        if not self.cart:
            self.show_popup("تنبيه", "السلة فارغة!")
            return
        
        if self.payment_method == "شيكات" and not self.check_owner:
            self.show_popup("تنبيه", "يجب إدخال اسم صاحب الشيك")
            return

        order_id = self.save_order_to_db()
        if order_id:
            invoice_id = f"INV-{datetime.now().strftime('%y%m%d')}-{order_id}"
            if self.process_sales_and_stock(invoice_id, order_id):
                self.show_popup("نجاح", f"تم تأكيد الطلب بنجاح\nرقم الفاتورة: {invoice_id}")
                self.new_order()
                self.load_products() # لتحديث الكميات المعروضة

    def save_order_to_db(self):
        """حفظ الطلب الأساسي في قاعدة البيانات"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("""
                INSERT INTO orders (order_date, customer_id, total, discount, net_total, payment_method, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.customer_id, 
                  self.cart_total, self.discount, self.net_total, self.payment_method, 'confirmed'))
            
            order_id = c.lastrowid
            
            # حفظ أصناف الطلب
            for item in self.cart:
                c.execute("""
                    INSERT INTO order_items (order_id, barcode, name, price, quantity, subtotal)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (order_id, item['barcode'], item['name'], item['price'], item['qty'], item['subtotal']))
            
            # إذا كان الدفع بشيك
            if self.payment_method == "شيكات":
                c.execute("""
                    INSERT INTO checks (order_id, check_number, owner_name, bank_name, due_date, amount, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (order_id, self.check_number, self.check_owner, self.check_bank, 
                      self.check_due_date, self.net_total, 'pending'))
            
            conn.commit()
            conn.close()
            return order_id
        except Exception as e:
            Logger.error(f"Error saving order: {e}")
            self.show_popup("خطأ", "فشل حفظ الطلب في قاعدة البيانات")
            return None

    def process_sales_and_stock(self, invoice_id, order_id):
        """تحديث المبيعات والمخزون وحسابات الزبائن"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            for item in self.cart:
                # 1. إضافة للمبيعات
                c.execute("""
                    INSERT INTO sales (invoice_id, customer_id, barcode, quantity, price, total, date, payment_method)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (invoice_id, self.customer_id, item['barcode'], item['qty'], item['price'], item['subtotal'], now, self.payment_method))
                
                # 2. تنزيل من المخزون
                c.execute("UPDATE products SET quantity = quantity - ? WHERE barcode = ?", (item['qty'], item['barcode']))

            # 3. تحديث دين الزبون إذا كانت الطريقة "دين"
            if self.payment_method == "دين" and self.customer_id != 0:
                c.execute("UPDATE customers SET balance = balance + ? WHERE id = ?", (self.net_total, self.customer_id))

            conn.commit()
            conn.close()
            
            # توليد PDF الفاتورة (اختياري حسب وظائف مشروعك)
            try:
                create_invoice_pdf(invoice_id, order_id, self.settings)
            except:
                Logger.warning("PDF Generation skipped or failed")
                
            return True
        except Exception as e:
            Logger.error(f"Error processing sales: {e}")
            return False

    def show_popup(self, title, message):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=message, font_name='ArabicFont', halign='center'))
        btn = Button(text="موافق", size_hint_y=None, height=45, font_name='ArabicFont')
        popup = Popup(title=title, content=content, size_hint=(0.7, 0.4))
        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        popup.open()

    def go_back(self):
        self.manager.current = 'dashboard'