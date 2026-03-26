from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, NumericProperty, ListProperty, BooleanProperty
from kivy.logger import Logger
from kivy.clock import Clock
import sqlite3
from datetime import datetime
from database import get_db_connection

# استيراد دالة الطباعة المحسنة للأندرويد
try:
    from utils.pdf_generator import create_return_receipt
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    Logger.warning("Returns: PDF Generator not found")

class ReturnsScreen(Screen):
    customer_id = NumericProperty(0)
    customer_name = StringProperty("")
    invoice_id = StringProperty("")
    return_amount = StringProperty("0.00")
    reason = StringProperty("")
    
    customers_names = ListProperty(["اختر الزبون"])
    invoices_ids = ListProperty(["اختر الفاتورة"])
    customers_dict = {}

    def on_enter(self):
        self.load_customers()

    def load_customers(self):
        """تحميل الزبائن الذين لديهم فواتير قابلة للإرجاع"""
        try:
            conn = get_db_connection()
            query = "SELECT DISTINCT c.id, c.name FROM customers c JOIN sales s ON c.id = s.customer_id ORDER BY c.name"
            rows = conn.execute(query).fetchall()
            conn.close()
            
            self.customers_dict = {row[1]: row[0] for row in rows}
            self.customers_names = ["اختر الزبون"] + list(self.customers_dict.keys())
        except Exception as e:
            Logger.error(f"Returns Load Customers: {e}")

    def on_customer_select(self, name):
        if name == "اختر الزبون":
            self.reset_fields()
            return
        self.customer_name = name
        self.customer_id = self.customers_dict.get(name, 0)
        self.load_invoices()

    def load_invoices(self):
        """تحميل أرقام الفواتير الخاصة بالزبون المحدد"""
        try:
            conn = get_db_connection()
            query = """
                SELECT DISTINCT invoice_id FROM sales 
                WHERE customer_id = ? 
                GROUP BY invoice_id 
                HAVING SUM(quantity) > COALESCE(SUM(returned_qty), 0)
            """
            rows = conn.execute(query, (self.customer_id,)).fetchall()
            conn.close()
            self.invoices_ids = ["اختر الفاتورة"] + [row[0] for row in rows]
        except Exception as e:
            Logger.error(f"Returns Load Invoices: {e}")

    def load_invoice_items(self, inv_id):
        """تحميل محتويات الفاتورة إلى القائمة"""
        if inv_id == "اختر الفاتورة": return
        self.invoice_id = inv_id
        try:
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            query = """
                SELECT s.*, p.name as item_name 
                FROM sales s LEFT JOIN products p ON s.barcode = p.barcode 
                WHERE s.invoice_id = ?
            """
            rows = conn.execute(query, (inv_id,)).fetchall()
            conn.close()

            rv_data = []
            for idx, row in enumerate(rows):
                available = row['quantity'] - (row['returned_qty'] or 0)
                if available > 0:
                    rv_data.append({
                        'index': idx,
                        'sale_id': row['id'],
                        'barcode': row['barcode'],
                        'p_name': row['item_name'] or "صنف سريع",
                        'p_price': float(row['price']),
                        'p_available': float(available),
                        'p_return_qty': "",
                        'p_subtotal': "0.00"
                    })
            self.ids.returns_rv.data = rv_data
            self.calculate_total()
        except Exception as e:
            Logger.error(f"Returns Items: {e}")

    def update_item_qty(self, index, text_qty):
        """تحديث الحسابات عند تغيير الكمية المرتجعة"""
        if not text_qty: text_qty = "0"
        try:
            data = self.ids.returns_rv.data[index]
            val = float(text_qty)
            
            if val > data['p_available']:
                val = data['p_available']
            
            data['p_return_qty'] = str(val)
            data['p_subtotal'] = f"{val * data['p_price']:.2f}"
            self.ids.returns_rv.refresh_from_data()
            self.calculate_total()
        except: pass

    def calculate_total(self):
        total = sum(float(item['p_subtotal']) for item in self.ids.returns_rv.data)
        self.return_amount = f"{total:.2f}"

    def process_return(self):
        """العملية الكبرى: تحديث القاعدة، المخزن، الرصيد، والطباعة"""
        items_to_return = [i for i in self.ids.returns_rv.data if float(i['p_return_qty'] or 0) > 0]
        
        if not items_to_return: return

        conn = get_db_connection()
        try:
            cur = conn.cursor()
            total_ret = float(self.return_amount)

            for item in items_to_return:
                qty = float(item['p_return_qty'])
                
                # 1. تحديث كمية المرتجع في سجل البيع الأصلي
                cur.execute("UPDATE sales SET returned_qty = COALESCE(returned_qty, 0) + ? WHERE id = ?", 
                            (qty, item['sale_id']))
                
                # 2. إعادة الصنف للمخزن (إلا إذا كان صنف سريع)
                if item['barcode'] != "سريع":
                    cur.execute("UPDATE products SET quantity = quantity + ? WHERE barcode = ?", 
                                (qty, item['barcode']))
                
                # 3. تسجيل حركة في جدول المرتجعات (Returns)
                cur.execute("""INSERT INTO returns (original_sale_id, barcode, quantity, return_amount, return_date, reason, customer_id)
                               VALUES (?, ?, ?, ?, datetime('now'), ?, ?)""",
                            (item['sale_id'], item['barcode'], qty, float(item['p_subtotal']), self.reason, self.customer_id))

            # 4. خصم المبلغ من مديونية الزبون
            cur.execute("UPDATE customers SET balance = balance - ? WHERE id = ?", (total_ret, self.customer_id))
            
            conn.commit()
            
            # 5. الطباعة
            if PDF_AVAILABLE:
                # تحويل البيانات لتناسب دالة الطباعة
                print_items = [{'name': i['p_name'], 'return_qty': i['p_return_qty'], 'price': i['p_price']} for i in items_to_return]
                create_return_receipt(self.customer_name, print_items, self.return_amount, self.reason)

            self.reset_fields()
            Logger.info("Return Processed Successfully")
            
        except Exception as e:
            conn.rollback()
            Logger.error(f"Process Return Error: {e}")
        finally:
            conn.close()

    def reset_fields(self):
        self.ids.returns_rv.data = []
        self.return_amount = "0.00"
        self.reason = ""
        self.invoice_id = ""
        self.load_customers() # لتحديث القائمة