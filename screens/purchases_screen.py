"""
OPS Purchases Screen - المشتريات المتكاملة (النسخة النهائية الشاملة)
تشمل: إدارة المخزون، حسابات الموردين، والطباعة التلقائية.
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.recycleview import RecycleView
from kivy.properties import StringProperty, NumericProperty, ObjectProperty, ListProperty
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.utils import platform

import sqlite3
import os
from datetime import datetime

# دالة الاتصال بقاعدة البيانات
def get_db_connection():
    try:
        from database import get_db_connection as db_conn
        return db_conn()
    except ImportError:
        conn = sqlite3.connect('pos_database.db')
        conn.row_factory = sqlite3.Row
        return conn

class PurchaseItem(BoxLayout):
    """تمثيل سطر واحد في سلة المشتريات (يستخدم في RecycleView)"""
    barcode = StringProperty("")
    name = StringProperty("")
    buy_price = NumericProperty(0)
    qty = NumericProperty(1)
    subtotal = NumericProperty(0)
    item_id = NumericProperty(0)

class PurchasesScreen(Screen):
    # خصائص الربط مع واجهة KV
    supplier_name = StringProperty("اختر المورد")
    total_amount = StringProperty("0.00")
    discount_amount = StringProperty("0.00")
    net_amount = StringProperty("0.00")
    barcode = StringProperty("")
    quantity = StringProperty("1")
    
    suppliers_list = ListProperty([])
    suppliers_dict = {}
    last_invoice_id = NumericProperty(0) # لتخزين رقم آخر فاتورة تم حفظها

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cart = []
        self.next_item_id = 1
        Clock.schedule_once(lambda dt: self.load_suppliers())
        
    def on_enter(self):
        """تحديث البيانات عند فتح الشاشة"""
        self.load_suppliers()
        self.update_totals()

    def load_suppliers(self):
        """تحميل قائمة الموردين من قاعدة البيانات"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT id, name FROM suppliers ORDER BY name")
            suppliers = c.fetchall()
            conn.close()
            
            self.suppliers_list = ["اختر المورد"] + [row['name'] for row in suppliers]
            self.suppliers_dict = {row['name']: row['id'] for row in suppliers}
        except Exception as e:
            Logger.error(f"OPS Purchases: Error loading suppliers - {e}")

    def update_totals(self, *args):
        """حساب إجماليات الفاتورة"""
        subtotal = sum(item['subtotal'] for item in self.cart)
        try:
            discount = float(self.discount_amount) if self.discount_amount else 0.0
        except ValueError:
            discount = 0.0
        
        final_total = max(0, subtotal - discount)
        self.total_amount = f"{subtotal:.2f}"
        self.net_amount = f"{final_total:.2f}"

    def add_to_cart(self):
        """إضافة منتج للسلة بناءً على الباركود"""
        barcode_val = self.barcode.strip()
        if not barcode_val:
            return

        try:
            qty_val = int(self.quantity)
            if qty_val <= 0: raise ValueError
        except ValueError:
            self.show_popup("خطأ", "الكمية يجب أن تكون رقماً صحيحاً موجباً")
            return

        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT name, buy_price FROM products WHERE barcode = ?", (barcode_val,))
        product = c.fetchone()
        conn.close()

        if not product:
            self.show_add_product_popup(barcode_val, qty_val)
            return

        # فحص إذا كان المنتج موجود مسبقاً في السلة لزيادة الكمية
        for item in self.cart:
            if item['barcode'] == barcode_val:
                item['qty'] += qty_val
                item['subtotal'] = item['qty'] * item['buy_price']
                self.refresh_cart_display()
                self.update_totals()
                self.clear_inputs()
                return

        # إضافة صنف جديد
        self.cart.append({
            'id': self.next_item_id,
            'barcode': barcode_val,
            'name': product['name'],
            'buy_price': product['buy_price'],
            'qty': qty_val,
            'subtotal': qty_val * product['buy_price']
        })
        self.next_item_id += 1
        self.refresh_cart_display()
        self.update_totals()
        self.clear_inputs()

    def refresh_cart_display(self):
        """تحديث بيانات RecycleView"""
        if 'cart_list' in self.ids:
            self.ids.cart_list.data = [
                {
                    'barcode': i['barcode'],
                    'name': i['name'],
                    'buy_price': i['buy_price'],
                    'qty': i['qty'],
                    'subtotal': i['subtotal'],
                    'item_id': i['id']
                } for i in self.cart
            ]

    def finish_purchase(self):
        """حفظ العملية في القاعدة وتحديث الأرصدة والطباعة"""
        if not self.cart:
            self.show_popup("تنبيه", "سلة المشتريات فارغة")
            return
        if self.supplier_name == "اختر المورد":
            self.show_popup("تنبيه", "يرجى تحديد المورد لتقييد الفاتورة في حسابه")
            return

        supplier_id = self.suppliers_dict.get(self.supplier_name)
        final_total = float(self.net_amount)
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            # 1. إنشاء سجل الفاتورة
            c.execute("INSERT INTO purchases (date, supplier_id, total, notes) VALUES (?, ?, ?, ?)",
                      (date_str, supplier_id, final_total, f"شراء أصناف - مورد: {self.supplier_name}"))
            purchase_id = c.lastrowid
            self.last_invoice_id = purchase_id # حفظ الرقم للطباعة اللاحقة
            
            # 2. تحديث المخزون وتفاصيل الفاتورة
            for item in self.cart:
                c.execute("INSERT INTO purchase_items (purchase_id, barcode, quantity, buy_price, subtotal) VALUES (?, ?, ?, ?, ?)",
                          (purchase_id, item['barcode'], item['qty'], item['buy_price'], item['subtotal']))
                c.execute("UPDATE products SET quantity = quantity + ? WHERE barcode = ?", (item['qty'], item['barcode']))
            
            # 3. تحديث رصيد المورد (زيادة مديونية المحل للمورد)
            c.execute("UPDATE suppliers SET balance = balance + ? WHERE id = ?", (final_total, supplier_id))
            
            conn.commit()
            conn.close()

            # 4. طباعة الفاتورة تلقائياً
            self.generate_invoice_print(purchase_id, self.cart, self.supplier_name, final_total)
            
            self.show_popup("نجاح", f"تم الحفظ بنجاح. رقم الفاتورة: {purchase_id}")
            self.clear_cart()
            
        except Exception as e:
            self.show_popup("خطأ في النظام", str(e))

    def generate_invoice_print(self, p_id, items_list, s_name, net):
        """توليد ملف نصي جاهز للطباعة"""
        filename = f"Invoice_Purchase_{p_id}.txt"
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        content = f"========================================\n"
        content += f"        سند استلام مشتريات        \n"
        content += f"========================================\n"
        content += f"رقم الفاتورة: {p_id}\n"
        content += f"التاريخ: {now}\n"
        content += f"المورد: {s_name}\n"
        content += "----------------------------------------\n"
        content += f"{'الصنف':<18} {'الكمية':<6} {'المجموع':<10}\n"
        content += "----------------------------------------\n"
        
        for item in items_list:
            name = item['name'][:18]
            content += f"{name:<18} {item['qty']:<6} {item['subtotal']:<10.2f}\n"
            
        content += "----------------------------------------\n"
        content += f"الإجمالي الصافي: {net:.2f} ₪\n"
        content += "========================================\n"
        content += "       تم الاستلام بواسطة OPS System      \n"

        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            
            if platform == 'win':
                os.startfile(filename)
        except Exception as e:
            Logger.error(f"Printing Error: {e}")

    def print_last_invoice(self):
        """وظيفة زر طباعة آخر فاتورة تم إنتاجها"""
        if self.last_invoice_id == 0:
            self.show_popup("تنبيه", "لا توجد فاتورة سابقة لطباعتها في هذه الجلسة")
            return
        
        filename = f"Invoice_Purchase_{self.last_invoice_id}.txt"
        if os.path.exists(filename):
            if platform == 'win':
                os.startfile(filename)
        else:
            self.show_popup("خطأ", "لم يتم العثور على ملف الفاتورة")

    def show_add_product_popup(self, barcode, qty):
        """نافذة سريعة لإضافة منتج جديد إذا لم يكن موجوداً في المخزن"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        grid = GridLayout(cols=2, spacing=10, size_hint_y=None, height=150)
        
        name_in = TextInput(hint_text="اسم المنتج الجديد", font_name='ArabicFont', multiline=False)
        buy_in = TextInput(text="0.00", input_filter='float', multiline=False)
        
        grid.add_widget(Label(text="الاسم:"))
        grid.add_widget(name_in)
        grid.add_widget(Label(text="سعر الشراء:"))
        grid.add_widget(buy_in)
        
        content.add_widget(grid)
        btn = Button(text="حفظ المنتج وإضافته للسلة", size_hint_y=None, height=50, background_color=(0, 0.7, 0, 1))
        content.add_widget(btn)
        
        popup = Popup(title="منتج جديد تماماً", content=content, size_hint=(0.8, 0.5))
        
        def save_and_close(inst):
            if name_in.text.strip() == "": return
            try:
                conn = get_db_connection()
                c = conn.cursor()
                c.execute("INSERT INTO products (barcode, name, buy_price, sell_price, quantity) VALUES (?, ?, ?, ?, 0)",
                          (barcode, name_in.text, float(buy_in.text), float(buy_in.text) * 1.2))
                conn.commit()
                conn.close()
                popup.dismiss()
                self.add_to_cart() # المحاولة مرة أخرى بعد الحفظ
            except Exception as e:
                print(e)

        btn.bind(on_release=save_and_close)
        popup.open()

    def remove_item(self, item_id):
        self.cart = [i for i in self.cart if i['id'] != item_id]
        self.refresh_cart_display()
        self.update_totals()

    def clear_cart(self):
        self.cart = []
        self.refresh_cart_display()
        self.discount_amount = "0.00"
        self.update_totals()

    def clear_inputs(self):
        self.barcode = ""
        self.quantity = "1"

    def go_back(self):
        self.manager.current = 'dashboard'

    def show_popup(self, title, message):
        Popup(title=title, content=Label(text=message), size_hint=(0.6, 0.4)).open()