"""
OPS PDF Generator
إنشاء ملفات PDF على Android باستخدام FPDF
"""

import os
from datetime import datetime
from fpdf import FPDF
from kivy.logger import Logger
from kivy.utils import platform
import sqlite3

# استيراد قاعدة البيانات
from database import get_db_connection

# تحديد مسار الخط العربي
if platform == 'android':
    from android.storage import primary_external_storage_path
    BASE_PATH = primary_external_storage_path()
else:
    BASE_PATH = os.path.expanduser("~")

FONT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'fonts', 'arial.ttf')


class ArabicPDF(FPDF):
    """كلاس مخصص لدعم اللغة العربية"""
    
    def __init__(self, orientation='P', unit='mm', format='A5'):
        super().__init__(orientation=orientation, unit=unit, format=format)
        self.add_font('Arabic', '', FONT_PATH, uni=True)
        self.set_auto_page_break(auto=True, margin=15)
    
    def header(self):
        """رأس الصفحة"""
        if self.page_no() == 1:
            self.set_font('Arabic', size=16)
            self.set_text_color(50, 50, 50)
            self.cell(0, 10, 'OPS - Orders Processing System', ln=True, align='C')
            self.ln(5)
    
    def footer(self):
        """تذييل الصفحة"""
        self.set_y(-15)
        self.set_font('Arabic', size=8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, f'صفحة {self.page_no()}', align='C')
        self.cell(0, 10, 'شكراً لتعاملكم معنا', align='C')


def create_customer_invoice(customer_name, invoice_data, items_data, is_return=False):
    """
    إنشاء فاتورة زبون PDF
    
    customer_name: اسم الزبون
    invoice_data: [invoice_id, date, payment_method, total]
    items_data: [(name, qty, price, total), ...]
    is_return: هل هي فاتورة مرتجع
    """
    try:
        # تحديد مجلد الحفظ
        if platform == 'android':
            pdf_dir = os.path.join(BASE_PATH, 'Documents', 'OPS_Invoices')
        else:
            pdf_dir = os.path.join(BASE_PATH, 'printouts', 'invoices')
        
        os.makedirs(pdf_dir, exist_ok=True)
        
        filename = f"Invoice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(pdf_dir, filename)
        
        # إنشاء PDF
        pdf = ArabicPDF()
        pdf.add_page()
        
        # عنوان الفاتورة
        pdf.set_font('Arabic', size=20)
        pdf.set_text_color(0, 0, 0)
        title = "فاتورة مرتجع" if is_return else "فاتورة زبون"
        pdf.cell(0, 15, title, ln=True, align='C')
        
        # خط فاصل
        pdf.ln(5)
        pdf.set_draw_color(150, 150, 150)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(8)
        
        # معلومات الزبون والفاتورة
        pdf.set_font('Arabic', size=11)
        
        # العمود الأيمن
        pdf.cell(0, 8, f"الزبون: {customer_name}", ln=True, align='R')
        pdf.cell(0, 8, f"التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='R')
        pdf.ln(5)
        
        if invoice_data:
            pdf.cell(0, 8, f"رقم الفاتورة: {invoice_data[0]}", ln=True, align='R')
            pdf.cell(0, 8, f"طريقة الدفع: {invoice_data[2]}", ln=True, align='R')
            pdf.cell(0, 8, f"الإجمالي: {invoice_data[3]:.2f} ₪", ln=True, align='R')
        
        pdf.ln(5)
        pdf.set_draw_color(150, 150, 150)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(8)
        
        # جدول الأصناف
        pdf.set_font('Arabic', size=9)
        
        # رؤوس الجدول - الترتيب من اليمين: الصنف، الكمية، السعر، الإجمالي
        col_widths = [80, 25, 30, 35]  # الصنف, الكمية, السعر, الإجمالي
        headers = ['اسم الصنف', 'الكمية', 'السعر', 'الإجمالي']
        
        # خلفية الرأس
        pdf.set_fill_color(230, 230, 230)
        
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 10, header, border=1, align='C', fill=True)
        pdf.ln()
        
        # بيانات الجدول
        for item in items_data:
            # تحديد لون النص للأحمر إذا كان مرتجع
            if is_return:
                pdf.set_text_color(200, 0, 0)
            
            pdf.cell(col_widths[0], 8, item[0], border=1, align='R')
            pdf.cell(col_widths[1], 8, str(item[1]), border=1, align='C')
            pdf.cell(col_widths[2], 8, f"{item[2]:.2f}", border=1, align='C')
            pdf.cell(col_widths[3], 8, f"{item[3]:.2f}", border=1, align='C')
            pdf.ln()
        
        # إعادة تعيين لون النص
        pdf.set_text_color(0, 0, 0)
        
        pdf.ln(10)
        
        # إجمالي الفاتورة
        pdf.set_font('Arabic', size=12, style='B')
        total_amount = sum(item[3] for item in items_data)
        pdf.cell(0, 10, f"الإجمالي النهائي: {total_amount:.2f} ₪", ln=True, align='L')
        
        pdf.ln(10)
        pdf.set_font('Arabic', size=10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 8, "شكراً لتعاملكم معنا", ln=True, align='C')
        
        # حفظ الملف
        pdf.output(filepath)
        Logger.info(f"OPS PDF: Invoice created at {filepath}")
        
        # فتح الملف على Android
        if platform == 'android':
            from android import mActivity
            from android.content import Intent
            from android.net import Uri
            from jnius import autoclass
            
            File = autoclass('java.io.File')
            Intent = autoclass('android.content.Intent')
            Uri = autoclass('android.net.Uri')
            
            file = File(filepath)
            uri = Uri.fromFile(file)
            intent = Intent(Intent.ACTION_VIEW)
            intent.setDataAndType(uri, 'application/pdf')
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            mActivity.startActivity(intent)
        else:
            # على Windows، فتح الملف مباشرة
            os.startfile(filepath)
        
        return filepath
        
    except Exception as e:
        Logger.error(f"OPS PDF: Error creating invoice - {e}")
        return None


