import sqlite3
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.properties import StringProperty, NumericProperty
from kivy.logger import Logger

try:
    from database import get_db_connection
except ImportError:
    Logger.error("OPS: database.py not found!")

class InvoiceItem(BoxLayout):
    """
    عنصر فاتورة في القائمة.
    الخصائص يتم ربطها تلقائياً من الـ RecycleView
    """
    invoice_id = StringProperty("")
    date = StringProperty("")
    total = StringProperty("")
    payment_method = StringProperty("")
    index = NumericProperty(0) # لعمل ألوان متبادلة (Zebra Stripes)

class CustomerInvoicesScreen(Screen):
    """شاشة عرض فواتير الزبون"""
    
    customer_id = NumericProperty(0)
    customer_name = StringProperty("تحميل...")
    selected_invoice_id = StringProperty("")
    
    def on_enter(self):
        """تحديث القائمة عند الدخول للشاشة"""
        if self.customer_id > 0:
            self.load_invoices()
    
    def set_customer(self, customer_id, customer_name):
        """تعيين بيانات الزبون المستهدف"""
        self.customer_id = customer_id
        self.customer_name = customer_name

    def load_invoices(self):
        """جلب ملخص الفواتير من قاعدة البيانات"""
        try:
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            c.execute("""
                SELECT invoice_id, date, SUM(total) as total_sum, payment_method 
                FROM sales 
                WHERE customer_id = ? 
                GROUP BY invoice_id
                ORDER BY date DESC
            """, (self.customer_id,))
            
            rows = c.fetchall()
            conn.close()
            
            final_data = []
            for i, row in enumerate(rows):
                final_data.append({
                    'invoice_id': str(row['invoice_id']),
                    'date': str(row['date']),
                    'total': f"{row['total_sum']:,.2f}",
                    'payment_method': row['payment_method'] or "نقدي",
                    'index': i
                })
            
            # ربط البيانات بالـ RecycleView عبر الـ ID المعرف في KV
            self.ids.invoices_list.data = final_data
            
        except Exception as e:
            Logger.error(f"OPS: Error loading invoices - {e}")
            self.show_popup("خطأ", "فشل تحميل سجل الفواتير")

    def select_invoice(self, invoice_id):
        """يتم استدعاؤها عند الضغط على زر التفاصيل 🔍 في أي سطر"""
        self.selected_invoice_id = invoice_id
        self.load_invoice_details()

    def load_invoice_details(self):
        """جلب محتويات فاتورة محددة (الأصناف)"""
        try:
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            c.execute("""
                SELECT s.quantity, s.price, s.total, p.name 
                FROM sales s 
                JOIN products p ON s.barcode = p.barcode 
                WHERE s.invoice_id = ?
            """, (self.selected_invoice_id,))
            
            items = c.fetchall()
            conn.close()
            
            if items:
                self.show_invoice_details_popup(items)
            else:
                self.show_popup("تنبيه", "لا توجد تفاصيل لهذه الفاتورة")
                
        except Exception as e:
            Logger.error(f"OPS: Details error - {e}")

    def show_invoice_details_popup(self, items):
        """إنشاء نافذة منبثقة احترافية لعرض محتوى الفاتورة"""
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # حاوية سكرول للأصناف (في حال كانت الفاتورة طويلة)
        scroll = ScrollView(size_hint=(1, 0.8))
        items_list = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5)
        items_list.bind(minimum_height=items_list.setter('height'))

        # رأس جدول التفاصيل داخل البوب آب
        header = BoxLayout(size_hint_y=None, height=40, spacing=5)
        header.add_widget(Label(text="المجموع", font_name='ArabicFont', size_hint_x=0.2, bold=True))
        header.add_widget(Label(text="السعر", font_name='ArabicFont', size_hint_x=0.2, bold=True))
        header.add_widget(Label(text="الكمية", font_name='ArabicFont', size_hint_x=0.15, bold=True))
        header.add_widget(Label(text="الصنف", font_name='ArabicFont', size_hint_x=0.45, bold=True))
        main_layout.add_widget(header)

        total_invoice_sum = 0
        for item in items:
            total_invoice_sum += item['total']
            row = BoxLayout(size_hint_y=None, height=35, spacing=5)
            row.add_widget(Label(text=f"{item['total']:,.2f}", size_hint_x=0.2))
            row.add_widget(Label(text=f"{item['price']:,.2f}", size_hint_x=0.2))
            row.add_widget(Label(text=str(item['quantity']), size_hint_x=0.15))
            # اسم المنتج محاذى لليمين (للعربية)
            row.add_widget(Label(text=item['name'], font_name='ArabicFont', size_hint_x=0.45, halign='right'))
            items_list.add_widget(row)

        scroll.add_widget(items_list)
        main_layout.add_widget(scroll)

        # عرض الإجمالي النهائي في أسفل البوب آب
        footer = Label(text=f"إجمالي الفاتورة: {total_invoice_sum:,.2f} ₪", 
                      font_name='ArabicFont', size_hint_y=None, height=40, bold=True)
        main_layout.add_widget(footer)

        close_btn = Button(text="إغلاق", size_hint_y=None, height=45, font_name='ArabicFont')
        main_layout.add_widget(close_btn)

        popup = Popup(title=f"تفاصيل فاتورة رقم: {self.selected_invoice_id}", 
                      content=main_layout, size_hint=(0.9, 0.8))
        close_btn.bind(on_press=popup.dismiss)
        popup.open()

    def go_back(self):
        self.manager.current = 'customers'

    def show_popup(self, title, message):
        content = BoxLayout(orientation='vertical', padding=10)
        content.add_widget(Label(text=message, font_name='ArabicFont'))
        btn = Button(text="موافق", size_hint_y=0.4, font_name='ArabicFont')
        popup = Popup(title=title, content=content, size_hint=(0.7, 0.3))
        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        popup.open()