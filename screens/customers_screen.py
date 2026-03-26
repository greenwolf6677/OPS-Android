from kivy.uix.screenmanager import Screen
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, NumericProperty, ListProperty
from kivy.logger import Logger
import sqlite3
from database import get_db_connection

class PaymentPopup(BoxLayout):
    """نافذة منبثقة لتسجيل دفعة مالية من زبون"""
    customer_id = StringProperty("")
    customer_name = StringProperty("")
    callback = None 

    def save_payment(self, amount, notes):
        if not amount or float(amount) <= 0: return
        try:
            conn = get_db_connection()
            conn.execute("INSERT INTO customer_payments (customer_id, amount, date, notes) VALUES (?, ?, date('now'), ?)",
                         (self.customer_id, float(amount), notes))
            conn.commit()
            conn.close()
            if self.callback: self.callback()
        except Exception as e:
            Logger.error(f"Customers: Error saving payment - {e}")

class CustomersScreen(Screen):
    customer_id = StringProperty("")
    customer_name = StringProperty("")
    phone = StringProperty("")
    address = StringProperty("")
    notes = StringProperty("")
    balance = StringProperty("0.00")
    
    total_customers = StringProperty("0")
    total_debt = StringProperty("0.00 ₪")

    def on_enter(self):
        self.load_customers()

    def load_customers(self):
        """تحميل الزبائن مع حساب الرصيد النهائي لكل واحد"""
        try:
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            # الاستعلام يحسب: الرصيد الابتدائي + المبيعات - المرتجعات - الدفعات
            query = """
                SELECT *, 
                (balance + 
                    COALESCE((SELECT SUM(total) FROM sales WHERE customer_id = customers.id), 0) - 
                    COALESCE((SELECT SUM(return_amount) FROM returns WHERE customer_id = customers.id), 0) -
                    COALESCE((SELECT SUM(amount) FROM customer_payments WHERE customer_id = customers.id), 0)
                ) as net_balance
                FROM customers ORDER BY name ASC
            """
            rows = conn.execute(query).fetchall()
            
            self.ids.customers_rv.data = [{
                'c_id': str(row['id']),
                'c_name': str(row['name']),
                'c_phone': str(row['phone'] or ""),
                'c_address': str(row['address'] or ""),
                'c_notes': str(row['notes'] or ""),
                'c_initial': str(row['balance']),
                'c_balance': f"{row['net_balance']:.2f} ₪",
                'c_color': [0.8, 0.2, 0.2, 1] if row['net_balance'] > 0 else [0.2, 0.7, 0.2, 1]
            } for row in rows]
            
            self.total_customers = str(len(rows))
            total_sum = sum(row['net_balance'] for row in rows)
            self.total_debt = f"{total_sum:.2f} ₪"
            conn.close()
        except Exception as e:
            Logger.error(f"Customers: Load Error - {e}")

    def select_customer_for_edit(self, data):
        """سحب بيانات الزبون من القائمة للحقول العلوية للتعديل"""
        self.customer_id = data['c_id']
        self.customer_name = data['c_name']
        self.phone = data['c_phone']
        self.address = data['c_address']
        self.notes = data['c_notes']
        self.balance = data['c_initial']

    def save_customer(self):
        """حفظ زبون جديد أو تحديث بيانات زبون حالي"""
        if not self.customer_name.strip(): return
        try:
            conn = get_db_connection()
            if self.customer_id: # تحديث
                conn.execute("UPDATE customers SET name=?, phone=?, address=?, notes=?, balance=? WHERE id=?",
                             (self.customer_name, self.phone, self.address, self.notes, float(self.balance or 0), self.customer_id))
            else: # إضافة جديد
                conn.execute("INSERT INTO customers (name, phone, address, notes, balance) VALUES (?,?,?,?,?)",
                             (self.customer_name, self.phone, self.address, self.notes, float(self.balance or 0)))
            conn.commit()
            conn.close()
            self.clear_fields()
            self.load_customers()
        except Exception as e:
            Logger.error(f"Customers: Save Error - {e}")

    def delete_customer(self, c_id):
        """حذف زبون"""
        try:
            conn = get_db_connection()
            conn.execute("DELETE FROM customers WHERE id=?", (c_id,))
            conn.commit()
            conn.close()
            self.load_customers()
        except Exception as e:
            Logger.error(f"Customers: Delete Error - {e}")

    def show_payment_popup(self):
        """فتح نافذة القبض النقدي"""
        if not self.customer_id: return
        content = PaymentPopup(customer_id=self.customer_id, customer_name=self.customer_name, callback=self.load_customers)
        self._popup = Popup(title="تسجيل دفعة نقدية", content=content, size_hint=(0.9, 0.5))
        self._popup.open()

    def clear_fields(self):
        self.customer_id = ""
        self.customer_name = ""
        self.phone = ""
        self.address = ""
        self.notes = ""
        self.balance = "0.00"

    def view_invoices(self, c_id):
        """الانتقال لشاشة عرض الفواتير الخاصة بالزبون"""
        # تأكد أن لديك شاشة باسم 'customer_invoices' في ScreenManager
        self.manager.current = 'customer_invoices'
        self.manager.get_screen('customer_invoices').customer_id = c_id