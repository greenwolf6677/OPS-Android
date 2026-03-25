"""
OPS Supplier Account Screen
شاشة كشف حساب المورد
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.logger import Logger

import sqlite3
from datetime import datetime
from database import get_db_connection


class TransactionItem(BoxLayout):
    """عنصر حركة في الكشف"""
    date = StringProperty("")
    type = StringProperty("")
    amount = NumericProperty(0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 45
        self.padding = [5, 5]
        self.spacing = 5


class TransactionsRecycleView(RecycleView):
    """عرض قائمة الحركات"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data = []
        self.layout_manager = RecycleBoxLayout(
            default_size=(None, 45),
            default_size_hint=(1, None),
            size_hint_y=None,
            height=self.minimum_height,
            orientation='vertical'
        )
        self.add_widget(self.layout_manager)


class SupplierAccountScreen(Screen):
    """شاشة كشف حساب المورد"""
    
    supplier_id = NumericProperty(0)
    supplier_name = StringProperty("")
    total_purchases = StringProperty("₪ 0.00")
    total_payments = StringProperty("₪ 0.00")
    balance = StringProperty("₪ 0.00")
    balance_color = StringProperty("(0.2, 0.6, 0.2, 1)")
    loading = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def set_supplier(self, supplier_id, supplier_name):
        """تعيين المورد وعرض كشف حسابه"""
        self.supplier_id = supplier_id
        self.supplier_name = supplier_name
        self.load_account()
    
    def on_enter(self):
        """عند دخول الشاشة"""
        if self.supplier_id:
            self.load_account()
    
    def load_account(self):
        """تحميل كشف حساب المورد"""
        self.loading = True
        try:
            self.transactions_list.data = []
            
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            # تجميع الحركات
            transactions = []
            total_purchases = 0
            total_payments = 0
            
            # جلب فواتير المشتريات
            c.execute("""
                SELECT id, date, total FROM purchases 
                WHERE supplier_id = ? 
                ORDER BY date
            """, (self.supplier_id,))
            for row in c.fetchall():
                transactions.append({
                    'date': row['date'],
                    'type': 'فاتورة شراء',
                    'amount': row['total'],
                    'is_purchase': True
                })
                total_purchases += row['total']
            
            # جلب المدفوعات
            c.execute("""
                SELECT id, amount, payment_date FROM supplier_payments 
                WHERE supplier_id = ? 
                ORDER BY payment_date
            """, (self.supplier_id,))
            for row in c.fetchall():
                transactions.append({
                    'date': row['payment_date'],
                    'type': 'سداد',
                    'amount': row['amount'],
                    'is_payment': True
                })
                total_payments += row['amount']
            
            conn.close()
            
            # ترتيب حسب التاريخ
            transactions.sort(key=lambda x: x['date'])
            
            # عرض البيانات
            data = []
            for trans in transactions:
                data.append({
                    'date': trans['date'],
                    'type': trans['type'],
                    'amount': trans['amount']
                })
            
            self.transactions_list.data = data
            
            # تحديث الإحصائيات
            self.total_purchases = f"₪ {total_purchases:.2f}"
            self.total_payments = f"₪ {total_payments:.2f}"
            
            remaining = total_purchases - total_payments
            self.balance = f"₪ {remaining:.2f}"
            
            if remaining > 0:
                self.balance_color = "(0.8, 0.2, 0.2, 1)"  # أحمر للدين
            elif remaining < 0:
                self.balance_color = "(0.2, 0.8, 0.2, 1)"  # أخضر للرصيد الموجب
            else:
                self.balance_color = "(0.5, 0.5, 0.5, 1)"  # رمادي للصفر
            
            Logger.info(f"OPS Supplier Account: Loaded {len(transactions)} transactions")
            
        except Exception as e:
            Logger.error(f"OPS Supplier Account: Error loading account - {e}")
            self.show_popup("خطأ", f"حدث خطأ: {str(e)}")
        finally:
            self.loading = False
    
    def go_back(self):
        """العودة لشاشة الموردين"""
        self.manager.current = 'suppliers'
    
    def show_popup(self, title, message):
        """عرض نافذة منبثقة"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=message, font_name='ArabicFont', halign='center', text_size=(400, None)))
        
        btn = Button(text="موافق", size_hint_y=0.3, font_name='ArabicFont')
        popup = Popup(title=title, content=content, size_hint=(0.8, 0.5))
        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        
        popup.open()