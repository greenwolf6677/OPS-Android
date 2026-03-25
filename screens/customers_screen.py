"""
OPS Customers Screen
شاشة إدارة الزبائن لنظام OPS
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
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, ObjectProperty
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.core.clipboard import Clipboard
from kivy.utils import platform
from kivy.animation import Animation

import sqlite3
from datetime import datetime
from database import get_db_connection

# استيراد دالة الطباعة من ملف pdf_generator
try:
    from utils.pdf_generator import create_customer_account_statement, create_customer_invoice
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    Logger.warning("OPS Customers: PDF generator not available")


class CustomerItem(BoxLayout):
    """عنصر زبون في قائمة العرض"""
    customer_id = NumericProperty(0)
    name = StringProperty("")
    phone = StringProperty("")
    address = StringProperty("")
    notes = StringProperty("")
    balance = StringProperty("0.00 ₪")
    balance_color = StringProperty("(0.2, 0.6, 0.2, 1)")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 60
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


class CustomersRecycleView(RecycleView):
    """عرض قائمة الزبائن مع إمكانية التمرير"""
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


class CustomersScreen(Screen):
    """شاشة إدارة الزبائن"""
    
    # متغيرات الحقول
    customer_id = StringProperty("")
    name = StringProperty("")
    phone = StringProperty("")
    address = StringProperty("")
    notes = StringProperty("")
    balance = StringProperty("0.00")
    payment_amount = StringProperty("")
    
    # متغيرات الإحصائيات
    total_customers = StringProperty("0")
    total_debt = StringProperty("₪ 0.00")
    debt_count = StringProperty("0")
    
    # حالة التحميل
    loading = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.all_customers = []
        self.selected_customer_id = None
        self.selected_customer_name = ""
        
    def on_enter(self):
        """عند دخول الشاشة"""
        self.load_customers()
        self.load_stats()
        Logger.info("OPS Customers: Screen entered")
    
    def load_customers(self):
        """تحميل قائمة الزبائن"""
        self.loading = True
        try:
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            query = """
                SELECT c.id, c.name, c.phone, c.address, c.notes, c.balance,
                       COALESCE((SELECT SUM(total) FROM sales WHERE customer_id = c.id), 0) as total_purchases,
                       COALESCE((SELECT SUM(amount) FROM customer_payments WHERE customer_id = c.id), 0) as total_payments
                FROM customers c
                ORDER BY c.name
            """
            c.execute(query)
            customers = c.fetchall()
            conn.close()
            
            data = []
            for row in customers:
                current_balance = row['balance'] or 0
                total_purchases = row['total_purchases'] or 0
                total_payments = row['total_payments'] or 0
                net_balance = current_balance + total_purchases - total_payments
                
                data.append({
                    'customer_id': row['id'],
                    'name': row['name'],
                    'phone': row['phone'] or "-",
                    'address': row['address'] or "-",
                    'notes': row['notes'] or "-",
                    'balance': f"{net_balance:.2f} ₪"
                })
            
            self.customers_list.data = data
            self.all_customers = data
            Logger.info(f"OPS Customers: Loaded {len(data)} customers")
            
        except Exception as e:
            Logger.error(f"OPS Customers: Error loading customers - {e}")
            self.show_popup("خطأ", f"حدث خطأ: {str(e)}")
        finally:
            self.loading = False
    
    def load_stats(self):
        """تحميل إحصائيات الزبائن"""
        try:
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            # عدد الزبائن
            c.execute("SELECT COUNT(*) as count FROM customers")
            total_customers = c.fetchone()['count']
            self.total_customers = str(total_customers)
            
            # إجمالي الديون
            c.execute("""
                SELECT SUM(balance) as total_debt FROM customers WHERE balance > 0
            """)
            total_debt_row = c.fetchone()
            total_debt = total_debt_row['total_debt'] or 0
            self.total_debt = f"₪ {total_debt:.2f}"
            
            # عدد الزبائن المدينين
            c.execute("SELECT COUNT(*) as count FROM customers WHERE balance > 0")
            debt_count = c.fetchone()['count']
            self.debt_count = str(debt_count)
            
            conn.close()
            
        except Exception as e:
            Logger.error(f"OPS Customers: Error loading stats - {e}")
    
    def clear_fields(self):
        """مسح جميع الحقول"""
        self.customer_id = ""
        self.name = ""
        self.phone = ""
        self.address = ""
        self.notes = ""
        self.balance = "0.00"
        self.payment_amount = ""
        self.selected_customer_id = None
        self.selected_customer_name = ""
    
    def select_customer(self, customer_id):
        """تحديد زبون للتحرير"""
        self.selected_customer_id = customer_id
        for customer in self.all_customers:
            if customer['customer_id'] == customer_id:
                self.customer_id = str(customer_id)
                self.name = customer['name']
                self.selected_customer_name = customer['name']
                self.phone = customer['phone'] if customer['phone'] != "-" else ""
                self.address = customer['address'] if customer['address'] != "-" else ""
                self.notes = customer['notes'] if customer['notes'] != "-" else ""
                # استخراج الرصيد الرقمي من النص
                balance_text = customer['balance']
                balance_num = balance_text.replace(' ₪', '')
                self.balance = balance_num
                break
        
        Logger.info(f"OPS Customers: Selected customer ID: {customer_id}")
    
    def add_customer(self):
        """إضافة زبون جديد"""
        name = self.name.strip()
        if not name:
            self.show_popup("تنبيه", "اسم الزبون مطلوب")
            return
        
        try:
            conn = get_db_connection()
            phone = self.phone.strip() if self.phone.strip() else ""
            address = self.address.strip() if self.address.strip() else ""
            notes = self.notes.strip() if self.notes.strip() else ""
            balance = float(self.balance) if self.balance.strip() else 0.00
            
            conn.execute("""
                INSERT INTO customers (name, phone, address, notes, balance)
                VALUES (?, ?, ?, ?, ?)
            """, (name, phone, address, notes, balance))
            conn.commit()
            conn.close()
            
            self.show_popup("نجاح", "تم إضافة الزبون بنجاح")
            self.clear_fields()
            self.load_customers()
            self.load_stats()
            
        except Exception as e:
            Logger.error(f"OPS Customers: Error adding customer - {e}")
            self.show_popup("خطأ", f"حدث خطأ: {str(e)}")
    
    def edit_customer(self):
        """تعديل بيانات الزبون"""
        if not self.selected_customer_id:
            self.show_popup("تنبيه", "اختر زبوناً أولاً")
            return
        
        name = self.name.strip()
        if not name:
            self.show_popup("تنبيه", "اسم الزبون مطلوب")
            return
        
        try:
            conn = get_db_connection()
            phone = self.phone.strip() if self.phone.strip() else ""
            address = self.address.strip() if self.address.strip() else ""
            notes = self.notes.strip() if self.notes.strip() else ""
            balance = float(self.balance) if self.balance.strip() else 0.00
            
            conn.execute("""
                UPDATE customers 
                SET name=?, phone=?, address=?, notes=?, balance=? 
                WHERE id=?
            """, (name, phone, address, notes, balance, self.selected_customer_id))
            conn.commit()
            conn.close()
            
            self.show_popup("نجاح", "تم تعديل الزبون بنجاح")
            self.clear_fields()
            self.load_customers()
            self.load_stats()
            
        except Exception as e:
            Logger.error(f"OPS Customers: Error editing customer - {e}")
            self.show_popup("خطأ", f"حدث خطأ: {str(e)}")
    
    def delete_customer(self):
        """حذف زبون"""
        if not self.selected_customer_id:
            self.show_popup("تنبيه", "اختر زبوناً أولاً")
            return
        
        # تأكيد الحذف
        self.show_confirmation_popup(
            "تأكيد الحذف",
            f"هل أنت متأكد من حذف الزبون '{self.name}'؟",
            self._delete_customer_confirm
        )
    
    def _delete_customer_confirm(self):
        """تأكيد حذف الزبون"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            # التحقق من وجود فواتير
            c.execute("SELECT COUNT(*) as count FROM sales WHERE customer_id=?", (self.selected_customer_id,))
            result = c.fetchone()
            
            if result and result[0] > 0:
                self.show_popup("تحذير", f"هذا الزبون لديه {result[0]} فاتورة. لا يمكن حذفه.")
                conn.close()
                return
            
            # حذف مدفوعات الزبون
            conn.execute("DELETE FROM customer_payments WHERE customer_id=?", (self.selected_customer_id,))
            conn.execute("DELETE FROM customers WHERE id=?", (self.selected_customer_id,))
            conn.commit()
            conn.close()
            
            self.show_popup("نجاح", "تم حذف الزبون بنجاح")
            self.clear_fields()
            self.load_customers()
            self.load_stats()
            
        except Exception as e:
            Logger.error(f"OPS Customers: Error deleting customer - {e}")
            self.show_popup("خطأ", f"حدث خطأ: {str(e)}")
    
    def add_payment(self):
        """تسجيل دفعة نقدية من الزبون"""
        if not self.selected_customer_id:
            self.show_popup("تنبيه", "اختر زبوناً أولاً")
            return
        
        amount = self.payment_amount.strip()
        if not amount:
            self.show_popup("تنبيه", "يرجى إدخال مبلغ الدفعة")
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
                INSERT INTO customer_payments (customer_id, amount, payment_date, notes)
                VALUES (?, ?, ?, ?)
            """, (self.selected_customer_id, payment_amount, 
                  datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "دفعة نقدية"))
            
            conn.commit()
            conn.close()
            
            self.show_popup("نجاح", f"تم تسجيل دفعة مبلغ {payment_amount:.2f} ₪ بنجاح")
            self.payment_amount = ""
            self.load_customers()
            self.load_stats()
            
        except Exception as e:
            Logger.error(f"OPS Customers: Error adding payment - {e}")
            self.show_popup("خطأ", f"فشل تسجيل الدفعة: {str(e)}")
    
    def view_customer_invoices(self):
        """عرض فواتير الزبون"""
        if not self.selected_customer_id:
            self.show_popup("تنبيه", "اختر زبوناً أولاً")
            return
        
        # الانتقال إلى شاشة فواتير الزبون
        self.manager.current = 'customer_invoices'
        if hasattr(self.manager.get_screen('customer_invoices'), 'set_customer'):
            self.manager.get_screen('customer_invoices').set_customer(
                self.selected_customer_id, self.name)
    
    def view_customer_payments(self):
        """عرض مدفوعات الزبون"""
        if not self.selected_customer_id:
            self.show_popup("تنبيه", "اختر زبوناً أولاً")
            return
        
        # الانتقال إلى شاشة مدفوعات الزبون
        self.manager.current = 'customer_payments'
        if hasattr(self.manager.get_screen('customer_payments'), 'set_customer'):
            self.manager.get_screen('customer_payments').set_customer(
                self.selected_customer_id, self.name)
    
    def show_customer_account(self):
        """عرض كشف حساب الزبون (عرض داخل التطبيق)"""
        if not self.selected_customer_id:
            self.show_popup("تنبيه", "اختر زبوناً أولاً")
            return
        
        # الانتقال إلى شاشة كشف حساب الزبون
        self.manager.current = 'customer_account'
        if hasattr(self.manager.get_screen('customer_account'), 'set_customer'):
            self.manager.get_screen('customer_account').set_customer(
                self.selected_customer_id, self.name)
    
    def print_customer_account(self):
        """طباعة كشف حساب الزبون PDF"""
        if not self.selected_customer_id:
            self.show_popup("تنبيه", "اختر زبوناً أولاً")
            return
        
        if not PDF_AVAILABLE:
            self.show_popup("تنبيه", "خدمة الطباعة غير متوفرة حالياً")
            return
        
        try:
            # عرض نافذة انتظار
            self.loading = True
            
            # جمع بيانات الحركات
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            # جلب المبيعات
            c.execute("""
                SELECT invoice_id, date, SUM(total) as total 
                FROM sales 
                WHERE customer_id = ? 
                GROUP BY invoice_id
                ORDER BY date
            """, (self.selected_customer_id,))
            sales = c.fetchall()
            
            # جلب المدفوعات
            c.execute("""
                SELECT amount, payment_date, notes 
                FROM customer_payments 
                WHERE customer_id = ? 
                ORDER BY payment_date
            """, (self.selected_customer_id,))
            payments = c.fetchall()
            
            # جلب المرتجعات
            try:
                c.execute("""
                    SELECT return_date, return_amount, reason 
                    FROM returns 
                    WHERE customer_id = ? 
                    ORDER BY return_date
                """, (self.selected_customer_id,))
                returns = c.fetchall()
            except:
                returns = []
            
            conn.close()
            
            # تجميع الحركات
            transactions = []
            
            for row in sales:
                transactions.append({
                    'date': row['date'],
                    'type': 'فاتورة مبيعات',
                    'amount': f"{row['total']:.2f} ₪",
                    'details': f"رقم: {row['invoice_id']}"
                })
            
            for row in returns:
                transactions.append({
                    'date': row['return_date'],
                    'type': 'مرتجع',
                    'amount': f"- {row['return_amount']:.2f} ₪",
                    'details': f"سبب: {row['reason'] or 'غير محدد'}"
                })
            
            for row in payments:
                transactions.append({
                    'date': row['payment_date'],
                    'type': 'دفعة',
                    'amount': f"- {row['amount']:.2f} ₪",
                    'details': row['notes'] or ""
                })
            
            # ترتيب حسب التاريخ
            transactions.sort(key=lambda x: x['date'])
            
            # إنشاء PDF
            result = create_customer_account_statement(
                self.selected_customer_name or self.name, 
                self.selected_customer_id, 
                transactions
            )
            
            self.loading = False
            
            if result:
                self.show_popup("نجاح", "تم إنشاء كشف الحساب بنجاح\nسيتم فتحه تلقائياً")
            else:
                self.show_popup("خطأ", "فشل إنشاء كشف الحساب")
            
        except Exception as e:
            self.loading = False
            Logger.error(f"OPS Customers: Error printing account - {e}")
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