"""
OPS Debt Report Screen
شاشة تقرير الديون (زبائن وموردين)
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.logger import Logger

import sqlite3
from datetime import datetime
from database import get_db_connection


class DebtItem(BoxLayout):
    """عنصر مدين في قائمة الديون"""
    debt_id = NumericProperty(0)
    name = StringProperty("")
    phone = StringProperty("")
    balance = StringProperty("")
    total_purchases = StringProperty("")
    total_payments = StringProperty("")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 50
        self.padding = [5, 5]
        self.spacing = 5


class DebtRecycleView(RecycleView):
    """عرض قائمة الديون"""
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


class DebtReportScreen(Screen):
    """شاشة تقرير الديون"""
    
    # متغيرات الإحصائيات (الزبائن)
    total_customer_debt = StringProperty("₪ 0.00")
    debt_customers_count = StringProperty("0")
    
    # متغيرات الإحصائيات (الموردين)
    total_supplier_debt = StringProperty("₪ 0.00")
    debt_suppliers_count = StringProperty("0")
    
    # حالة التحميل
    loading = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.load_customer_debt()
        self.load_supplier_debt()
    
    def on_enter(self):
        """عند دخول الشاشة"""
        self.load_customer_debt()
        self.load_supplier_debt()
        Logger.info("OPS Debt Report: Screen entered")
    
    def load_customer_debt(self):
        """تحميل ديون الزبائن"""
        self.loading = True
        try:
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            query = """
                SELECT 
                    c.id,
                    c.name,
                    c.phone,
                    c.balance,
                    COALESCE((SELECT SUM(total) FROM sales WHERE customer_id = c.id), 0) as total_purchases,
                    COALESCE((SELECT SUM(amount) FROM customer_payments WHERE customer_id = c.id), 0) as total_payments
                FROM customers c
                WHERE c.balance > 0 OR (SELECT SUM(total) FROM sales WHERE customer_id = c.id) > 
                      (SELECT SUM(amount) FROM customer_payments WHERE customer_id = c.id)
                ORDER BY c.balance DESC
            """
            c.execute(query)
            customers = c.fetchall()
            
            data = []
            total_debt = 0
            debt_count = 0
            
            for row in customers:
                net_debt = row['balance'] + row['total_purchases'] - row['total_payments']
                if net_debt > 0:
                    data.append({
                        'debt_id': row['id'],
                        'name': row['name'],
                        'phone': row['phone'] or "-",
                        'balance': f"{net_debt:.2f} ₪",
                        'total_purchases': f"{row['total_purchases']:.2f} ₪",
                        'total_payments': f"{row['total_payments']:.2f} ₪"
                    })
                    total_debt += net_debt
                    debt_count += 1
            
            self.customer_debt_list.data = data
            self.total_customer_debt = f"₪ {total_debt:.2f}"
            self.debt_customers_count = str(debt_count)
            
            conn.close()
            Logger.info(f"OPS Debt Report: Loaded {len(data)} customers with debt")
            
        except Exception as e:
            Logger.error(f"OPS Debt Report: Error loading customer debt - {e}")
            self.show_popup("خطأ", f"حدث خطأ: {str(e)}")
        finally:
            self.loading = False
    
    def load_supplier_debt(self):
        """تحميل ديون الموردين"""
        try:
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            query = """
                SELECT 
                    s.id,
                    s.name,
                    s.phone,
                    s.balance,
                    COALESCE((SELECT SUM(total) FROM purchases WHERE supplier_id = s.id), 0) as total_purchases,
                    COALESCE((SELECT SUM(amount) FROM supplier_payments WHERE supplier_id = s.id), 0) as total_payments
                FROM suppliers s
                WHERE s.balance > 0
                ORDER BY s.balance DESC
            """
            try:
                c.execute(query)
                suppliers = c.fetchall()
            except sqlite3.OperationalError:
                # إذا لم يكن جدول supplier_payments موجوداً
                query = """
                    SELECT 
                        s.id,
                        s.name,
                        s.phone,
                        s.balance,
                        COALESCE((SELECT SUM(total) FROM purchases WHERE supplier_id = s.id), 0) as total_purchases,
                        0 as total_payments
                    FROM suppliers s
                    WHERE s.balance > 0
                    ORDER BY s.balance DESC
                """
                c.execute(query)
                suppliers = c.fetchall()
            
            data = []
            total_debt = 0
            debt_count = 0
            
            for row in suppliers:
                net_debt = row['balance'] + row['total_purchases'] - row['total_payments']
                if net_debt > 0:
                    data.append({
                        'debt_id': row['id'],
                        'name': row['name'],
                        'phone': row['phone'] or "-",
                        'balance': f"{net_debt:.2f} ₪",
                        'total_purchases': f"{row['total_purchases']:.2f} ₪",
                        'total_payments': f"{row['total_payments']:.2f} ₪"
                    })
                    total_debt += net_debt
                    debt_count += 1
            
            self.supplier_debt_list.data = data
            self.total_supplier_debt = f"₪ {total_debt:.2f}"
            self.debt_suppliers_count = str(debt_count)
            
            conn.close()
            Logger.info(f"OPS Debt Report: Loaded {len(data)} suppliers with debt")
            
        except Exception as e:
            Logger.error(f"OPS Debt Report: Error loading supplier debt - {e}")
    
    def go_back(self):
        """العودة لشاشة التقارير الرئيسية"""
        self.manager.current = 'reports'
    
    def show_popup(self, title, message):
        """عرض نافذة منبثقة"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=message, font_name='ArabicFont', halign='center', text_size=(400, None)))
        
        btn = Button(text="موافق", size_hint_y=0.3, font_name='ArabicFont')
        popup = Popup(title=title, content=content, size_hint=(0.8, 0.5))
        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        
        popup.open()