def create_customer_account_statement(customer_name, customer_id, transactions):
    """
    إنشاء كشف حساب الزبون PDF
    
    customer_name: اسم الزبون
    customer_id: معرف الزبون
    transactions: قائمة الحركات [{'date', 'type', 'amount', 'details'}, ...]
    """
    try:
        if platform == 'android':
            pdf_dir = os.path.join(BASE_PATH, 'Documents', 'OPS_Reports')
        else:
            pdf_dir = os.path.join(BASE_PATH, 'printouts', 'reports')
        
        os.makedirs(pdf_dir, exist_ok=True)
        
        filename = f"Account_{customer_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(pdf_dir, filename)
        
        pdf = ArabicPDF(orientation='L')  # أفقي لعرض أكثر
        pdf.add_page()
        
        # عنوان التقرير
        pdf.set_font('Arabic', size=18)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 15, f"كشف حساب الزبون: {customer_name}", ln=True, align='C')
        
        pdf.ln(5)
        pdf.set_font('Arabic', size=10)
        pdf.cell(0, 8, f"تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='R')
        
        pdf.ln(5)
        pdf.set_draw_color(150, 150, 150)
        pdf.line(10, pdf.get_y(), 280, pdf.get_y())
        pdf.ln(8)
        
        # جدول الحركات
        pdf.set_font('Arabic', size=9)
        
        # رؤوس الجدول
        col_widths = [50, 40, 50, 120]  # التاريخ, نوع الحركة, المبلغ, التفاصيل
        headers = ['التاريخ', 'نوع الحركة', 'المبلغ', 'التفاصيل']
        
        # خلفية الرأس
        pdf.set_fill_color(230, 230, 230)
        
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 10, header, border=1, align='C', fill=True)
        pdf.ln()
        
        # بيانات الجدول
        total_debit = 0
        total_credit = 0
        
        for trans in transactions:
            # تحديد لون النص حسب نوع الحركة
            if trans['type'] == 'فاتورة مبيعات':
                pdf.set_text_color(0, 100, 0)
                total_debit += float(trans['amount'].replace(' ₪', ''))
            elif trans['type'] == 'مرتجع':
                pdf.set_text_color(200, 100, 0)
                total_credit += float(trans['amount'].replace(' ₪', '').replace('- ', ''))
            elif trans['type'] == 'دفعة':
                pdf.set_text_color(200, 0, 0)
                total_credit += float(trans['amount'].replace(' ₪', '').replace('- ', ''))
            
            pdf.cell(col_widths[0], 8, trans['date'], border=1, align='C')
            pdf.cell(col_widths[1], 8, trans['type'], border=1, align='C')
            pdf.cell(col_widths[2], 8, trans['amount'], border=1, align='C')
            pdf.cell(col_widths[3], 8, trans['details'], border=1, align='R')
            pdf.ln()
        
        # إعادة تعيين لون النص
        pdf.set_text_color(0, 0, 0)
        
        pdf.ln(10)
        
        # المجاميع
        pdf.set_font('Arabic', size=11, style='B')
        net_balance = total_debit - total_credit
        pdf.cell(0, 8, f"إجمالي المشتريات: {total_debit:.2f} ₪", ln=True, align='R')
        pdf.cell(0, 8, f"إجمالي المدفوعات: {total_credit:.2f} ₪", ln=True, align='R')
        pdf.cell(0, 8, f"الرصيد الحالي: {net_balance:.2f} ₪", ln=True, align='R')
        
        pdf.ln(10)
        pdf.set_font('Arabic', size=10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 8, "شكراً لتعاملكم معنا", ln=True, align='C')
        
        pdf.output(filepath)
        Logger.info(f"OPS PDF: Account statement created at {filepath}")
        
        # فتح الملف
        if platform == 'android':
            from android import mActivity
            from android.content import Intent
            from android.net import Uri
            from jnius import autoclass
            
            File = autoclass('java.io.File')
            Intent = autoclass('android.content.Intent')
            Uri = autoclass('android.net.Uri')
            
            file = File(filepath)
            uri = Uri.fromFile(file)
            intent = Intent(Intent.ACTION_VIEW)
            intent.setDataAndType(uri, 'application/pdf')
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            mActivity.startActivity(intent)
        else:
            os.startfile(filepath)
        
        return filepath
        
    except Exception as e:
        Logger.error(f"OPS PDF: Error creating account statement - {e}")
        return None


