import sqlite3
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.properties import StringProperty, NumericProperty
from kivy.logger import Logger

# ملاحظة: تأكد من أن ملف database.py موجود في نفس المجلد
try:
    from database import get_db_connection
except ImportError:
    Logger.error("OPS: database.py not found!")

class TransactionItem(BoxLayout):
    """
    هذا الكلاس يجب أن يبقى بسيطاً لأن الـ RecycleView 
    سيقوم بتعبئة الخصائص (date, type, amount, details) تلقائياً
    """
    date = StringProperty("")
    type = StringProperty("")
    amount = StringProperty("")
    details = StringProperty("")
    index = NumericProperty(0) # أضفنا هذا لعمل Zebra Stripes (لون سطر وسطر)

class CustomerAccountScreen(Screen):
    """شاشة كشف حساب الزبون"""
    
    customer_id = NumericProperty(0)
    customer_name = StringProperty("جاري التحميل...")
    current_balance = StringProperty("₪ 0.00")
    total_purchases = StringProperty("₪ 0.00")
    total_payments = StringProperty("₪ 0.00")
    total_returns = StringProperty("₪ 0.00")
    
    def on_enter(self):
        """تحديث البيانات فور دخول الشاشة"""
        if self.customer_id > 0:
            self.load_account()
    
    def set_customer(self, customer_id, customer_name):
        """تعيين الزبون من الشاشة السابقة"""
        self.customer_id = customer_id
        self.customer_name = customer_name
        # لا نحتاج لاستدعاء load_account هنا لأن on_enter ستتكفل بذلك
        
    def load_account(self):
        """تحميل كشف حساب الزبون من قاعدة البيانات"""
        try:
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            # 1. جلب المبيعات
            c.execute("""
                SELECT invoice_id, date, SUM(total) as total 
                FROM sales WHERE customer_id = ? 
                GROUP BY invoice_id ORDER BY date DESC
            """, (self.customer_id,))
            sales = c.fetchall()
            
            # 2. جلب المرتجعات
            c.execute("SELECT return_date, return_amount, reason FROM returns WHERE customer_id = ?", (self.customer_id,))
            returns = c.fetchall()
            
            # 3. جلب المدفوعات
            c.execute("SELECT amount, payment_date, notes FROM customer_payments WHERE customer_id = ?", (self.customer_id,))
            payments = c.fetchall()
            
            # حساب الإحصائيات
            sum_sales = sum(row['total'] for row in sales) if sales else 0
            sum_returns = sum(row['return_amount'] for row in returns) if returns else 0
            sum_payments = sum(row['amount'] for row in payments) if payments else 0
            
            # تحديث الواجهة (الخصائص المرتبطة بالـ KV)
            self.total_purchases = f"₪ {sum_sales:,.2f}"
            self.total_payments = f"₪ {sum_payments:,.2f}"
            self.total_returns = f"₪ {sum_returns:,.2f}"
            self.current_balance = f"₪ {(sum_sales - sum_returns - sum_payments):,.2f}"
            
            # بناء قائمة الحركات للـ RecycleView
            raw_transactions = []
            
            for row in sales:
                raw_transactions.append({
                    'date': str(row['date']),
                    'type': "فاتورة مبيعات",
                    'amount': f"{row['total']:,.2f}",
                    'details': f"رقم الفاتورة: {row['invoice_id']}"
                })
                
            for row in returns:
                raw_transactions.append({
                    'date': str(row['return_date']),
                    'type': "مرتجع مبيعات",
                    'amount': f"-{row['return_amount']:,.2f}",
                    'details': row['reason'] or "بدون سبب"
                })
                
            for row in payments:
                raw_transactions.append({
                    'date': str(row['payment_date']),
                    'type': "دفعة نقدية",
                    'amount': f"-{row['amount']:,.2f}",
                    'details': row['notes'] or "سند قبض"
                })
            
            # ترتيب الحركات من الأحدث إلى الأقدم
            raw_transactions.sort(key=lambda x: x['date'], reverse=True)
            
            # إضافة الـ index لعمل تأثير الألوان في KV
            final_data = []
            for i, trans in enumerate(raw_transactions):
                trans['index'] = i
                final_data.append(trans)
            
            # ربط البيانات بالـ RecycleView الموجود في ملف KV
            self.ids.transactions_list.data = final_data
            
            conn.close()
        except Exception as e:
            Logger.error(f"OPS: Error loading account - {e}")
            self.show_popup("خطأ في البيانات", str(e))

    def go_back(self):
        self.manager.current = 'customers'

    def show_popup(self, title, message):
        content = BoxLayout(orientation='vertical', padding=10)
        content.add_widget(Label(text=message, font_name='ArabicFont'))
        btn = Button(text="إغلاق", size_hint_y=0.4, font_name='ArabicFont')
        popup = Popup(title=title, content=content, size_hint=(0.8, 0.4))
        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        popup.open()