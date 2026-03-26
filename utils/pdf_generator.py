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
import arabic_reshaper
from bidi.algorithm import get_display
# استيراد قاعدة البيانات
from database import get_db_connection

def open_file_android(filepath):
    """دالة موحدة لفتح ملفات PDF على أندرويد بشكل آمن"""
    if platform == 'android':
        try:
            from jnius import autoclass, cast
            
            # حل مشكلة الحماية في النسخ الجديدة (Android 11+)
            StrictMode = autoclass('android.os.StrictMode')
            StrictMode.disableDeathOnFileUriExposure()
            
            File = autoclass('java.io.File')
            Intent = autoclass('android.content.Intent')
            Uri = autoclass('android.net.Uri')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            mActivity = PythonActivity.mActivity
            
            file = File(filepath)
            uri = Uri.fromFile(file)
            intent = Intent(Intent.ACTION_VIEW)
            intent.setDataAndType(uri, "application/pdf")
            
            # منح صلاحيات القراءة للتطبيقات الأخرى
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            
            currentActivity = cast('android.app.Activity', mActivity)
            currentActivity.startActivity(intent)
        except Exception as e:
            Logger.error(f"OPS PDF: Failed to open PDF on Android - {e}")
    else:
        # نظام ويندوز أو ماك
        os.startfile(filepath)
# تحديد مسار الخط العربي
if platform == 'android':
    from android.storage import primary_external_storage_path
    BASE_PATH = primary_external_storage_path()
else:
    BASE_PATH = os.path.expanduser("~")

FONT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'fonts', 'arial.ttf')