def create_products_report(products_data, title="قائمة المنتجات"):
    """
    إنشاء تقرير المنتجات PDF
    
    products_data: قائمة المنتجات [{'barcode', 'name', 'unit', 'quantity', 'buy_price', 'sell_price'}, ...]
    title: عنوان التقرير
    """
    try:
        if platform == 'android':
            pdf_dir = os.path.join(BASE_PATH, 'Documents', 'OPS_Reports')
        else:
            pdf_dir = os.path.join(BASE_PATH, 'printouts', 'reports')
        
        os.makedirs(pdf_dir, exist_ok=True)
        
        filename = f"Products_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(pdf_dir, filename)
        
        pdf = ArabicPDF(orientation='L')
        pdf.add_page()
        
        # عنوان التقرير
        pdf.set_font('Arabic', size=18)
        pdf.cell(0, 15, title, ln=True, align='C')
        
        pdf.set_font('Arabic', size=10)
        pdf.cell(0, 8, f"تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='R')
        
        pdf.ln(5)
        pdf.line(10, pdf.get_y(), 280, pdf.get_y())
        pdf.ln(8)
        
        # رؤوس الجدول
        pdf.set_font('Arabic', size=9)
        col_widths = [40, 80, 35, 40, 40, 40]  # باركود, اسم المنتج, وحدة, كمية, سعر الشراء, سعر البيع
        headers = ['الباركود', 'اسم المنتج', 'الوحدة', 'الكمية', 'سعر الشراء', 'سعر البيع']
        
        pdf.set_fill_color(230, 230, 230)
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 10, header, border=1, align='C', fill=True)
        pdf.ln()
        
        # بيانات الجدول
        for prod in products_data:
            pdf.cell(col_widths[0], 8, prod['barcode'], border=1, align='C')
            pdf.cell(col_widths[1], 8, prod['name'], border=1, align='R')
            pdf.cell(col_widths[2], 8, prod['unit'], border=1, align='C')
            
            # تلوين الكمية المنخفضة
            if int(prod['quantity']) <= 10:
                pdf.set_fill_color(255, 230, 200)
                pdf.cell(col_widths[3], 8, str(prod['quantity']), border=1, align='C', fill=True)
                pdf.set_fill_color(255, 255, 255)
            else:
                pdf.cell(col_widths[3], 8, str(prod['quantity']), border=1, align='C')
            
            pdf.cell(col_widths[4], 8, f"{prod['buy_price']:.2f}", border=1, align='C')
            pdf.cell(col_widths[5], 8, f"{prod['sell_price']:.2f}", border=1, align='C')
            pdf.ln()
        
        pdf.output(filepath)
        Logger.info(f"OPS PDF: Products report created at {filepath}")
        
        return filepath
        
    except Exception as e:
        Logger.error(f"OPS PDF: Error creating products report - {e}")
        return None


