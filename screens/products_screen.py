"""
OPS Products Screen
شاشة إدارة المنتجات لنظام OPS
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.filechooser import FileChooserListView
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, ObjectProperty
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.core.clipboard import Clipboard
from kivy.utils import platform

import sqlite3
import os
import pandas as pd
from datetime import datetime
from database import get_db_connection

# استيراد دوال PDF
try:
    from utils.pdf_generator import create_products_report
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    Logger.warning("OPS Products: PDF generator not available")

# محاولة استيراد pandas (قد لا يكون متاحاً على Android)
try:
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    Logger.warning("OPS Products: Pandas not available, Excel import disabled")


class ProductItem(BoxLayout):
    """عنصر منتج في قائمة العرض"""
    barcode = StringProperty("")
    name = StringProperty("")
    unit = StringProperty("")
    quantity = NumericProperty(0)
    buy_price = NumericProperty(0)
    sell_price = NumericProperty(0)
    is_low_stock = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 50
        self.padding = [5, 5]
        self.spacing = 5


class ProductsRecycleView(RecycleView):
    """عرض قائمة المنتجات مع إمكانية التمرير"""
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


class ProductsScreen(Screen):
    """شاشة إدارة المنتجات"""
    
    # متغيرات الحقول
    barcode = StringProperty("")
    name = StringProperty("")
    unit = StringProperty("قطعة")
    buy_price = StringProperty("0.00")
    sell_price = StringProperty("0.00")
    quantity = StringProperty("0")
    
    # متغيرات الإحصائيات
    total_products = StringProperty("0")
    total_quantity = StringProperty("0")
    total_value = StringProperty("₪ 0.00")
    
    # حالة التحميل
    loading = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.all_products = []
        self.selected_product_barcode = None
        self.units_list = ["قطعة", "كيلو", "لتر", "علبة", "كرتون", "حبة"]
        
    def on_enter(self):
        """عند دخول الشاشة"""
        self.load_stats()
        self.load_all_products()
        Logger.info("OPS Products: Screen entered")
    
    def load_stats(self):
        """تحميل إحصائيات المنتجات"""
        try:
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            # عدد المنتجات
            c.execute("SELECT COUNT(*) as count FROM products")
            total = c.fetchone()['count']
            self.total_products = str(total)
            
            # إجمالي الكميات
            c.execute("SELECT SUM(quantity) as total FROM products")
            total_qty = c.fetchone()['total'] or 0
            self.total_quantity = str(int(total_qty))
            
            # قيمة المخزون
            c.execute("SELECT SUM(buy_price * quantity) as total_value FROM products")
            total_val = c.fetchone()['total_value'] or 0
            self.total_value = f"₪ {total_val:.2f}"
            
            conn.close()
            
            # التحقق من المخزون المنخفض
            self.check_low_stock()
            
        except Exception as e:
            Logger.error(f"OPS Products: Error loading stats - {e}")
    
    def check_low_stock(self):
        """التحقق من المنتجات منخفضة المخزون"""
        try:
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT name, quantity, unit FROM products WHERE quantity <= 10 ORDER BY quantity")
            low_stock = c.fetchall()
            conn.close()
            
            if low_stock:
                message = "⚠️ تنبيه: المنتجات التالية وصلت للحد الأدنى (أقل من أو يساوي 10):\n\n"
                for item in low_stock:
                    message += f"• {item['name']}: {item['quantity']} {item['unit']}\n"
                self.show_popup("تنبيه المخزون", message)
                
        except Exception as e:
            Logger.error(f"OPS Products: Error checking low stock - {e}")
    
    def load_all_products(self):
        """تحميل جميع المنتجات للعرض"""
        self.loading = True
        try:
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            # التأكد من وجود عمود الوحدة
            try:
                c.execute("SELECT unit FROM products LIMIT 1")
            except sqlite3.OperationalError:
                c.execute("ALTER TABLE products ADD COLUMN unit TEXT DEFAULT 'قطعة'")
                conn.commit()
            
            c.execute("SELECT barcode, name, buy_price, sell_price, quantity, unit FROM products ORDER BY name")
            rows = c.fetchall()
            conn.close()
            
            data = []
            for row in rows:
                unit = row['unit'] if row['unit'] else "قطعة"
                data.append({
                    'barcode': row['barcode'],
                    'name': row['name'],
                    'unit': unit,
                    'quantity': row['quantity'],
                    'buy_price': row['buy_price'],
                    'sell_price': row['sell_price'],
                    'is_low_stock': row['quantity'] <= 10
                })
            
            self.products_list.data = data
            self.all_products = data
            Logger.info(f"OPS Products: Loaded {len(data)} products")
            
        except Exception as e:
            Logger.error(f"OPS Products: Error loading products - {e}")
            self.show_popup("خطأ", f"حدث خطأ: {str(e)}")
        finally:
            self.loading = False
    
    def clear_fields(self):
        """مسح جميع الحقول"""
        self.barcode = ""
        self.name = ""
        self.buy_price = "0.00"
        self.sell_price = "0.00"
        self.quantity = "0"
        self.unit = "قطعة"
        self.selected_product_barcode = None
    
    def load_product_by_barcode(self):
        """تحميل بيانات المنتج باستخدام الباركود"""
        barcode = self.barcode.strip()
        if not barcode:
            self.show_popup("تنبيه", "أدخل الباركود أولاً")
            return
        
        try:
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT name, buy_price, sell_price, quantity, unit FROM products WHERE barcode = ?", (barcode,))
            product = c.fetchone()
            conn.close()
            
            if product:
                self.name = product['name']
                self.buy_price = f"{product['buy_price']:.2f}"
                self.sell_price = f"{product['sell_price']:.2f}"
                self.quantity = str(product['quantity'])
                self.unit = product['unit'] if product['unit'] else "قطعة"
                self.selected_product_barcode = barcode
                self.show_popup("موجود", "المنتج موجود، يمكنك إضافة كمية إضافية")
            else:
                self.show_popup("جديد", "باركود جديد – أدخل البيانات")
                
        except Exception as e:
            Logger.error(f"OPS Products: Error loading product - {e}")
            self.show_popup("خطأ", f"حدث خطأ: {str(e)}")
    
    def save_product(self):
        """حفظ المنتج في قاعدة البيانات"""
        barcode = self.barcode.strip()
        name = self.name.strip()
        unit = self.unit.strip()
        
        try:
            buy_price = float(self.buy_price)
            sell_price = float(self.sell_price)
            add_qty = int(self.quantity)
        except ValueError:
            self.show_popup("خطأ", "تأكد من إدخال أرقام صحيحة في الأسعار والكمية")
            return
        
        if not barcode or not name:
            self.show_popup("خطأ", "الباركود واسم المنتج مطلوبين")
            return
        
        if sell_price <= buy_price:
            self.show_confirmation_popup(
                "تأكيد",
                "سعر البيع أقل من أو يساوي سعر الشراء. هل تريد المتابعة؟",
                self._save_product_confirm
            )
            return
        
        self._save_product_confirm()
    
    def _save_product_confirm(self):
        """تأكيد حفظ المنتج"""
        barcode = self.barcode.strip()
        name = self.name.strip()
        unit = self.unit.strip()
        
        try:
            buy_price = float(self.buy_price)
            sell_price = float(self.sell_price)
            add_qty = int(self.quantity)
        except ValueError:
            return
        
        try:
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            # التأكد من وجود عمود الوحدة
            try:
                c.execute("SELECT unit FROM products LIMIT 1")
            except sqlite3.OperationalError:
                c.execute("ALTER TABLE products ADD COLUMN unit TEXT DEFAULT 'قطعة'")
                conn.commit()
            
            c.execute("SELECT quantity FROM products WHERE barcode = ?", (barcode,))
            exists = c.fetchone()
            
            if exists:
                new_qty = exists['quantity'] + add_qty
                c.execute("""
                    UPDATE products 
                    SET name = ?, buy_price = ?, sell_price = ?, quantity = ?, unit = ?
                    WHERE barcode = ?
                """, (name, buy_price, sell_price, new_qty, unit, barcode))
                msg = f"تم تحديث المنتج!\nالكمية الجديدة: {new_qty} {unit}"
            else:
                c.execute("""
                    INSERT INTO products (barcode, name, buy_price, sell_price, quantity, unit)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (barcode, name, buy_price, sell_price, add_qty, unit))
                msg = f"تم إضافة المنتج بنجاح! ({unit})"
            
            conn.commit()
            conn.close()
            
            self.show_popup("نجاح", msg)
            self.clear_fields()
            self.load_stats()
            self.load_all_products()
            
        except Exception as e:
            Logger.error(f"OPS Products: Error saving product - {e}")
            self.show_popup("خطأ", f"حدث خطأ: {str(e)}")
    
    def import_from_excel(self):
        """استيراد المنتجات من ملف Excel"""
        if not PANDAS_AVAILABLE:
            self.show_popup("تنبيه", "ميزة الاستيراد من Excel غير متوفرة حالياً")
            return
        
        # عرض نافذة اختيار الملف
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        filechooser = FileChooserListView(path='/sdcard' if platform == 'android' else '/')
        content.add_widget(filechooser)
        
        buttons = BoxLayout(size_hint_y=0.3, spacing=10)
        btn_import = Button(text="استيراد", font_name='ArabicFont')
        btn_cancel = Button(text="إلغاء", font_name='ArabicFont')
        buttons.add_widget(btn_import)
        buttons.add_widget(btn_cancel)
        content.add_widget(buttons)
        
        popup = Popup(title="اختر ملف Excel", content=content, size_hint=(0.9, 0.9))
        
        def do_import(instance):
            if filechooser.selection:
                file_path = filechooser.selection[0]
                popup.dismiss()
                self._process_excel_import(file_path)
        
        btn_import.bind(on_press=do_import)
        btn_cancel.bind(on_press=popup.dismiss)
        popup.open()
    
    def _process_excel_import(self, file_path):
        """معالجة ملف Excel واستيراده"""
        try:
            self.loading = True
            df = pd.read_excel(file_path)
            
            required_columns = ['باركود', 'اسم المنتج', 'سعر الشراء', 'سعر البيع', 'الكمية المضافة']
            missing = [col for col in required_columns if col not in df.columns]
            if missing:
                self.show_popup("خطأ في الملف", f"الملف ناقص أعمدة: {', '.join(missing)}")
                self.loading = False
                return
            
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            # التأكد من وجود عمود الوحدة
            try:
                c.execute("SELECT unit FROM products LIMIT 1")
            except sqlite3.OperationalError:
                c.execute("ALTER TABLE products ADD COLUMN unit TEXT DEFAULT 'قطعة'")
                conn.commit()
            
            added, updated, errors = 0, 0, 0
            
            for _, row in df.iterrows():
                try:
                    barcode = str(row['باركود']).strip()
                    name = str(row['اسم المنتج']).strip()
                    buy_price = float(row['سعر الشراء'])
                    sell_price = float(row['سعر البيع'])
                    qty = int(row['الكمية المضافة'])
                    unit = row['الوحدة'] if 'الوحدة' in df.columns and pd.notna(row.get('الوحدة', '')) else "قطعة"
                    
                    if not barcode or not name:
                        errors += 1
                        continue
                    
                    c.execute("SELECT quantity FROM products WHERE barcode = ?", (barcode,))
                    exists = c.fetchone()
                    
                    if exists:
                        new_qty = exists['quantity'] + qty
                        c.execute("""
                            UPDATE products 
                            SET name = ?, buy_price = ?, sell_price = ?, quantity = ?, unit = ?
                            WHERE barcode = ?
                        """, (name, buy_price, sell_price, new_qty, unit, barcode))
                        updated += 1
                    else:
                        c.execute("""
                            INSERT INTO products (barcode, name, buy_price, sell_price, quantity, unit)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (barcode, name, buy_price, sell_price, qty, unit))
                        added += 1
                except Exception as e:
                    errors += 1
                    Logger.error(f"OPS Products: Error importing row - {e}")
            
            conn.commit()
            conn.close()
            
            self.show_popup("نتيجة الاستيراد", 
                          f"✅ تم الاستيراد بنجاح!\n\n"
                          f"📦 منتجات جديدة: {added}\n"
                          f"🔄 منتجات محدثة: {updated}\n"
                          f"⚠️ أخطاء: {errors}")
            
            self.load_stats()
            self.load_all_products()
            
        except Exception as e:
            Logger.error(f"OPS Products: Error processing Excel - {e}")
            self.show_popup("خطأ", f"حدث خطأ أثناء قراءة Excel:\n{str(e)}")
        finally:
            self.loading = False
    
    def print_products_report(self):
        """طباعة تقرير المنتجات PDF"""
        if not PDF_AVAILABLE:
            self.show_popup("تنبيه", "خدمة الطباعة غير متوفرة حالياً")
            return
        
        try:
            self.loading = True
            
            # جمع بيانات المنتجات
            products_data = []
            for product in self.all_products:
                products_data.append({
                    'barcode': product['barcode'],
                    'name': product['name'],
                    'unit': product['unit'],
                    'quantity': product['quantity'],
                    'buy_price': product['buy_price'],
                    'sell_price': product['sell_price']
                })
            
            result = create_products_report(products_data, f"قائمة المنتجات - {datetime.now().strftime('%Y-%m-%d')}")
            
            self.loading = False
            
            if result:
                self.show_popup("نجاح", "تم إنشاء تقرير المنتجات بنجاح\nسيتم فتحه تلقائياً")
            else:
                self.show_popup("خطأ", "فشل إنشاء تقرير المنتجات")
                
        except Exception as e:
            self.loading = False
            Logger.error(f"OPS Products: Error printing report - {e}")
            self.show_popup("خطأ", f"حدث خطأ: {str(e)}")
    
    def edit_product(self, barcode):
        """تعديل منتج"""
        for product in self.all_products:
            if product['barcode'] == barcode:
                self.barcode = product['barcode']
                self.name = product['name']
                self.unit = product['unit']
                self.buy_price = f"{product['buy_price']:.2f}"
                self.sell_price = f"{product['sell_price']:.2f}"
                self.quantity = str(product['quantity'])
                self.selected_product_barcode = barcode
                break
    
    def delete_product(self, barcode, name):
        """حذف منتج"""
        self.show_confirmation_popup(
            "تأكيد الحذف",
            f"هل أنت متأكد من حذف المنتج '{name}'؟",
            lambda: self._delete_product_confirm(barcode)
        )
    
    def _delete_product_confirm(self, barcode):
        """تأكيد حذف المنتج"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("DELETE FROM products WHERE barcode = ?", (barcode,))
            conn.commit()
            conn.close()
            
            self.show_popup("نجاح", "تم حذف المنتج بنجاح")
            self.load_stats()
            self.load_all_products()
            if self.selected_product_barcode == barcode:
                self.clear_fields()
                
        except Exception as e:
            Logger.error(f"OPS Products: Error deleting product - {e}")
            self.show_popup("خطأ", f"حدث خطأ: {str(e)}")
    
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
        
        popup = Popup(title=title, content=content, size_hint=(0.7, 0.4))
        
        def yes_action(instance):
            popup.dismiss()
            on_confirm()
        
        btn_yes.bind(on_press=yes_action)
        btn_no.bind(on_press=popup.dismiss)
        
        popup.open()