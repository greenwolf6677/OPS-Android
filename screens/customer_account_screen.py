"""
OPS Customer Account Screen
شاشة كشف حساب الزبون لنظام OPS
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.properties import StringProperty, NumericProperty
from kivy.logger import Logger

import sqlite3
from datetime import datetime
from database import get_db_connection


class TransactionItem(BoxLayout):
    """عنصر حركة في الكشف"""
    date = StringProperty("")
    type = StringProperty("")
    amount = StringProperty("")
    details = StringProperty("")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 50
        self.padding = [5, 5]
        self.spacing = 5


class TransactionsRecycleView(RecycleView):
    """عرض قائمة الحركات"""
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


class CustomerAccountScreen(Screen):
    """شاشة كشف حساب الزبون"""
    
    customer_id = NumericProperty(0)
    customer_name = StringProperty("")
    current_balance = StringProperty("₪ 0.00")
    total_purchases = StringProperty("₪ 0.00")
    total_payments = StringProperty("₪ 0.00")
    total_returns = StringProperty("₪ 0.00")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
    def set_customer(self, customer_id, customer_name):
        """تعيين الزبون وعرض كشف حسابه"""
        self.customer_id = customer_id
        self.customer_name = customer_name
        self.load_account()
        
    def on_enter(self):
        """عند دخول الشاشة"""
        if self.customer_id:
            self.load_account()
    
    def load_account(self):
        """تحميل كشف حساب الزبون"""
        try:
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            # جلب فواتير المبيعات
            c.execute("""
                SELECT invoice_id, date, SUM(total) as total, payment_method 
                FROM sales 
                WHERE customer_id = ? 
                GROUP BY invoice_id
                ORDER BY date
            """, (self.customer_id,))
            sales = c.fetchall()
            
            # جلب المرتجعات
            try:
                c.execute("""
                    SELECT id, return_date, return_amount, reason 
                    FROM returns 
                    WHERE customer_id = ? 
                    ORDER BY return_date
                """, (self.customer_id,))
                returns = c.fetchall()
            except:
                returns = []
            
            # جلب المدفوعات
            c.execute("""
                SELECT id, amount, payment_date, notes 
                FROM customer_payments 
                WHERE customer_id = ? 
                ORDER BY payment_date
            """, (self.customer_id,))
            payments = c.fetchall()
            
            # حساب المجاميع
            total_sales = sum(row['total'] for row in sales) if sales else 0
            total_returns_sum = sum(row['return_amount'] for row in returns) if returns else 0
            total_payments_sum = sum(row['amount'] for row in payments) if payments else 0
            
            # جلب الرصيد الحالي من جدول الزبائن
            c.execute("SELECT balance FROM customers WHERE id = ?", (self.customer_id,))
            cust = c.fetchone()
            current_balance = cust['balance'] if cust else 0
            net_balance = current_balance + total_sales - total_returns_sum - total_payments_sum
            
            self.total_purchases = f"₪ {total_sales:.2f}"
            self.total_payments = f"₪ {total_payments_sum:.2f}"
            self.total_returns = f"₪ {total_returns_sum:.2f}"
            self.current_balance = f"₪ {net_balance:.2f}"
            
            # تجميع الحركات
            transactions = []
            
            # إضافة فواتير المبيعات
            for row in sales:
                transactions.append({
                    'date': row['date'],
                    'type': "فاتورة مبيعات",
                    'amount': f"{row['total']:.2f} ₪",
                    'details': f"رقم: {row['invoice_id']}"
                })
            
            # إضافة المرتجعات
            for row in returns:
                transactions.append({
                    'date': row['return_date'],
                    'type': "مرتجع",
                    'amount': f"- {row['return_amount']:.2f} ₪",
                    'details': f"سبب: {row['reason'] or 'غير محدد'}"
                })
            
            # إضافة المدفوعات
            for row in payments:
                transactions.append({
                    'date': row['payment_date'],
                    'type': "دفعة",
                    'amount': f"- {row['amount']:.2f} ₪",
                    'details': row['notes'] or ""
                })
            
            # ترتيب حسب التاريخ
            transactions.sort(key=lambda x: x['date'])
            
            data = []
            for trans in transactions:
                data.append({
                    'date': trans['date'],
                    'type': trans['type'],
                    'amount': trans['amount'],
                    'details': trans['details']
                })
            
            self.transactions_list.data = data
            conn.close()
            
            Logger.info(f"OPS Customer Account: Loaded account for {self.customer_name}")
            
        except Exception as e:
            Logger.error(f"OPS Customer Account: Error loading account - {e}")
            self.show_popup("خطأ", f"حدث خطأ: {str(e)}")
    
    def go_back(self):
        """العودة لشاشة الزبائن"""
        self.manager.current = 'customers'
    
    def show_popup(self, title, message):
        """عرض نافذة منبثقة"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=message, font_name='ArabicFont', halign='center'))
        
        btn = Button(text="موافق", size_hint_y=0.3, font_name='ArabicFont')
        popup = Popup(title=title, content=content, size_hint=(0.7, 0.4))
        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        
        popup.open()