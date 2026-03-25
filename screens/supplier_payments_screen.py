"""
OPS Supplier Payments Screen
شاشة عرض مدفوعات المورد
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


class PaymentItem(BoxLayout):
    """عنصر دفعة في القائمة"""
    amount = NumericProperty(0)
    date = StringProperty("")
    payment_id = NumericProperty(0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 45
        self.padding = [5, 5]
        self.spacing = 5


class PaymentsRecycleView(RecycleView):
    """عرض قائمة المدفوعات"""
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


class SupplierPaymentsScreen(Screen):
    """شاشة عرض مدفوعات المورد"""
    
    supplier_id = NumericProperty(0)
    supplier_name = StringProperty("")
    total_paid = StringProperty("₪ 0.00")
    loading = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def set_supplier(self, supplier_id, supplier_name):
        """تعيين المورد وعرض مدفوعاته"""
        self.supplier_id = supplier_id
        self.supplier_name = supplier_name
        self.load_payments()
    
    def on_enter(self):
        """عند دخول الشاشة"""
        if self.supplier_id:
            self.load_payments()
    
    def load_payments(self):
        """تحميل مدفوعات المورد"""
        self.loading = True
        try:
            self.payments_list.data = []
            
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            c.execute("""
                SELECT id, amount, payment_date FROM supplier_payments 
                WHERE supplier_id = ? 
                ORDER BY payment_date DESC
            """, (self.supplier_id,))
            
            payments = c.fetchall()
            conn.close()
            
            total = 0
            data = []
            for row in payments:
                data.append({
                    'payment_id': row['id'],
                    'amount': row['amount'],
                    'date': row['payment_date']
                })
                total += row['amount']
            
            self.payments_list.data = data
            self.total_paid = f"₪ {total:.2f}"
            Logger.info(f"OPS Supplier Payments: Loaded {len(data)} payments")
            
        except Exception as e:
            Logger.error(f"OPS Supplier Payments: Error loading payments - {e}")
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