def create_invoice_pdf(invoice_id, order_id, settings):
    """إنشاء فاتورة الطلبية PDF"""
    try:
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # جلب معلومات الطلب
        c.execute("""
            SELECT o.*, c.name as customer_name 
            FROM orders o
            LEFT JOIN customers c ON o.customer_id = c.id
            WHERE o.id = ?
        """, (order_id,))
        order = c.fetchone()
        
        # جلب الأصناف
        c.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,))
        items = c.fetchall()
        
        # جلب معلومات الشيك
        check_info = None
        if order and order['payment_method'] == 'شيكات':
            c.execute("SELECT * FROM checks WHERE order_id = ?", (order_id,))
            check_info = c.fetchone()
        
        conn.close()
        
        if not order:
            Logger.error(f"OPS PDF: Order {order_id} not found")
            return None
        
        if platform == 'android':
            pdf_dir = os.path.join(BASE_PATH, 'Documents', 'OPS_Invoices')
        else:
            pdf_dir = os.path.join(BASE_PATH, 'printouts', 'invoices')
        
        os.makedirs(pdf_dir, exist_ok=True)
        
        filename = f"Invoice_{invoice_id}.pdf"
        filepath = os.path.join(pdf_dir, filename)
        
        pdf = ArabicPDF()
        pdf.add_page()
        
        # عنوان الفاتورة
        pdf.set_font('Arabic', size=16)
        pdf.cell(0, 10, settings.get('store_name', 'OPS'), ln=True, align='C')
        pdf.set_font('Arabic', size=12)
        pdf.cell(0, 8, "فاتورة طلبية", ln=True, align='C')
        
        pdf.ln(5)
        pdf.set_font('Arabic', size=10)
        pdf.cell(0, 6, f"رقم الفاتورة: {invoice_id}", ln=True, align='R')
        pdf.cell(0, 6, f"التاريخ: {order['order_date']}", ln=True, align='R')
        customer_name = order['customer_name'] if order['customer_name'] else 'زبون نقدي'
        pdf.cell(0, 6, f"الزبون: {customer_name}", ln=True, align='R')
        pdf.cell(0, 6, f"طريقة الدفع: {order['payment_method']}", ln=True, align='R')
        
        if check_info:
            pdf.cell(0, 6, f"اسم صاحب الشيك: {check_info['owner_name']}", ln=True, align='R')
            pdf.cell(0, 6, f"البنك: {check_info['bank_name']}", ln=True, align='R')
            pdf.cell(0, 6, f"رقم الشيك: {check_info['check_number']}", ln=True, align='R')
            pdf.cell(0, 6, f"تاريخ الاستحقاق: {check_info['due_date']}", ln=True, align='R')
        
        if settings.get('store_phone'):
            pdf.cell(0, 6, f"هاتف: {settings['store_phone']}", ln=True, align='R')
        
        if settings.get('store_address'):
            pdf.cell(0, 6, f"العنوان: {settings['store_address']}", ln=True, align='R')
        
        pdf.ln(5)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(8)
        
        # رؤوس الجدول - الترتيب من اليمين: الصنف، الكمية، السعر، الإجمالي
        pdf.set_font('Arabic', size=9)
        col_widths = [100, 25, 30, 35]
        pdf.cell(col_widths[0], 8, 'اسم الصنف', border=1, align='C')
        pdf.cell(col_widths[1], 8, 'الكمية', border=1, align='C')
        pdf.cell(col_widths[2], 8, 'السعر', border=1, align='C')
        pdf.cell(col_widths[3], 8, 'الإجمالي', border=1, align='C')
        pdf.ln()
        
        # بيانات الجدول
        for item in items:
            pdf.cell(col_widths[0], 7, item['name'], border=1, align='R')
            pdf.cell(col_widths[1], 7, str(item['quantity']), border=1, align='C')
            pdf.cell(col_widths[2], 7, f"{item['price']:.2f}", border=1, align='C')
            pdf.cell(col_widths[3], 7, f"{item['subtotal']:.2f}", border=1, align='C')
            pdf.ln()
        
        pdf.ln(5)
        pdf.set_font('Arabic', size=10)
        pdf.cell(0, 8, f"الإجمالي: {order['total']:.2f} {settings.get('currency', '₪')}", ln=True, align='L')
        
        if order['discount'] > 0:
            pdf.cell(0, 8, f"الخصم: {order['discount']:.2f}", ln=True, align='L')
        
        pdf.set_font('Arabic', size=12, style='B')
        pdf.cell(0, 10, f"الصافي: {order['net_total']:.2f} {settings.get('currency', '₪')}", ln=True, align='L')
        
        pdf.ln(10)
        pdf.set_font('Arabic', size=8)
        pdf.cell(0, 8, settings.get('receipt_footer', 'شكراً لتعاملكم معنا'), ln=True, align='C')
        
        pdf.output(filepath)
        
        # فتح الملف
        if platform == 'android':
            from android import mActivity
            from android.content import Intent
            from android.net import Uri
            from jnius import autoclass
            
            File = autoclass('java.io.File')
            Intent = autoclass('android.content.Intent')
            Uri = autoclass('android.net.Uri')
            
            file = File(filepath)
            uri = Uri.fromFile(file)
            intent = Intent(Intent.ACTION_VIEW)
            intent.setDataAndType(uri, 'application/pdf')
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            mActivity.startActivity(intent)
        else:
            os.startfile(filepath)
        
        return filepath
        
    except Exception as e:
        Logger.error(f"OPS PDF: Error creating invoice - {e}")
        return None


