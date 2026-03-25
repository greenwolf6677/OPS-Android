"""
OPS Suppliers Screen
شاشة إدارة الموردين والديون لنظام OPS
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

# استيراد دوال PDF
try:
    from utils.pdf_generator import create_supplier_account_statement
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    Logger.warning("OPS Suppliers: PDF generator not available")


class SupplierItem(BoxLayout):
    """عنصر مورد في قائمة العرض"""
    supplier_id = NumericProperty(0)
    name = StringProperty("")
    mobile = StringProperty("")
    address = StringProperty("")
    notes = StringProperty("")
    balance = StringProperty("0.00 ₪")
    balance_color = StringProperty("(0.2, 0.6, 0.2, 1)")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 50
        self.padding = [5, 5]
        self.spacing = 5
        self.bind(balance=self.update_balance_color)
    
    def update_balance_color(self, instance, value):
        """تحديث لون الرصيد حسب قيمته"""
        try:
            balance_num = float(value.replace(' ₪', ''))
            if balance_num > 0:
                self.balance_color = "(0.8, 0.2, 0.2, 1)"  # أحمر للدين
            elif balance_num < 0:
                self.balance_color = "(0.2, 0.8, 0.2, 1)"  # أخضر للرصيد الموجب
            else:
                self.balance_color = "(0.5, 0.5, 0.5, 1)"  # رمادي للصفر
        except:
            pass


class SuppliersRecycleView(RecycleView):
    """عرض قائمة الموردين"""
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


class SuppliersScreen(Screen):
    """شاشة إدارة الموردين والديون"""
    
    # متغيرات الحقول
    supplier_id = StringProperty("")
    name = StringProperty("")
    mobile = StringProperty("")
    address = StringProperty("")
    notes = StringProperty("")
    payment_amount = StringProperty("")
    
    # متغيرات الإحصائيات
    total_debt = StringProperty("₪ 0.00")
    total_suppliers = StringProperty("0")
    avg_debt = StringProperty("₪ 0.00")
    
    # حالة التحميل
    loading = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.all_suppliers = []
        self.selected_supplier_id = None
        self.selected_supplier_name = ""
        
    def on_enter(self):
        """عند دخول الشاشة"""
        self.load_suppliers()
        self.update_statistics()
        Logger.info("OPS Suppliers: Screen entered")
    
    def update_statistics(self):
        """تحديث إحصائيات الديون"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            # حساب إجمالي الديون
            c.execute("""
                SELECT COALESCE(SUM((SELECT COALESCE(SUM(total), 0) FROM purchases WHERE supplier_id = s.id) - 
                               COALESCE((SELECT SUM(amount) FROM supplier_payments WHERE supplier_id = s.id), 0)), 0) as total_debt
                FROM suppliers s
            """)
            total_debt_val = c.fetchone()[0] or 0
            self.total_debt = f"₪ {total_debt_val:.2f}"
            
            # حساب عدد الموردين
            c.execute("SELECT COUNT(*) FROM suppliers")
            total_suppliers_val = c.fetchone()[0] or 0
            self.total_suppliers = str(total_suppliers_val)
            
            # حساب متوسط الدين
            if total_suppliers_val > 0:
                avg_debt_val = total_debt_val / total_suppliers_val
            else:
                avg_debt_val = 0
            self.avg_debt = f"₪ {avg_debt_val:.2f}"
            
            conn.close()
            
        except Exception as e:
            Logger.error(f"OPS Suppliers: Error updating statistics - {e}")
    
    def load_suppliers(self):
        """تحميل قائمة الموردين"""
        self.loading = True
        try:
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            query = """
                SELECT s.id, s.notes, s.address, s.phone as mobile, s.name,
                (COALESCE((SELECT SUM(total) FROM purchases WHERE supplier_id = s.id), 0) - 
                 COALESCE((SELECT SUM(amount) FROM supplier_payments WHERE supplier_id = s.id), 0)) as balance
                FROM suppliers s ORDER BY s.name
            """
            c.execute(query)
            suppliers = c.fetchall()
            conn.close()
            
            data = []
            for row in suppliers:
                data.append({
                    'supplier_id': row['id'],
                    'name': row['name'],
                    'mobile': row['mobile'] or "-",
                    'address': row['address'] or "-",
                    'notes': row['notes'] or "-",
                    'balance': f"{row['balance']:.2f} ₪"
                })
            
            self.suppliers_list.data = data
            self.all_suppliers = data
            self.update_statistics()
            Logger.info(f"OPS Suppliers: Loaded {len(data)} suppliers")
            
        except Exception as e:
            Logger.error(f"OPS Suppliers: Error loading suppliers - {e}")
            self.show_popup("خطأ", f"حدث خطأ: {str(e)}")
        finally:
            self.loading = False
    
    def clear_fields(self):
        """مسح جميع الحقول"""
        self.supplier_id = ""
        self.name = ""
        self.mobile = ""
        self.address = ""
        self.notes = ""
        self.payment_amount = ""
        self.selected_supplier_id = None
        self.selected_supplier_name = ""
    
    def select_supplier(self, supplier_id):
        """تحديد مورد للتحرير"""
        self.selected_supplier_id = supplier_id
        for supplier in self.all_suppliers:
            if supplier['supplier_id'] == supplier_id:
                self.supplier_id = str(supplier_id)
                self.name = supplier['name']
                self.selected_supplier_name = supplier['name']
                self.mobile = supplier['mobile'] if supplier['mobile'] != "-" else ""
                self.address = supplier['address'] if supplier['address'] != "-" else ""
                self.notes = supplier['notes'] if supplier['notes'] != "-" else ""
                break
        
        Logger.info(f"OPS Suppliers: Selected supplier ID: {supplier_id}")
    
    def add_supplier(self):
        """إضافة مورد جديد"""
        name = self.name.strip()
        if not name:
            self.show_popup("تنبيه", "اسم المورد مطلوب")
            return
        
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            address = self.address.strip() if self.address.strip() else ""
            mobile = self.mobile.strip() if self.mobile.strip() else ""
            notes = self.notes.strip() if self.notes.strip() else ""
            
            sql = "INSERT INTO suppliers (name, address, phone, notes) VALUES (?, ?, ?, ?)"
            c.execute(sql, (name, address, mobile, notes))
            conn.commit()
            conn.close()
            
            self.show_popup("نجاح", "تم إضافة المورد بنجاح")
            self.clear_fields()
            self.load_suppliers()
            self.update_statistics()
            
        except Exception as e:
            Logger.error(f"OPS Suppliers: Error adding supplier - {e}")
            self.show_popup("خطأ", f"حدث خطأ: {str(e)}")
    
    def edit_supplier(self):
        """تعديل بيانات المورد"""
        if not self.selected_supplier_id:
            self.show_popup("تنبيه", "اختر مورداً أولاً")
            return
        
        name = self.name.strip()
        if not name:
            self.show_popup("تنبيه", "اسم المورد مطلوب")
            return
        
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            address = self.address.strip() if self.address.strip() else ""
            mobile = self.mobile.strip() if self.mobile.strip() else ""
            notes = self.notes.strip() if self.notes.strip() else ""
            
            c.execute("""
                UPDATE suppliers SET name=?, address=?, phone=?, notes=? WHERE id=?
            """, (name, address, mobile, notes, self.selected_supplier_id))
            conn.commit()
            conn.close()
            
            self.show_popup("نجاح", "تم تحديث بيانات المورد")
            self.clear_fields()
            self.load_suppliers()
            self.update_statistics()
            
        except Exception as e:
            Logger.error(f"OPS Suppliers: Error editing supplier - {e}")
            self.show_popup("خطأ", f"حدث خطأ: {str(e)}")
    
    def delete_supplier(self):
        """حذف مورد"""
        if not self.selected_supplier_id:
            self.show_popup("تنبيه", "اختر مورداً أولاً")
            return
        
        self.show_confirmation_popup(
            "تأكيد الحذف",
            f"هل أنت متأكد من حذف المورد '{self.name}'؟",
            self._delete_supplier_confirm
        )
    
    def _delete_supplier_confirm(self):
        """تأكيد حذف المورد"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("DELETE FROM suppliers WHERE id=?", (self.selected_supplier_id,))
            conn.commit()
            conn.close()
            
            self.show_popup("نجاح", "تم حذف المورد بنجاح")
            self.clear_fields()
            self.load_suppliers()
            self.update_statistics()
            
        except Exception as e:
            Logger.error(f"OPS Suppliers: Error deleting supplier - {e}")
            self.show_popup("خطأ", f"حدث خطأ: {str(e)}")
    
    def add_payment(self):
        """تسجيل سداد نقدي للمورد"""
        if not self.selected_supplier_id:
            self.show_popup("تنبيه", "اختر مورداً أولاً لتسجيل السداد")
            return
        
        amount = self.payment_amount.strip()
        if not amount:
            self.show_popup("تنبيه", "يرجى إدخال مبلغ السداد")
            return
        
        try:
            payment_amount = float(amount)
            if payment_amount <= 0:
                self.show_popup("تنبيه", "يرجى إدخال مبلغ صحيح")
                return
        except ValueError:
            self.show_popup("تنبيه", "يرجى إدخال رقم صحيح")
            return
        
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute("""
                INSERT INTO supplier_payments (supplier_id, amount, payment_date, notes)
                VALUES (?, ?, ?, ?)
            """, (self.selected_supplier_id, payment_amount, 
                  datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "سداد نقدي"))
            
            conn.commit()
            conn.close()
            
            self.show_popup("نجاح", f"تم تسجيل سداد مبلغ {payment_amount:.2f} ₪ بنجاح")
            self.payment_amount = ""
            self.load_suppliers()
            self.update_statistics()
            
        except Exception as e:
            Logger.error(f"OPS Suppliers: Error adding payment - {e}")
            self.show_popup("خطأ", f"فشل تسجيل السداد: {str(e)}")
    
    def show_supplier_invoices(self):
        """عرض فواتير المورد"""
        if not self.selected_supplier_id:
            self.show_popup("تنبيه", "اختر مورداً أولاً")
            return
        
        # الانتقال إلى شاشة فواتير المورد
        self.manager.current = 'supplier_invoices'
        if hasattr(self.manager.get_screen('supplier_invoices'), 'set_supplier'):
            self.manager.get_screen('supplier_invoices').set_supplier(
                self.selected_supplier_id, self.selected_supplier_name)
    
    def show_supplier_payments(self):
        """عرض مدفوعات المورد"""
        if not self.selected_supplier_id:
            self.show_popup("تنبيه", "اختر مورداً أولاً")
            return
        
        # الانتقال إلى شاشة مدفوعات المورد
        self.manager.current = 'supplier_payments'
        if hasattr(self.manager.get_screen('supplier_payments'), 'set_supplier'):
            self.manager.get_screen('supplier_payments').set_supplier(
                self.selected_supplier_id, self.selected_supplier_name)
    
    def show_supplier_account(self):
        """عرض كشف حساب المورد"""
        if not self.selected_supplier_id:
            self.show_popup("تنبيه", "اختر مورداً أولاً")
            return
        
        # الانتقال إلى شاشة كشف حساب المورد
        self.manager.current = 'supplier_account'
        if hasattr(self.manager.get_screen('supplier_account'), 'set_supplier'):
            self.manager.get_screen('supplier_account').set_supplier(
                self.selected_supplier_id, self.selected_supplier_name)
    
    def print_supplier_account(self):
        """طباعة كشف حساب المورد PDF"""
        if not self.selected_supplier_id:
            self.show_popup("تنبيه", "اختر مورداً أولاً")
            return
        
        if not PDF_AVAILABLE:
            self.show_popup("تنبيه", "خدمة الطباعة غير متوفرة حالياً")
            return
        
        try:
            self.loading = True
            
            # جمع بيانات الحركات
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            # جلب فواتير المشتريات
            c.execute("SELECT id, date, total FROM purchases WHERE supplier_id = ? ORDER BY date", 
                     (self.selected_supplier_id,))
            purchases = c.fetchall()
            
            # جلب المدفوعات
            c.execute("SELECT payment_date, amount FROM supplier_payments WHERE supplier_id = ? ORDER BY payment_date", 
                     (self.selected_supplier_id,))
            payments = c.fetchall()
            
            conn.close()
            
            # تجميع الحركات
            transactions = []
            
            for row in purchases:
                transactions.append({
                    'date': row['date'],
                    'type': "فاتورة شراء",
                    'amount': row['total'],
                    'is_purchase': True
                })
            
            for row in payments:
                transactions.append({
                    'date': row['payment_date'],
                    'type': "سداد",
                    'amount': row['amount'],
                    'is_payment': True
                })
            
            # ترتيب حسب التاريخ
            transactions.sort(key=lambda x: x['date'])
            
            # إنشاء PDF
            result = create_supplier_account_statement(
                self.selected_supplier_name,
                self.selected_supplier_id,
                transactions
            )
            
            self.loading = False
            
            if result:
                self.show_popup("نجاح", "تم إنشاء كشف الحساب بنجاح\nسيتم فتحه تلقائياً")
            else:
                self.show_popup("خطأ", "فشل إنشاء كشف الحساب")
                
        except Exception as e:
            self.loading = False
            Logger.error(f"OPS Suppliers: Error printing account - {e}")
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