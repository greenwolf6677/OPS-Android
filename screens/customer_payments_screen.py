import sqlite3
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.properties import StringProperty, NumericProperty
from kivy.logger import Logger

try:
    from database import get_db_connection
except ImportError:
    Logger.error("OPS: database.py not found!")

class PaymentItem(BoxLayout):
    """
    عنصر دفعة في القائمة.
    يتم ربط الخصائص تلقائياً من خلال الـ RecycleView.
    """
    amount = StringProperty("")
    date = StringProperty("")
    notes = StringProperty("")
    index = NumericProperty(0) # للتحكم في لون السطر (Zebra Stripes)

class CustomerPaymentsScreen(Screen):
    """شاشة عرض مدفوعات الزبون"""
    
    customer_id = NumericProperty(0)
    customer_name = StringProperty("جاري التحميل...")
    total_paid = StringProperty("₪ 0.00")
    
    def on_enter(self):
        """تحديث البيانات عند فتح الشاشة"""
        if self.customer_id > 0:
            self.load_payments()
    
    def set_customer(self, customer_id, customer_name):
        """تعيين الزبون المستهدف"""
        self.customer_id = customer_id
        self.customer_name = customer_name
        
    def load_payments(self):
        """جلب بيانات المدفوعات من قاعدة البيانات"""
        try:
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            c.execute("""
                SELECT amount, payment_date, notes 
                FROM customer_payments 
                WHERE customer_id = ? 
                ORDER BY payment_date DESC
            """, (self.customer_id,))
            
            rows = c.fetchall()
            conn.close()
            
            total_sum = 0
            final_data = []
            
            for i, row in enumerate(rows):
                amount_val = row['amount']
                total_sum += amount_val
                
                final_data.append({
                    'amount': f"{amount_val:,.2f} ₪",
                    'date': str(row['payment_date']),
                    'notes': row['notes'] or "-",
                    'index': i
                })
            
            # تحديث الـ RecycleView والملخص
            self.ids.payments_list.data = final_data
            self.total_paid = f"₪ {total_sum:,.2f}"
            
            Logger.info(f"OPS: Loaded {len(final_data)} payments for {self.customer_name}")
            
        except Exception as e:
            Logger.error(f"OPS: Error loading payments - {e}")
            self.show_popup("خطأ في الاتصال", "تعذر جلب سجل المدفوعات")

    def go_back(self):
        """العودة لشاشة إدارة الزبائن"""
        self.manager.current = 'customers'

    def show_popup(self, title, message):
        """نافذة تنبيه بسيطة"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=message, font_name='ArabicFont'))
        btn = Button(text="إغلاق", size_hint_y=0.4, font_name='ArabicFont')
        popup = Popup(title=title, content=content, size_hint=(0.7, 0.3))
        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        popup.open()