def create_sales_report(sales_data, start_date, end_date, total_sales, net_sales):
    """
    إنشاء تقرير المبيعات PDF
    """
    try:
        if platform == 'android':
            pdf_dir = os.path.join(BASE_PATH, 'Documents', 'OPS_Reports')
        else:
            pdf_dir = os.path.join(BASE_PATH, 'printouts', 'reports')
        
        os.makedirs(pdf_dir, exist_ok=True)
        
        filename = f"Sales_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(pdf_dir, filename)
        
        pdf = ArabicPDF(orientation='L')
        pdf.add_page()
        
        # عنوان التقرير
        pdf.set_font('Arabic', size=18)
        pdf.cell(0, 15, "تقرير المبيعات", ln=True, align='C')
        
        pdf.set_font('Arabic', size=10)
        pdf.cell(0, 8, f"الفترة: من {start_date} إلى {end_date}", ln=True, align='R')
        pdf.cell(0, 8, f"تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='R')
        
        pdf.ln(5)
        pdf.line(10, pdf.get_y(), 280, pdf.get_y())
        pdf.ln(8)
        
        # الإحصائيات
        pdf.set_font('Arabic', size=11, style='B')
        pdf.cell(0, 8, f"إجمالي المبيعات: {total_sales:.2f} ₪", ln=True, align='R')
        pdf.cell(0, 8, f"صافي المبيعات: {net_sales:.2f} ₪", ln=True, align='R')
        
        pdf.ln(8)
        pdf.line(10, pdf.get_y(), 280, pdf.get_y())
        pdf.ln(8)
        
        # رؤوس الجدول
        pdf.set_font('Arabic', size=9)
        col_widths = [40, 60, 40, 40, 50, 50]  # باركود, اسم المنتج, كمية, سعر, إجمالي, التاريخ
        headers = ['الباركود', 'اسم المنتج', 'الكمية', 'السعر', 'الإجمالي', 'التاريخ']
        
        pdf.set_fill_color(230, 230, 230)
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 10, header, border=1, align='C', fill=True)
        pdf.ln()
        
        # بيانات الجدول
        for sale in sales_data:
            pdf.cell(col_widths[0], 8, sale['barcode'], border=1, align='C')
            pdf.cell(col_widths[1], 8, sale['name'], border=1, align='R')
            pdf.cell(col_widths[2], 8, str(sale['quantity']), border=1, align='C')
            pdf.cell(col_widths[3], 8, f"{sale['price']:.2f}", border=1, align='C')
            pdf.cell(col_widths[4], 8, f"{sale['total']:.2f}", border=1, align='C')
            pdf.cell(col_widths[5], 8, sale['date'], border=1, align='C')
            pdf.ln()
        
        pdf.output(filepath)
        Logger.info(f"OPS PDF: Sales report created at {filepath}")
        
        return filepath
        
    except Exception as e:
        Logger.error(f"OPS PDF: Error creating sales report - {e}")
        return None