class ArabicPDF(FPDF):
    def __init__(self, orientation='P', unit='mm', format='A5'):
        super().__init__(orientation=orientation, unit=unit, format=format)
        # تأكد أن مسار الخط صحيح تماماً داخل مجلد assets
        self.add_font('Arabic', '', FONT_PATH, uni=True)
        self.set_auto_page_break(auto=True, margin=15)
    
    def write_arabic(self, text, w=0, h=10, border=0, ln=0, align='R', fill=False):
        """دالة مساعدة لمعالجة النص العربي قبل الطباعة"""
        if text:
            reshaped_text = arabic_reshaper.reshape(str(text))
            bidi_text = get_display(reshaped_text)
            self.cell(w, h, bidi_text, border=border, ln=ln, align=align, fill=fill)
                
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
    إنشاء فاتورة زبون PDF مع دعم كامل للعربية والأندرويد الحديث
    """
    try:
        # 1. تحديد مجلد الحفظ
        if platform == 'android':
            pdf_dir = os.path.join(BASE_PATH, 'Documents', 'OPS_Invoices')
        else:
            pdf_dir = os.path.join(BASE_PATH, 'printouts', 'invoices')
        
        os.makedirs(pdf_dir, exist_ok=True)
        filename = f"Invoice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(pdf_dir, filename)
        
        # 2. إنشاء PDF (تأكد من وجود كلاس ArabicPDF في ملفك)
        pdf = ArabicPDF()
        pdf.add_page()
        
        # دالة مساعدة داخلية لتنسيق النص العربي بسرعة
        def ar(text):
            from arabic_reshaper import reshape
            from bidi.algorithm import get_display
            return get_display(reshape(str(text)))

        # 3. عنوان الفاتورة
        pdf.set_font('Arabic', size=20)
        title = "فاتورة مرتجع" if is_return else "فاتورة زبون"
        pdf.cell(0, 15, ar(title), ln=True, align='C')
        
        pdf.ln(5)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(8)
        
        # 4. معلومات الزبون والفاتورة
        pdf.set_font('Arabic', size=11)
        pdf.cell(0, 8, ar(f"الزبون: {customer_name}"), ln=True, align='R')
        pdf.cell(0, 8, ar(f"التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}"), ln=True, align='R')
        
        if invoice_data:
            pdf.cell(0, 8, ar(f"رقم الفاتورة: {invoice_data[0]}"), ln=True, align='R')
            pdf.cell(0, 8, ar(f"طريقة الدفع: {invoice_data[2]}"), ln=True, align='R')
            pdf.cell(0, 8, ar(f"الإجمالي: {invoice_data[3]:.2f} ₪"), ln=True, align='R')
        
        pdf.ln(8)
        
        # 5. جدول الأصناف
        pdf.set_font('Arabic', size=9)
        col_widths = [35, 30, 25, 80]  # الترتيب: إجمالي، سعر، كمية، صنف (من اليسار لليمين للـ PDF)
        headers = ['الإجمالي', 'السعر', 'الكمية', 'اسم الصنف']
        
        pdf.set_fill_color(230, 230, 230)
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 10, ar(header), border=1, align='C', fill=True)
        pdf.ln()
        
        # بيانات الجدول
        for item in items_data:
            if is_return: pdf.set_text_color(200, 0, 0)
            
            # طباعة الخلايا (يجب عكس ترتيب البيانات ليتناسب مع اتجاه الجدول)
            pdf.cell(col_widths[0], 8, f"{item[3]:.2f}", border=1, align='C')
            pdf.cell(col_widths[1], 8, f"{item[2]:.2f}", border=1, align='C')
            pdf.cell(col_widths[2], 8, str(item[1]), border=1, align='C')
            pdf.cell(col_widths[3], 8, ar(item[0]), border=1, align='R')
            pdf.ln()
            pdf.set_text_color(0, 0, 0)
        
        # 6. الإجمالي النهائي
        pdf.ln(10)
        pdf.set_font('Arabic', size=12)
        total_amount = sum(item[3] for item in items_data)
        pdf.cell(0, 10, ar(f"الإجمالي النهائي: {total_amount:.2f} ₪"), ln=True, align='L')
        
        pdf.ln(5)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 8, ar("شكراً لتعاملكم معنا"), ln=True, align='C')
        
        # 7. الحفظ والفتح
        pdf.output(filepath)
        Logger.info(f"OPS PDF: Invoice created at {filepath}")
        
        # استدعاء الدالة الموحدة التي أنشأناها سابقاً
        open_file_android(filepath)
        
        return filepath
        
    except Exception as e:
        Logger.error(f"OPS PDF: Error creating invoice - {e}")
        return None
    
def create_customer_account_statement(customer_name, customer_id, transactions):
    """
    إنشاء كشف حساب الزبون PDF مع دعم كامل للعربية والأندرويد الحديث
    """
    try:
        # 1. تحديد مسار الحفظ
        if platform == 'android':
            pdf_dir = os.path.join(BASE_PATH, 'Documents', 'OPS_Reports')
        else:
            pdf_dir = os.path.join(BASE_PATH, 'printouts', 'reports')
        
        os.makedirs(pdf_dir, exist_ok=True)
        filename = f"Account_{customer_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(pdf_dir, filename)
        
        # 2. إعداد ملف PDF (أفقي L)
        pdf = ArabicPDF(orientation='L') 
        pdf.add_page()
        
        # دالة داخلية لتنسيق العربي
        def ar(text):
            from arabic_reshaper import reshape
            from bidi.algorithm import get_display
            return get_display(reshape(str(text)))

        # 3. عنوان التقرير
        pdf.set_font('Arabic', size=18)
        pdf.cell(0, 15, ar(f"كشف حساب الزبون: {customer_name}"), ln=True, align='C')
        
        pdf.set_font('Arabic', size=10)
        pdf.cell(0, 8, ar(f"تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d %H:%M')}"), ln=True, align='R')
        
        pdf.ln(5)
        pdf.line(10, pdf.get_y(), 280, pdf.get_y())
        pdf.ln(8)
        
        # 4. جدول الحركات
        pdf.set_font('Arabic', size=9)
        
        # ترتيب الأعمدة للعربية (من اليمين لليسار برمجياً): التفاصيل، المبلغ، النوع، التاريخ
        col_widths = [120, 50, 50, 40] 
        headers = ['التفاصيل', 'المبلغ', 'نوع الحركة', 'التاريخ']
        
        # رسم الرأس
        pdf.set_fill_color(230, 230, 230)
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 10, ar(header), border=1, align='C', fill=True)
        pdf.ln()
        
        # 5. معالجة البيانات داخل الجدول
        total_debit = 0
        total_credit = 0
        
        for trans in transactions:
            # تنظيف نص المبلغ لتحويله لرقم
            try:
                raw_amount = float(str(trans['amount']).replace(' ₪', '').replace('-', '').strip())
            except:
                raw_amount = 0.0

            # تحديد الألوان وحساب المجاميع
            if 'فاتورة' in trans['type']:
                pdf.set_text_color(0, 100, 0)
                total_debit += raw_amount
            elif 'مرتجع' in trans['type'] or 'دفعة' in trans['type']:
                pdf.set_text_color(200, 0, 0)
                total_credit += raw_amount
            
            # طباعة السطر (بالترتيب المعكوس ليظهر العربي صحيحاً)
            pdf.cell(col_widths[0], 8, ar(trans['details']), border=1, align='R')
            pdf.cell(col_widths[1], 8, ar(trans['amount']), border=1, align='C')
            pdf.cell(col_widths[2], 8, ar(trans['type']), border=1, align='C')
            pdf.cell(col_widths[3], 8, ar(trans['date']), border=1, align='C')
            pdf.ln()
            pdf.set_text_color(0, 0, 0)
        
        # 6. قسم المجاميع والنتائج
        pdf.ln(10)
        pdf.set_font('Arabic', size=11)
        net_balance = total_debit - total_credit
        
        pdf.cell(0, 8, ar(f"إجمالي المشتريات: {total_debit:.2f} ₪"), ln=True, align='R')
        pdf.cell(0, 8, ar(f"إجمالي المدفوعات: {total_credit:.2f} ₪"), ln=True, align='R')
        
        # تلوين الرصيد (أحمر إذا كان عليه ديون)
        if net_balance > 0: pdf.set_text_color(200, 0, 0)
        pdf.cell(0, 8, ar(f"الرصيد الحالي: {net_balance:.2f} ₪"), ln=True, align='R')
        pdf.set_text_color(0, 0, 0)
        
        pdf.ln(10)
        pdf.cell(0, 8, ar("شكراً لتعاملكم معنا"), ln=True, align='C')
        
        # 7. الحفظ والفتح الآمن
        pdf.output(filepath)
        Logger.info(f"OPS PDF: Account statement created at {filepath}")
        
        # استدعاء دالة الفتح الموحدة التي وضعناها في أول الملف
        open_file_android(filepath)
        
        return filepath
        
    except Exception as e:
        Logger.error(f"OPS PDF: Error creating account statement - {e}")
        return None

def create_products_report(products_data, title="قائمة المنتجات"):
    """
    إنشاء تقرير المنتجات PDF مع دعم العربية وتنبيه الكميات المنخفضة
    """
    try:
        # 1. إعداد المسار
        if platform == 'android':
            pdf_dir = os.path.join(BASE_PATH, 'Documents', 'OPS_Reports')
        else:
            pdf_dir = os.path.join(BASE_PATH, 'printouts', 'reports')
        
        os.makedirs(pdf_dir, exist_ok=True)
        filename = f"Products_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(pdf_dir, filename)
        
        # 2. إنشاء PDF (بالعرض Landscape)
        pdf = ArabicPDF(orientation='L')
        pdf.add_page()
        
        def ar(text):
            from arabic_reshaper import reshape
            from bidi.algorithm import get_display
            return get_display(reshape(str(text)))

        # 3. العنوان والتاريخ
        pdf.set_font('Arabic', size=18)
        pdf.cell(0, 15, ar(title), ln=True, align='C')
        
        pdf.set_font('Arabic', size=10)
        pdf.cell(0, 8, ar(f"تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d %H:%M')}"), ln=True, align='R')
        
        pdf.ln(5)
        pdf.line(10, pdf.get_y(), 280, pdf.get_y())
        pdf.ln(8)
        
        # 4. رؤوس الجدول (عكس الترتيب للعربية)
        # الترتيب: سعر البيع، سعر الشراء، الكمية، الوحدة، اسم المنتج، الباركود
        col_widths = [40, 40, 40, 35, 80, 40] 
        headers = ['سعر البيع', 'سعر الشراء', 'الكمية', 'الوحدة', 'اسم المنتج', 'الباركود']
        
        pdf.set_fill_color(230, 230, 230)
        pdf.set_font('Arabic', size=10, style='B')
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 10, ar(header), border=1, align='C', fill=True)
        pdf.ln()
        
        # 5. بيانات المنتجات
        pdf.set_font('Arabic', size=9)
        for prod in products_data:
            # الخلية 1: سعر البيع
            pdf.cell(col_widths[0], 8, f"{float(prod['sell_price']):.2f}", border=1, align='C')
            
            # الخلية 2: سعر الشراء
            pdf.cell(col_widths[1], 8, f"{float(prod['buy_price']):.2f}", border=1, align='C')
            
            # الخلية 3: الكمية (مع تلوين التنبيه)
            qty = int(prod['quantity'])
            if qty <= 10:
                pdf.set_fill_color(255, 200, 200) # لون أحمر خفيف للتنبيه
                pdf.cell(col_widths[2], 8, str(qty), border=1, align='C', fill=True)
                pdf.set_fill_color(255, 255, 255)
            else:
                pdf.cell(col_widths[2], 8, str(qty), border=1, align='C')
            
            # الخلية 4: الوحدة
            pdf.cell(col_widths[3], 8, ar(prod['unit']), border=1, align='C')
            
            # الخلية 5: اسم المنتج
            pdf.cell(col_widths[4], 8, ar(prod['name']), border=1, align='R')
            
            # الخلية 6: الباركود
            pdf.cell(col_widths[5], 8, str(prod['barcode']), border=1, align='C')
            
            pdf.ln()
        
        # 6. الحفظ والفتح
        pdf.output(filepath)
        Logger.info(f"OPS PDF: Products report created at {filepath}")
        
        # استدعاء دالة الفتح التلقائي
        open_file_android(filepath)
        
        return filepath
        
    except Exception as e:
        Logger.error(f"OPS PDF: Error creating products report - {e}")
        return None

def create_invoice_pdf(invoice_id, order_id, settings):
    """
    إنشاء فاتورة الطلبية PDF مع دعم الشيكات واللغة العربية
    """
    try:
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # 1. جلب البيانات من قاعدة البيانات
        c.execute("""
            SELECT o.*, c.name as customer_name 
            FROM orders o
            LEFT JOIN customers c ON o.customer_id = c.id
            WHERE o.id = ?
        """, (order_id,))
        order = c.fetchone()
        
        c.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,))
        items = c.fetchall()
        
        check_info = None
        if order and order['payment_method'] == 'شيكات':
            c.execute("SELECT * FROM checks WHERE order_id = ?", (order_id,))
            check_info = c.fetchone()
        
        conn.close()
        
        if not order:
            Logger.error(f"OPS PDF: Order {order_id} not found")
            return None

        # 2. إعداد المسار
        if platform == 'android':
            pdf_dir = os.path.join(BASE_PATH, 'Documents', 'OPS_Invoices')
        else:
            pdf_dir = os.path.join(BASE_PATH, 'printouts', 'invoices')
        
        os.makedirs(pdf_dir, exist_ok=True)
        filename = f"Invoice_{invoice_id}.pdf"
        filepath = os.path.join(pdf_dir, filename)
        
        # 3. إنشاء الـ PDF وتنسيق العربي
        pdf = ArabicPDF()
        pdf.add_page()
        
        def ar(text):
            from arabic_reshaper import reshape
            from bidi.algorithm import get_display
            return get_display(reshape(str(text)))

        # 4. رأس الفاتورة (معلومات المتجر)
        pdf.set_font('Arabic', size=16)
        pdf.cell(0, 10, ar(settings.get('store_name', 'OPS')), ln=True, align='C')
        pdf.set_font('Arabic', size=12)
        pdf.cell(0, 8, ar("فاتورة طلبية"), ln=True, align='C')
        
        pdf.ln(5)
        pdf.set_font('Arabic', size=10)
        
        # معلومات الفاتورة والزبون
        pdf.cell(0, 6, ar(f"رقم الفاتورة: {invoice_id}"), ln=True, align='R')
        pdf.cell(0, 6, ar(f"التاريخ: {order['order_date']}"), ln=True, align='R')
        
        cust_name = order['customer_name'] if order['customer_name'] else 'زبون نقدي'
        pdf.cell(0, 6, ar(f"الزبون: {cust_name}"), ln=True, align='R')
        pdf.cell(0, 6, ar(f"طريقة الدفع: {order['payment_method']}"), ln=True, align='R')
        
        # إضافة معلومات الشيك إن وجدت
        if check_info:
            pdf.set_text_color(100, 0, 0)
            pdf.cell(0, 6, ar(f"صاحب الشيك: {check_info['owner_name']} | بنك: {check_info['bank_name']}"), ln=True, align='R')
            pdf.cell(0, 6, ar(f"رقم الشيك: {check_info['check_number']} | استحقاق: {check_info['due_date']}"), ln=True, align='R')
            pdf.set_text_color(0, 0, 0)

        # هاتف وعنوان المتجر
        if settings.get('store_phone'):
            pdf.cell(0, 6, ar(f"هاتف: {settings['store_phone']}"), ln=True, align='R')
        if settings.get('store_address'):
            pdf.cell(0, 6, ar(f"العنوان: {settings['store_address']}"), ln=True, align='R')
        
        pdf.ln(5)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(8)
        
        # 5. جدول الأصناف (عكس الترتيب ليتناسب مع اتجاه العربي)
        # الترتيب: الإجمالي، السعر، الكمية، اسم الصنف
        col_widths = [35, 30, 25, 100]
        headers = ['الإجمالي', 'السعر', 'الكمية', 'اسم الصنف']
        
        pdf.set_fill_color(240, 240, 240)
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 8, ar(header), border=1, align='C', fill=True)
        pdf.ln()
        
        for item in items:
            pdf.cell(col_widths[0], 7, f"{item['subtotal']:.2f}", border=1, align='C')
            pdf.cell(col_widths[1], 7, f"{item['price']:.2f}", border=1, align='C')
            pdf.cell(col_widths[2], 7, str(item['quantity']), border=1, align='C')
            pdf.cell(col_widths[3], 7, ar(item['name']), border=1, align='R')
            pdf.ln()
        
        # 6. المخلص المالي
        pdf.ln(5)
        curr = settings.get('currency', '₪')
        pdf.set_font('Arabic', size=10)
        pdf.cell(0, 8, ar(f"الإجمالي: {order['total']:.2f} {curr}"), ln=True, align='L')
        
        if order['discount'] > 0:
            pdf.set_text_color(200, 0, 0)
            pdf.cell(0, 8, ar(f"الخصم: {order['discount']:.2f} {curr}"), ln=True, align='L')
            pdf.set_text_color(0, 0, 0)
        
        pdf.set_font('Arabic', size=12, style='B')
        pdf.cell(0, 10, ar(f"الصافي النهائي: {order['net_total']:.2f} {curr}"), ln=True, align='L')
        
        # تذييل الفاتورة
        pdf.ln(10)
        pdf.set_font('Arabic', size=9)
        pdf.cell(0, 8, ar(settings.get('receipt_footer', 'شكراً لتعاملكم معنا')), ln=True, align='C')
        
        # 7. الحفظ والفتح الآمن
        pdf.output(filepath)
        Logger.info(f"OPS PDF: Invoice created at {filepath}")
        
        open_file_android(filepath)
        
        return filepath
        
    except Exception as e:
        Logger.error(f"OPS PDF: Error creating invoice - {e}")
        return None

def create_sales_report(sales_data, start_date, end_date, total_sales, net_sales):
    """
    إنشاء تقرير المبيعات PDF مع دعم العربية والفتح التلقائي
    """
    try:
        # تحديد المسار
        if platform == 'android':
            pdf_dir = os.path.join(BASE_PATH, 'Documents', 'OPS_Reports')
        else:
            pdf_dir = os.path.join(BASE_PATH, 'printouts', 'reports')
        
        os.makedirs(pdf_dir, exist_ok=True)
        filename = f"Sales_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(pdf_dir, filename)
        
        pdf = ArabicPDF(orientation='L') # وضع أفقي
        pdf.add_page()
        
        def ar(text):
            from arabic_reshaper import reshape
            from bidi.algorithm import get_display
            return get_display(reshape(str(text)))

        # العنوان
        pdf.set_font('Arabic', size=18)
        pdf.cell(0, 15, ar("تقرير المبيعات"), ln=True, align='C')
        
        pdf.set_font('Arabic', size=10)
        pdf.cell(0, 8, ar(f"الفترة: من {start_date} إلى {end_date}"), ln=True, align='R')
        pdf.cell(0, 8, ar(f"تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d %H:%M')}"), ln=True, align='R')
        
        pdf.ln(5)
        pdf.line(10, pdf.get_y(), 280, pdf.get_y())
        pdf.ln(8)
        
        # الإحصائيات المالية
        pdf.set_font('Arabic', size=11, style='B')
        pdf.set_text_color(0, 100, 0) # أخضر للمبيعات
        pdf.cell(0, 8, ar(f"إجمالي المبيعات: {total_sales:.2f} ₪"), ln=True, align='R')
        pdf.set_text_color(0, 0, 100) # أزرق للصافي
        pdf.cell(0, 8, ar(f"صافي المبيعات (بعد الخصم): {net_sales:.2f} ₪"), ln=True, align='R')
        pdf.set_text_color(0, 0, 0)
        
        pdf.ln(5)
        
        # رؤوس الجدول (عكس الترتيب للعربية)
        # الترتيب: التاريخ، الإجمالي، السعر، الكمية، الاسم، الباركود
        col_widths = [50, 40, 40, 30, 80, 40] 
        headers = ['التاريخ والوقت', 'الإجمالي', 'سعر الوحدة', 'الكمية', 'اسم المنتج', 'الباركود']
        
        pdf.set_fill_color(230, 230, 230)
        pdf.set_font('Arabic', size=9)
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 10, ar(header), border=1, align='C', fill=True)
        pdf.ln()
        
        # بيانات الجدول
        for sale in sales_data:
            pdf.cell(col_widths[0], 8, str(sale['date']), border=1, align='C')
            pdf.cell(col_widths[1], 8, f"{float(sale['total']):.2f}", border=1, align='C')
            pdf.cell(col_widths[2], 8, f"{float(sale['price']):.2f}", border=1, align='C')
            pdf.cell(col_widths[3], 8, str(sale['quantity']), border=1, align='C')
            pdf.cell(col_widths[4], 8, ar(sale['name']), border=1, align='R')
            pdf.cell(col_widths[5], 8, str(sale['barcode']), border=1, align='C')
            pdf.ln()
        
        pdf.output(filepath)
        open_file_android(filepath) # دالة الفتح الآمنة
        return filepath
        
    except Exception as e:
        Logger.error(f"OPS PDF: Error sales report - {e}")
        return None
    
def create_purchase_invoice_pdf(supplier_name, purchase, items_data):
    """
    إنشاء فاتورة مشتريات PDF احترافية تدعم العربية
    """
    try:
        # 1. إعداد مسار الحفظ
        if platform == 'android':
            pdf_dir = os.path.join(BASE_PATH, 'Documents', 'OPS_Purchases')
        else:
            pdf_dir = os.path.join(BASE_PATH, 'printouts', 'purchases')
        
        os.makedirs(pdf_dir, exist_ok=True)
        filename = f"Purchase_{purchase['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(pdf_dir, filename)
        
        # 2. إعداد PDF وتنسيق العربي
        pdf = ArabicPDF()
        pdf.add_page()
        
        def ar(text):
            from arabic_reshaper import reshape
            from bidi.algorithm import get_display
            return get_display(reshape(str(text)))

        # 3. ترويسة الفاتورة
        pdf.set_font('Arabic', size=16)
        pdf.set_text_color(0, 51, 102) # لون أزرق غامق للمشتريات
        pdf.cell(0, 10, ar('فاتورة مشتريات من مورد'), ln=True, align='C')
        pdf.set_text_color(0, 0, 0) # عودة للون الأسود
        
        pdf.ln(5)
        pdf.set_font('Arabic', size=10)
        pdf.cell(0, 6, ar(f"رقم الفاتورة: {purchase['id']}"), ln=True, align='R')
        pdf.cell(0, 6, ar(f"التاريخ: {purchase['date']}"), ln=True, align='R')
        pdf.cell(0, 6, ar(f"المورد: {supplier_name}"), ln=True, align='R')
        
        pdf.ln(5)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(8)
        
        # 4. رؤوس الجدول (عكس الترتيب للعربية)
        # الترتيب: الإجمالي، السعر، الكمية، الصنف
        col_widths = [35, 30, 25, 100]
        headers = ['الإجمالي', 'سعر الشراء', 'الكمية', 'اسم الصنف']
        
        pdf.set_fill_color(220, 230, 241) # لون خلفية زرقاء فاتحة للرأس
        pdf.set_font('Arabic', size=9, style='B')
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 10, ar(header), border=1, align='C', fill=True)
        pdf.ln()
        
        # 5. بيانات الأصناف
        pdf.set_font('Arabic', size=9)
        total_calculated = 0
        for item in items_data:
            subtotal = float(item['price']) * float(item['quantity'])
            total_calculated += subtotal
            
            pdf.cell(col_widths[0], 8, f"{subtotal:.2f}", border=1, align='C')
            pdf.cell(col_widths[1], 8, f"{float(item['price']):.2f}", border=1, align='C')
            pdf.cell(col_widths[2], 8, str(item['quantity']), border=1, align='C')
            pdf.cell(col_widths[3], 8, ar(item['name']), border=1, align='R')
            pdf.ln()
            
        # 6. الملخص المالي
        pdf.ln(5)
        pdf.set_font('Arabic', size=10)
        pdf.cell(0, 8, ar(f"إجمالي الفاتورة: {total_calculated:.2f} ₪"), ln=True, align='L')
        
        # حساب الخصم الممنوح من المورد إن وجد
        if abs(total_calculated - float(purchase['total'])) > 0.01:
            discount = total_calculated - float(purchase['total'])
            pdf.set_text_color(0, 128, 0) # لون أخضر للخصم (توفير)
            pdf.cell(0, 8, ar(f"الخصم المكتسب: {discount:.2f} ₪"), ln=True, align='L')
            pdf.set_text_color(0, 0, 0)
            
        pdf.set_font('Arabic', size=12, style='B')
        pdf.cell(0, 10, ar(f"الصافي المطلوب للمورد: {float(purchase['total']):.2f} ₪"), ln=True, align='L')
        
        # 7. الحفظ والفتح
        pdf.output(filepath)
        Logger.info(f"OPS PDF: Purchase invoice created at {filepath}")
        
        open_file_android(filepath) # دالة الفتح الآمنة
        
        return filepath
        
    except Exception as e:
        Logger.error(f"OPS PDF: Error creating purchase invoice - {e}")
        return None

def create_top_products_report(products_data, start_date, end_date, total_sales):
    """
    إنشاء تقرير الأصناف الأكثر مبيعاً PDF مع دعم العربية والفتح التلقائي
    """
    try:
        # 1. إعداد المسار
        if platform == 'android':
            pdf_dir = os.path.join(BASE_PATH, 'Documents', 'OPS_Reports')
        else:
            pdf_dir = os.path.join(BASE_PATH, 'printouts', 'reports')
        
        os.makedirs(pdf_dir, exist_ok=True)
        filename = f"TopProducts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(pdf_dir, filename)
        
        # 2. إنشاء PDF (عرضي Landscape ليناسب البيانات الكثيرة)
        pdf = ArabicPDF(orientation='L')
        pdf.add_page()
        
        def ar(text):
            from arabic_reshaper import reshape
            from bidi.algorithm import get_display
            return get_display(reshape(str(text)))

        # 3. العنوان والإحصائيات العامة
        pdf.set_font('Arabic', size=18)
        pdf.cell(0, 15, ar("تقرير الأصناف الأكثر مبيعاً"), ln=True, align='C')
        
        pdf.set_font('Arabic', size=10)
        pdf.cell(0, 8, ar(f"الفترة: من {start_date} إلى {end_date}"), ln=True, align='R')
        pdf.cell(0, 8, ar(f"تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d %H:%M')}"), ln=True, align='R')
        
        pdf.ln(5)
        pdf.line(10, pdf.get_y(), 280, pdf.get_y())
        pdf.ln(8)
        
        # ملخص سريع في أعلى التقرير
        pdf.set_font('Arabic', size=11, style='B')
        pdf.set_text_color(0, 51, 102) # لون كحلي
        pdf.cell(0, 8, ar(f"إجمالي قيمة مبيعات الأصناف: {total_sales:.2f} ₪"), ln=True, align='R')
        pdf.cell(0, 8, ar(f"عدد الأصناف المسجلة في التقرير: {len(products_data)}"), ln=True, align='R')
        pdf.set_text_color(0, 0, 0)
        
        pdf.ln(8)
        
        # 4. رؤوس الجدول (عكس الترتيب للعربية)
        # الترتيب من اليسار لليمين برمجياً (ليظهر من اليمين لليسار في الـ PDF):
        # متوسط السعر، إجمالي المبيعات، الكمية المباعة، اسم المنتج، الترتيب
        col_widths = [50, 50, 40, 100, 30]
        headers = ['متوسط سعر البيع', 'إجمالي المبيعات', 'الكمية المباعة', 'اسم المنتج', 'الترتيب']
        
        pdf.set_fill_color(230, 230, 230)
        pdf.set_font('Arabic', size=10, style='B')
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 10, ar(header), border=1, align='C', fill=True)
        pdf.ln()
        
        # 5. بيانات الجدول
        pdf.set_font('Arabic', size=9)
        for prod in products_data:
            # متوسط السعر
            pdf.cell(col_widths[0], 8, f"{float(prod['avg_price']):.2f} ₪", border=1, align='C')
            # إجمالي المبيعات
            pdf.cell(col_widths[1], 8, f"{float(prod['total_sales']):.2f} ₪", border=1, align='C')
            # الكمية
            pdf.cell(col_widths[2], 8, str(prod['total_qty']), border=1, align='C')
            # اسم المنتج
            pdf.cell(col_widths[3], 8, ar(prod['name']), border=1, align='R')
            # الترتيب (تمييز بسيط)
            pdf.set_fill_color(245, 245, 245)
            pdf.cell(col_widths[4], 8, str(prod['rank']), border=1, align='C', fill=True)
            
            pdf.ln()
        
        # 6. الحفظ والفتح
        pdf.output(filepath)
        Logger.info(f"OPS PDF: Top products report created at {filepath}")
        
        open_file_android(filepath) # الدالة الموحدة لفتح الملف
        
        return filepath
        
    except Exception as e:
        Logger.error(f"OPS PDF: Error creating top products report - {e}")
        return None

def create_supplier_account_statement(supplier_name, supplier_id, transactions):
    """
    إنشاء كشف حساب المورد PDF مع حساب الأرصدة ودعم العربية
    """
    try:
        # 1. إعداد المسار
        if platform == 'android':
            pdf_dir = os.path.join(BASE_PATH, 'Documents', 'OPS_Reports')
        else:
            pdf_dir = os.path.join(BASE_PATH, 'printouts', 'reports')
        
        os.makedirs(pdf_dir, exist_ok=True)
        filename = f"Supplier_Acc_{supplier_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(pdf_dir, filename)
        
        pdf = ArabicPDF(orientation='L') # وضع أفقي ليناسب عرض الجداول الممالية
        pdf.add_page()
        
        def ar(text):
            from arabic_reshaper import reshape
            from bidi.algorithm import get_display
            return get_display(reshape(str(text)))

        # 2. العنوان الرئيسي
        pdf.set_font('Arabic', size=18)
        pdf.cell(0, 15, ar(f"كشف حساب المورد: {supplier_name}"), ln=True, align='C')
        
        pdf.set_font('Arabic', size=10)
        pdf.cell(0, 8, ar(f"تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d %H:%M')}"), ln=True, align='R')
        
        pdf.ln(5)
        pdf.line(10, pdf.get_y(), 280, pdf.get_y())
        pdf.ln(8)
        
        # 3. رؤوس الجدول (عكس الترتيب للعربية)
        # الترتيب: المبلغ، نوع الحركة، التاريخ
        col_widths = [80, 80, 100]
        headers = ['المبلغ (₪)', 'نوع العملية', 'التاريخ والوقت']
        
        pdf.set_fill_color(230, 230, 230)
        pdf.set_font('Arabic', size=11, style='B')
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 10, ar(header), border=1, align='C', fill=True)
        pdf.ln()
        
        # 4. بيانات الجدول ومعالجة الحسابات
        pdf.set_font('Arabic', size=10)
        total_purchases = 0
        total_payments = 0
        
        for trans in transactions:
            amount = float(trans['amount'])
            
            # تمييز الألوان: المشتريات تزيد الدين (أحمر) - الدفعات تنقص الدين (أخضر)
            if trans.get('is_purchase', False):
                pdf.set_text_color(150, 0, 0) # أحمر غامق
                total_purchases += amount
            else:
                pdf.set_text_color(0, 120, 0) # أخضر غامق
                total_payments += amount
            
            pdf.cell(col_widths[0], 8, f"{amount:.2f}", border=1, align='C')
            pdf.cell(col_widths[1], 8, ar(trans['type']), border=1, align='C')
            pdf.cell(col_widths[2], 8, str(trans['date']), border=1, align='C')
            pdf.ln()
        
        # 5. ملخص الحساب النهائي
        pdf.set_text_color(0, 0, 0)
        pdf.ln(10)
        pdf.line(180, pdf.get_y(), 280, pdf.get_y())
        pdf.ln(2)
        
        pdf.set_font('Arabic', size=12, style='B')
        remaining = total_purchases - total_payments
        
        pdf.cell(0, 8, ar(f"إجمالي قيمة المشتريات: {total_purchases:.2f} ₪"), ln=True, align='L')
        pdf.cell(0, 8, ar(f"إجمالي المبالغ المدفوعة: {total_payments:.2f} ₪"), ln=True, align='L')
        
        # تمييز الرصيد المتبقي
        if remaining > 0:
            pdf.set_text_color(200, 0, 0)
            status = f"الرصيد المتبقي للمورد (دين): {remaining:.2f} ₪"
        elif remaining < 0:
            pdf.set_text_color(0, 0, 200)
            status = f"رصيد لنا عند المورد (دفع مقدم): {abs(remaining):.2f} ₪"
        else:
            status = "الحساب خالص (صفر)"
            
        pdf.cell(0, 10, ar(status), ln=True, align='L')
        
        # 6. التذييل والفتح
        pdf.set_text_color(0, 0, 0)
        pdf.ln(10)
        pdf.set_font('Arabic', size=9)
        pdf.cell(0, 8, ar("طُبع بواسطة نظام OPS لإدارة المخزون"), ln=True, align='C')
        
        pdf.output(filepath)
        open_file_android(filepath) # دالة الفتح الآمنة الموحدة
        
        return filepath
        
    except Exception as e:
        Logger.error(f"OPS PDF: Error creating supplier statement - {e}")
        return None