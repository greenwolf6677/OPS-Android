"""
OPS Purchases Screen
شاشة إدارة المشتريات لنظام OPS
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
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


class PurchaseItem(BoxLayout):
    """عنصر منتج في سلة المشتريات"""
    barcode = StringProperty("")
    name = StringProperty("")
    buy_price = NumericProperty(0)
    qty = NumericProperty(1)
    subtotal = NumericProperty(0)
    item_id = NumericProperty(0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 50
        self.padding = [5, 5]
        self.spacing = 5


class PurchasesRecycleView(RecycleView):
    """عرض سلة المشتريات"""
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


class PurchasesScreen(Screen):
    """شاشة إدارة المشتريات"""
    
    # متغيرات الفاتورة
    supplier_name = StringProperty("")
    total_amount = StringProperty("0.00")
    discount_amount = StringProperty("0.00")
    net_amount = StringProperty("0.00")
    
    # متغيرات الإدخال
    barcode = StringProperty("")
    quantity = StringProperty("1")
    
    # قائمة الموردين
    suppliers_list = []
    suppliers_dict = {}
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cart = []
        self.next_item_id = 1
        self.load_suppliers()
        
    def on_enter(self):
        """عند دخول الشاشة"""
        self.load_suppliers()
        self.update_totals()
        Logger.info("OPS Purchases: Screen entered")
    
    def load_suppliers(self):
        """تحميل قائمة الموردين"""
        try:
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT id, name FROM suppliers ORDER BY name")
            suppliers = c.fetchall()
            conn.close()
            
            self.suppliers_list = ["اختر المورد"] + [row['name'] for row in suppliers]
            self.suppliers_dict = {row['name']: row['id'] for row in suppliers}
            
            if suppliers:
                self.supplier_name = suppliers[0]['name']
            
            Logger.info(f"OPS Purchases: Loaded {len(suppliers)} suppliers")
            
        except Exception as e:
            Logger.error(f"OPS Purchases: Error loading suppliers - {e}")
    
    def update_totals(self):
        """تحديث إجماليات الفاتورة"""
        subtotal = sum(item['subtotal'] for item in self.cart)
        
        try:
            discount = float(self.discount_amount) if self.discount_amount else 0.0
        except ValueError:
            discount = 0.0
            self.discount_amount = "0.00"
        
        final_total = subtotal - discount
        if final_total < 0:
            final_total = 0
        
        self.total_amount = f"{subtotal:.2f}"
        self.net_amount = f"{final_total:.2f}"
    
    def add_to_cart(self):
        """إضافة منتج إلى سلة المشتريات"""
        barcode = self.barcode.strip()
        if not barcode:
            self.show_popup("تنبيه", "أدخل الباركود")
            return
        
        try:
            qty = int(self.quantity)
            if qty <= 0:
                raise ValueError
        except ValueError:
            self.show_popup("خطأ", "الكمية يجب أن تكون رقم موجب")
            self.quantity = "1"
            return
        
        # البحث عن المنتج في قاعدة البيانات
        try:
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT name, buy_price FROM products WHERE barcode = ?", (barcode,))
            product = c.fetchone()
            conn.close()
            
            if not product:
                self.show_add_product_popup(barcode, qty)
                return
            
            name = product['name']
            buy_price = product['buy_price']
            subtotal = qty * buy_price
            
            # التحقق من وجود المنتج في السلة
            for item in self.cart:
                if item['barcode'] == barcode:
                    item['qty'] += qty
                    item['subtotal'] = item['qty'] * buy_price
                    self.refresh_cart_display()
                    self.update_totals()
                    self.clear_inputs()
                    return
            
            # إضافة منتج جديد
            new_item = {
                'id': self.next_item_id,
                'barcode': barcode,
                'name': name,
                'buy_price': buy_price,
                'qty': qty,
                'subtotal': subtotal
            }
            self.cart.append(new_item)
            self.next_item_id += 1
            self.refresh_cart_display()
            self.update_totals()
            self.clear_inputs()
            
        except Exception as e:
            Logger.error(f"OPS Purchases: Error adding to cart - {e}")
            self.show_popup("خطأ", f"حدث خطأ: {str(e)}")
    
    def refresh_cart_display(self):
        """تحديث عرض السلة"""
        data = []
        for item in self.cart:
            data.append({
                'barcode': item['barcode'],
                'name': item['name'],
                'buy_price': item['buy_price'],
                'qty': item['qty'],
                'subtotal': item['subtotal'],
                'item_id': item['id']
            })
        self.cart_list.data = data
    
    def remove_item(self, item_id):
        """حذف عنصر من السلة"""
        for i, item in enumerate(self.cart):
            if item['id'] == item_id:
                del self.cart[i]
                break
        self.refresh_cart_display()
        self.update_totals()
    
    def clear_cart(self):
        """مسح السلة بالكامل"""
        self.cart = []
        self.refresh_cart_display()
        self.discount_amount = "0.00"
        self.update_totals()
    
    def clear_inputs(self):
        """مسح حقول الإدخال"""
        self.barcode = ""
        self.quantity = "1"
    
    def show_add_product_popup(self, barcode, qty):
        """عرض نافذة إضافة منتج جديد"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # عنوان
        content.add_widget(Label(text="إضافة منتج جديد", font_size=18, bold=True, 
                                  font_name='ArabicFont', size_hint_y=None, height=40))
        
        # نموذج الإدخال
        form = GridLayout(cols=2, spacing=10, size_hint_y=None, height=350)
        form.add_widget(Label(text="الباركود:", font_name='ArabicFont', halign='right'))
        barcode_display = TextInput(text=barcode, readonly=True, font_name='ArabicFont')
        form.add_widget(barcode_display)
        
        form.add_widget(Label(text="اسم المنتج:", font_name='ArabicFont', halign='right'))
        name_input = TextInput(font_name='ArabicFont')
        form.add_widget(name_input)
        
        form.add_widget(Label(text="سعر الشراء:", font_name='ArabicFont', halign='right'))
        buy_price_input = TextInput(text="0.00", font_name='ArabicFont', input_filter='float')
        form.add_widget(buy_price_input)
        
        form.add_widget(Label(text="سعر البيع:", font_name='ArabicFont', halign='right'))
        sell_price_input = TextInput(text="0.00", font_name='ArabicFont', input_filter='float')
        form.add_widget(sell_price_input)
        
        form.add_widget(Label(text="الوحدة:", font_name='ArabicFont', halign='right'))
        unit_spinner = Spinner(text="قطعة", values=["قطعة", "كيلو", "لتر", "علبة", "كرتون", "حبة"],
                               font_name='ArabicFont', size_hint_x=1)
        form.add_widget(unit_spinner)
        
        form.add_widget(Label(text="الكمية:", font_name='ArabicFont', halign='right'))
        qty_input = TextInput(text=str(qty), font_name='ArabicFont', input_filter='int')
        form.add_widget(qty_input)
        
        content.add_widget(form)
        
        # أزرار التحكم
        buttons = BoxLayout(size_hint_y=None, height=50, spacing=10)
        btn_save = Button(text="💾 حفظ وإضافة للسلة", font_name='ArabicFont', 
                          background_color=(0.2, 0.6, 0.2, 1))
        btn_cancel = Button(text="❌ إلغاء", font_name='ArabicFont', 
                            background_color=(0.6, 0.2, 0.2, 1))
        buttons.add_widget(btn_save)
        buttons.add_widget(btn_cancel)
        content.add_widget(buttons)
        
        popup = Popup(title="إضافة منتج جديد", content=content, size_hint=(0.8, 0.8))
        
        def save_new_product(instance):
            name = name_input.text.strip()
            try:
                buy_price = float(buy_price_input.text)
                sell_price = float(sell_price_input.text)
                stock = int(qty_input.text)
                unit = unit_spinner.text
            except ValueError:
                self.show_popup("خطأ", "الأسعار والكمية يجب أن تكون أرقام صحيحة")
                return
            
            if not name or buy_price <= 0 or sell_price <= 0 or stock < 0:
                self.show_popup("خطأ", "البيانات غير كاملة أو خاطئة")
                return
            
            try:
                conn = get_db_connection()
                c = conn.cursor()
                
                # التحقق من وجود عمود الوحدة
                try:
                    c.execute("SELECT unit FROM products LIMIT 1")
                except sqlite3.OperationalError:
                    c.execute("ALTER TABLE products ADD COLUMN unit TEXT DEFAULT 'قطعة'")
                    conn.commit()
                
                c.execute("""
                    INSERT INTO products (barcode, name, buy_price, sell_price, quantity, unit)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (barcode, name, buy_price, sell_price, stock, unit))
                conn.commit()
                conn.close()
                
                self.show_popup("نجاح", f"تم إضافة المنتج {name} بنجاح")
                
                # إضافة للسلة
                subtotal = qty * buy_price
                new_item = {
                    'id': self.next_item_id,
                    'barcode': barcode,
                    'name': name,
                    'buy_price': buy_price,
                    'qty': qty,
                    'subtotal': subtotal
                }
                self.cart.append(new_item)
                self.next_item_id += 1
                self.refresh_cart_display()
                self.update_totals()
                self.clear_inputs()
                
                popup.dismiss()
                
            except sqlite3.IntegrityError:
                self.show_popup("خطأ", "هذا الباركود موجود مسبقاً")
            except Exception as e:
                Logger.error(f"OPS Purchases: Error saving new product - {e}")
                self.show_popup("خطأ", f"حدث خطأ: {str(e)}")
        
        btn_save.bind(on_press=save_new_product)
        btn_cancel.bind(on_press=popup.dismiss)
        
        popup.open()
    
    def finish_purchase(self):
        """إنهاء عملية الشراء"""
        if not self.cart:
            self.show_popup("تنبيه", "سلة المشتريات فارغة!")
            return
        
        supplier_name = self.supplier_name
        if not supplier_name or supplier_name == "اختر المورد":
            self.show_popup("تنبيه", "اختر المورد أولاً")
            return
        
        supplier_id = self.suppliers_dict.get(supplier_name)
        if not supplier_id:
            self.show_popup("تنبيه", "المورد غير موجود")
            return
        
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        final_total = float(self.net_amount)
        discount_val = self.discount_amount
        
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute("""
                INSERT INTO purchases (date, supplier_id, total, notes)
                VALUES (?, ?, ?, ?)
            """, (date_str, supplier_id, final_total, f"فاتورة شراء - خصم: {discount_val} ₪"))
            
            purchase_id = c.lastrowid
            
            for item in self.cart:
                c.execute("""
                    INSERT INTO purchase_items (purchase_id, barcode, quantity, buy_price, subtotal)
                    VALUES (?, ?, ?, ?, ?)
                """, (purchase_id, item['barcode'], item['qty'], item['buy_price'], item['subtotal']))
                
                c.execute("UPDATE products SET quantity = quantity + ? WHERE barcode = ?",
                          (item['qty'], item['barcode']))
            
            conn.commit()
            conn.close()
            
            self.show_popup("نجاح", f"✅ تم تسجيل فاتورة الشراء بنجاح!\nالمجموع النهائي: {final_total} ₪")
            
            # مسح السلة
            self.cart = []
            self.refresh_cart_display()
            self.discount_amount = "0.00"
            self.update_totals()
            self.clear_inputs()
            
        except Exception as e:
            Logger.error(f"OPS Purchases: Error finishing purchase - {e}")
            self.show_popup("خطأ", f"حدث خطأ أثناء التسجيل:\n{str(e)}")
    
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