def create_return_receipt(customer_name, items, total_amount, reason):
    """إنشاء وصل مرتجع PDF"""
    try:
        if platform == 'android':
            pdf_dir = os.path.join(BASE_PATH, 'Documents', 'OPS_Returns')
        else:
            pdf_dir = os.path.join(BASE_PATH, 'printouts', 'returns')
        
        os.makedirs(pdf_dir, exist_ok=True)
        
        filename = f"Return_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(pdf_dir, filename)
        
        pdf = ArabicPDF(format='A6')
        pdf.add_page()
        
        # عنوان الوصل
        pdf.set_font('Arabic', size=14)
        pdf.cell(0, 10, 'وصل مرتجع - OPS', ln=True, align='C')
        
        pdf.ln(5)
        pdf.set_font('Arabic', size=10)
        pdf.cell(0, 8, f"التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='R')
        pdf.cell(0, 8, f"الزبون: {customer_name}", ln=True, align='R')
        
        pdf.ln(5)
        pdf.line(10, pdf.get_y(), 150, pdf.get_y())
        pdf.ln(8)
        
        # رؤوس الجدول
        pdf.set_font('Arabic', size=9)
        col_widths = [80, 25, 30]
        pdf.cell(col_widths[0], 8, 'اسم الصنف', border=1, align='C')
        pdf.cell(col_widths[1], 8, 'الكمية', border=1, align='C')
        pdf.cell(col_widths[2], 8, 'السعر', border=1, align='C')
        pdf.ln()
        
        # بيانات الجدول
        for item in items:
            pdf.cell(col_widths[0], 7, item['name'], border=1, align='R')
            pdf.cell(col_widths[1], 7, str(item['return_qty']), border=1, align='C')
            pdf.cell(col_widths[2], 7, f"{item['price']:.2f}", border=1, align='C')
            pdf.ln()
        
        pdf.ln(5)
        pdf.set_font('Arabic', size=10, style='B')
        pdf.cell(0, 8, f"الإجمالي المسترد: {total_amount} ₪", ln=True, align='L')
        
        if reason:
            pdf.set_font('Arabic', size=8)
            pdf.cell(0, 8, f"السبب: {reason}", ln=True, align='R')
        
        pdf.ln(5)
        pdf.set_font('Arabic', size=8)
        pdf.cell(0, 8, "شكراً لتعاملكم معنا", ln=True, align='C')
        
        pdf.output(filepath)
        
        # فتح الملف
        if platform == 'android':
            from android import mActivity
            from android.content import Intent
            from android.net import Uri
            from jnius import autoclass
            
            File = autoclass('java.io.File')
            Intent = autoclass('android.content.Intent')
            Uri = autoclass('android.net.Uri')
            
            file = File(filepath)
            uri = Uri.fromFile(file)
            intent = Intent(Intent.ACTION_VIEW)
            intent.setDataAndType(uri, 'application/pdf')
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            mActivity.startActivity(intent)
        else:
            os.startfile(filepath)
        
        return filepath
        
    except Exception as e:
        Logger.error(f"OPS PDF: Error creating return receipt - {e}")
        return None


def create_purchase_invoice_pdf(supplier_name, purchase, items_data):
    """إنشاء فاتورة مشتريات PDF"""
    try:
        if platform == 'android':
            pdf_dir = os.path.join(BASE_PATH, 'Documents', 'OPS_Purchases')
        else:
            pdf_dir = os.path.join(BASE_PATH, 'printouts', 'purchases')
        
        os.makedirs(pdf_dir, exist_ok=True)
        
        filename = f"Purchase_Invoice_{purchase['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(pdf_dir, filename)
        
        pdf = ArabicPDF()
        pdf.add_page()
        
        # عنوان الفاتورة
        pdf.set_font('Arabic', size=16)
        pdf.cell(0, 10, 'فاتورة مشتريات', ln=True, align='C')
        
        pdf.ln(5)
        pdf.set_font('Arabic', size=10)
        pdf.cell(0, 6, f"رقم الفاتورة: {purchase['id']}", ln=True, align='R')
        pdf.cell(0, 6, f"التاريخ: {purchase['date']}", ln=True, align='R')
        pdf.cell(0, 6, f"المورد: {supplier_name}", ln=True, align='R')
        
        pdf.ln(5)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(8)
        
        # رؤوس الجدول - الترتيب من اليمين: الصنف، الكمية، السعر، الإجمالي
        pdf.set_font('Arabic', size=9)
        col_widths = [100, 25, 30, 35]
        pdf.cell(col_widths[0], 8, 'اسم الصنف', border=1, align='C')
        pdf.cell(col_widths[1], 8, 'الكمية', border=1, align='C')
        pdf.cell(col_widths[2], 8, 'سعر الشراء', border=1, align='C')
        pdf.cell(col_widths[3], 8, 'الإجمالي', border=1, align='C')
        pdf.ln()
        
        # بيانات الجدول
        for item in items_data:
            pdf.cell(col_widths[0], 7, item['name'], border=1, align='R')
            pdf.cell(col_widths[1], 7, str(item['quantity']), border=1, align='C')
            pdf.cell(col_widths[2], 7, f"{item['price']:.2f}", border=1, align='C')
            pdf.cell(col_widths[3], 7, f"{item['subtotal']:.2f}", border=1, align='C')
            pdf.ln()
        
        pdf.ln(5)
        pdf.set_font('Arabic', size=10)
        total_amount = sum(item['subtotal'] for item in items_data)
        pdf.cell(0, 8, f"الإجمالي النهائي: {total_amount:.2f} ₪", ln=True, align='L')
        
        # حساب الخصم إن وجد
        if abs(total_amount - purchase['total']) > 0.01:
            discount = total_amount - purchase['total']
            pdf.cell(0, 8, f"الخصم: {discount:.2f} ₪", ln=True, align='L')
            pdf.cell(0, 8, f"الصافي المدفوع: {purchase['total']:.2f} ₪", ln=True, align='L')
        
        pdf.ln(10)
        pdf.set_font('Arabic', size=8)
        pdf.cell(0, 8, "شكراً لتعاملكم معنا", ln=True, align='C')
        
        pdf.output(filepath)
        
        # فتح الملف
        if platform == 'android':
            from android import mActivity
            from android.content import Intent
            from android.net import Uri
            from jnius import autoclass
            
            File = autoclass('java.io.File')
            Intent = autoclass('android.content.Intent')
            Uri = autoclass('android.net.Uri')
            
            file = File(filepath)
            uri = Uri.fromFile(file)
            intent = Intent(Intent.ACTION_VIEW)
            intent.setDataAndType(uri, 'application/pdf')
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            mActivity.startActivity(intent)
        else:
            os.startfile(filepath)
        
        return filepath
        
    except Exception as e:
        Logger.error(f"OPS PDF: Error creating purchase invoice - {e}")
        return None


def create_top_products_report(products_data, start_date, end_date, total_sales):
    """إنشاء تقرير الأصناف الأكثر مبيعاً PDF"""
    try:
        if platform == 'android':
            pdf_dir = os.path.join(BASE_PATH, 'Documents', 'OPS_Reports')
        else:
            pdf_dir = os.path.join(BASE_PATH, 'printouts', 'reports')
        
        os.makedirs(pdf_dir, exist_ok=True)
        
        filename = f"TopProducts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(pdf_dir, filename)
        
        pdf = ArabicPDF(orientation='L')
        pdf.add_page()
        
        # عنوان التقرير
        pdf.set_font('Arabic', size=18)
        pdf.cell(0, 15, "تقرير الأصناف الأكثر مبيعاً", ln=True, align='C')
        
        pdf.set_font('Arabic', size=10)
        pdf.cell(0, 8, f"الفترة: من {start_date} إلى {end_date}", ln=True, align='R')
        pdf.cell(0, 8, f"تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='R')
        
        pdf.ln(5)
        pdf.line(10, pdf.get_y(), 280, pdf.get_y())
        pdf.ln(8)
        
        # الإحصائيات
        pdf.set_font('Arabic', size=11, style='B')
        pdf.cell(0, 8, f"إجمالي المبيعات: {total_sales:.2f} ₪", ln=True, align='R')
        pdf.cell(0, 8, f"عدد المنتجات: {len(products_data)}", ln=True, align='R')
        
        pdf.ln(8)
        pdf.line(10, pdf.get_y(), 280, pdf.get_y())
        pdf.ln(8)
        
        # رؤوس الجدول
        pdf.set_font('Arabic', size=9)
        col_widths = [30, 60, 40, 50, 50]  # الترتيب, اسم المنتج, الكمية, إجمالي المبيعات, متوسط السعر
        headers = ['الترتيب', 'اسم المنتج', 'الكمية المباعة', 'إجمالي المبيعات', 'متوسط السعر']
        
        pdf.set_fill_color(230, 230, 230)
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 10, header, border=1, align='C', fill=True)
        pdf.ln()
        
        # بيانات الجدول
        for prod in products_data:
            pdf.cell(col_widths[0], 8, str(prod['rank']), border=1, align='C')
            pdf.cell(col_widths[1], 8, prod['name'], border=1, align='R')
            pdf.cell(col_widths[2], 8, str(prod['total_qty']), border=1, align='C')
            pdf.cell(col_widths[3], 8, f"{prod['total_sales']:.2f} ₪", border=1, align='C')
            pdf.cell(col_widths[4], 8, f"{prod['avg_price']:.2f} ₪", border=1, align='C')
            pdf.ln()
        
        pdf.output(filepath)
        Logger.info(f"OPS PDF: Top products report created at {filepath}")
        
        return filepath
        
    except Exception as e:
        Logger.error(f"OPS PDF: Error creating top products report - {e}")
        return None


def create_supplier_account_statement(supplier_name, supplier_id, transactions):
    """إنشاء كشف حساب المورد PDF"""
    try:
        if platform == 'android':
            pdf_dir = os.path.join(BASE_PATH, 'Documents', 'OPS_Reports')
        else:
            pdf_dir = os.path.join(BASE_PATH, 'printouts', 'reports')
        
        os.makedirs(pdf_dir, exist_ok=True)
        
        filename = f"Supplier_Account_{supplier_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(pdf_dir, filename)
        
        pdf = ArabicPDF(orientation='L')
        pdf.add_page()
        
        # عنوان التقرير
        pdf.set_font('Arabic', size=18)
        pdf.cell(0, 15, f"كشف حساب المورد: {supplier_name}", ln=True, align='C')
        
        pdf.ln(5)
        pdf.set_font('Arabic', size=10)
        pdf.cell(0, 8, f"تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='R')
        
        pdf.ln(5)
        pdf.line(10, pdf.get_y(), 280, pdf.get_y())
        pdf.ln(8)
        
        # رؤوس الجدول
        pdf.set_font('Arabic', size=9)
        col_widths = [80, 60, 80]  # التاريخ, نوع الحركة, المبلغ
        headers = ['التاريخ', 'نوع الحركة', 'المبلغ']
        
        pdf.set_fill_color(230, 230, 230)
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 10, header, border=1, align='C', fill=True)
        pdf.ln()
        
        # بيانات الجدول
        total_purchases = 0
        total_payments = 0
        
        for trans in transactions:
            if trans.get('is_purchase', False):
                pdf.set_text_color(0, 100, 0)
                total_purchases += trans['amount']
            else:
                pdf.set_text_color(200, 0, 0)
                total_payments += trans['amount']
            
            pdf.cell(col_widths[0], 8, trans['date'], border=1, align='C')
            pdf.cell(col_widths[1], 8, trans['type'], border=1, align='C')
            pdf.cell(col_widths[2], 8, f"{trans['amount']:.2f}", border=1, align='C')
            pdf.ln()
        
        # إعادة تعيين لون النص
        pdf.set_text_color(0, 0, 0)
        
        pdf.ln(10)
        
        # المجاميع
        pdf.set_font('Arabic', size=11, style='B')
        remaining = total_purchases - total_payments
        pdf.cell(0, 8, f"إجمالي المشتريات: {total_purchases:.2f} ₪", ln=True, align='R')
        pdf.cell(0, 8, f"إجمالي المدفوعات: {total_payments:.2f} ₪", ln=True, align='R')
        
        if remaining > 0:
            pdf.set_text_color(200, 0, 0)
            pdf.cell(0, 8, f"المبلغ المتبقي (الدين): {remaining:.2f} ₪", ln=True, align='R')
            pdf.set_text_color(0, 0, 0)
        else:
            pdf.cell(0, 8, f"المبلغ المتبقي: {remaining:.2f} ₪", ln=True, align='R')
        
        pdf.ln(10)
        pdf.set_font('Arabic', size=10)
        pdf.cell(0, 8, "شكراً لتعاملكم معنا", ln=True, align='C')
        
        pdf.output(filepath)
        
        # فتح الملف
        if platform == 'android':
            from android import mActivity
            from android.content import Intent
            from android.net import Uri
            from jnius import autoclass
            
            File = autoclass('java.io.File')
            Intent = autoclass('android.content.Intent')
            Uri = autoclass('android.net.Uri')
            
            file = File(filepath)
            uri = Uri.fromFile(file)
            intent = Intent(Intent.ACTION_VIEW)
            intent.setDataAndType(uri, 'application/pdf')
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            mActivity.startActivity(intent)
        else:
            os.startfile(filepath)
        
        return filepath
        
    except Exception as e:
        Logger.error(f"OPS PDF: Error creating supplier account statement - {e}")
        return None