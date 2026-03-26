import os
import sqlite3
from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, ListProperty, NumericProperty, ObjectProperty
from kivy.metrics import dp
from kivy.clock import Clock

# محاولة استيراد مكتبة التقرير للطباعة
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import inch
except ImportError:
    print("ReportLab library not found. PDF printing will not work.")

def get_db_connection():
    """ دالة الاتصال بقاعدة البيانات - تأكد من وجود الملف بنفس المجلد """
    conn = sqlite3.connect('pos_database.db')
    conn.row_factory = sqlite3.Row
    return conn

class SupplierItem(Screen):
    """ كلاس يمثل سطر المورد في القائمة اليمنى """
    supplier_id = NumericProperty(0)
    name = StringProperty("")
    mobile = StringProperty("")
    balance = StringProperty("")
    balance_color = StringProperty("(1, 1, 1, 1)")

class SuppliersScreen(Screen):
    # ربط المعرفات بملف الـ KV
    suppliers_list = ObjectProperty(None)
    
    # خصائص الإحصائيات والعناوين
    total_debt = StringProperty("0.00 ₪")
    total_suppliers = StringProperty("0")
    selected_supplier_id = NumericProperty(0)
    selected_supplier_name = StringProperty("")
    
    # خصائص حقول الإدخال
    name = StringProperty("")
    mobile = StringProperty("")
    payment_amount = StringProperty("")

    def __init__(self, **kwargs):
        super(SuppliersScreen, self).__init__(**kwargs)
        self.all_suppliers = []
        # تحميل البيانات عند فتح الشاشة مباشرة
        Clock.schedule_once(lambda dt: self.load_suppliers())

    def go_back(self):
        """ العودة للشاشة السابقة """
        self.manager.current = 'dashboard'

    def load_suppliers(self):
        """ جلب قائمة الموردين وتحديث الأرصدة الإجمالية """
        try:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT id, name, mobile, balance FROM suppliers ORDER BY name ASC")
            rows = c.fetchall()
            
            data = []
            total_d = 0.0
            for row in rows:
                total_d += float(row['balance'])
                # أحمر للدين (>0) وأخضر للفائض (<=0)
                b_color = "(1, 0.3, 0.3, 1)" if row['balance'] > 0 else "(0.3, 1, 0.3, 1)"
                
                data.append({
                    'supplier_id': row['id'],
                    'name': row['name'],
                    'mobile': row['mobile'] if row['mobile'] else "-",
                    'balance': f"{row['balance']:.2f} ₪",
                    'balance_color': b_color
                })
            
            self.all_suppliers = data
            self.ids.suppliers_list.data = data
            self.total_debt = f"{total_d:.2f} ₪"
            self.total_suppliers = str(len(rows))
            conn.close()
        except Exception as e:
            print(f"Error loading suppliers: {e}")

    def select_supplier(self, supplier_id):
        """ تنفيذ عند اختيار مورد لعرض بياناته وحركاته المالية """
        self.selected_supplier_id = supplier_id
        
        # ملء حقول النص ببيانات المورد المختار للتعديل
        for s in self.all_suppliers:
            if s['supplier_id'] == supplier_id:
                self.selected_supplier_name = s['name']
                self.name = s['name']
                self.mobile = s['mobile'] if s['mobile'] != "-" else ""
                break
        
        # تحديث كشف الحساب في القسم الأيسر
        self.load_movements(supplier_id)

    def load_movements(self, supplier_id):
        """ جلب الفواتير والسدادات لبناء كشف حساب تراكمي """
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            # 1. المشتريات (تزيد مديونية المحل للمورد)
            c.execute("SELECT date, total FROM purchases WHERE supplier_id=?", (supplier_id,))
            purchases = [{'date': r[0][:10], 'label': "فاتورة شراء", 'amount': r[1]} for r in c.fetchall()]
            
            # 2. السدادات (تنقص مديونية المحل للمورد)
            c.execute("SELECT payment_date, amount FROM supplier_payments WHERE supplier_id=?", (supplier_id,))
            payments = [{'date': r[0][:10], 'label': "سداد نقدي", 'amount': -r[1]} for r in c.fetchall()]
            
            # دمج الحركات وترتيبها حسب التاريخ
            combined = sorted(purchases + payments, key=lambda x: x['date'])
            
            final_data = []
            running_bal = 0.0
            for move in combined:
                running_bal += float(move['amount'])
                final_data.append({
                    'date': move['date'],
                    'label': move['label'],
                    'amount': f"{abs(move['amount']):.2f} ₪",
                    'balance_after': f"{running_bal:.2f} ₪"
                })
            
            # عرض الأحدث في الأعلى دائماً
            self.ids.movements_list.data = final_data[::-1]
            conn.close()
        except Exception as e:
            print(f"Error loading movements: {e}")
            self.ids.movements_list.data = []

    def add_supplier(self):
        """ إضافة مورد جديد للقاعدة """
        if not self.name: return
        try:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("INSERT INTO suppliers (name, mobile, balance) VALUES (?, ?, 0)", 
                      (self.name, self.mobile))
            conn.commit()
            conn.close()
            self.clear_fields()
            self.load_suppliers()
        except Exception as e:
            print(f"Add Supplier Error: {e}")

    def edit_supplier(self):
        """ تعديل بيانات المورد المختار """
        if self.selected_supplier_id == 0: return
        try:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("UPDATE suppliers SET name=?, mobile=? WHERE id=?", 
                      (self.name, self.mobile, self.selected_supplier_id))
            conn.commit()
            conn.close()
            self.load_suppliers()
        except Exception as e:
            print(f"Edit Supplier Error: {e}")

    def add_payment(self):
        """ تسجيل سداد مالي وتحديث الرصيد فوراً """
        if self.selected_supplier_id == 0 or not self.payment_amount: return
        try:
            pay = float(self.payment_amount)
            conn = get_db_connection()
            c = conn.cursor()
            
            # تسجيل العملية
            c.execute("INSERT INTO supplier_payments (supplier_id, amount, payment_date) VALUES (?, ?, datetime('now'))", 
                      (self.selected_supplier_id, pay))
            
            # خصم المبلغ من رصيد المورد
            c.execute("UPDATE suppliers SET balance = balance - ? WHERE id = ?", (pay, self.selected_supplier_id))
            
            conn.commit()
            conn.close()
            
            self.payment_amount = ""
            self.load_suppliers()
            self.load_movements(self.selected_supplier_id)
        except Exception as e:
            print(f"Payment Error: {e}")

    def delete_supplier(self):
        """ حذف المورد فقط إذا كان رصيده 0 """
        if self.selected_supplier_id == 0: return
        try:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT balance FROM suppliers WHERE id=?", (self.selected_supplier_id,))
            res = c.fetchone()
            if res and res['balance'] != 0:
                print("Cannot delete: Supplier has outstanding balance.")
                return
                
            c.execute("DELETE FROM suppliers WHERE id=?", (self.selected_supplier_id,))
            conn.commit()
            conn.close()
            self.clear_fields()
            self.load_suppliers()
            self.ids.movements_list.data = []
        except Exception as e:
            print(f"Delete Error: {e}")

    def clear_fields(self):
        """ تفريغ الحقول لإضافة مورد جديد """
        self.selected_supplier_id = 0
        self.selected_supplier_name = ""
        self.name = ""
        self.mobile = ""
        self.payment_amount = ""

    def print_supplier_account(self):
        """ توليد ملف PDF ككشف حساب رسمي للمورد المختار """
        if self.selected_supplier_id == 0: return
        
        filename = f"Statement_{self.selected_supplier_name.replace(' ', '_')}.pdf"
        try:
            pdf = canvas.Canvas(filename, pagesize=A4)
            pdf.setFont("Helvetica-Bold", 16)
            pdf.drawCentredString(4*inch, 11*inch, f"Supplier Statement: {self.selected_supplier_name}")
            
            y = 10*inch
            pdf.setFont("Helvetica-Bold", 12)
            pdf.drawString(1*inch, y, "Date")
            pdf.drawString(2.5*inch, y, "Description")
            pdf.drawString(4.5*inch, y, "Amount")
            pdf.drawString(6*inch, y, "Balance After")
            
            y -= 0.3*inch
            pdf.setFont("Helvetica", 10)
            for move in self.ids.movements_list.data:
                pdf.drawString(1*inch, y, move['date'])
                pdf.drawString(2.5*inch, y, move['label'])
                pdf.drawString(4.5*inch, y, move['amount'])
                pdf.drawString(6*inch, y, move['balance_after'])
                y -= 0.25*inch
                if y < 1*inch:
                    pdf.showPage()
                    y = 11*inch
            
            pdf.save()
            if os.name == 'nt': os.startfile(filename) # Windows
            else: os.system(f'open "{filename}"') # Mac/Linux
        except Exception as e:
            print(f"PDF Print Error: {e}")