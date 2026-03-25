"""
OPS Reports Screen
شاشة التقارير لنظام OPS
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.spinner import Spinner
from kivy.uix.datepicker import DatePicker
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, ObjectProperty
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.utils import platform

import sqlite3
import os
from datetime import datetime, date, timedelta
from database import get_db_connection

# استيراد دوال PDF
try:
    from utils.pdf_generator import create_sales_report
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    Logger.warning("OPS Reports: PDF generator not available")


class ReportItem(BoxLayout):
    """عنصر تقرير في القائمة"""
    barcode = StringProperty("")
    name = StringProperty("")
    qty = NumericProperty(0)
    total = NumericProperty(0)
    date = StringProperty("")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 45
        self.padding = [5, 5]
        self.spacing = 5


class ReportsRecycleView(RecycleView):
    """عرض بيانات التقارير"""
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


class ReportsScreen(Screen):
    """شاشة التقارير الرئيسية"""
    
    # متغيرات الإحصائيات
    total_sales = StringProperty("₪ 0.00")
    total_items = StringProperty("0")
    net_sales = StringProperty("₪ 0.00")
    
    # متغيرات التاريخ
    start_date = StringProperty("")
    end_date = StringProperty("")
    opening_balance = StringProperty("0")
    
    # حالة التحميل
    loading = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # تعيين التواريخ الافتراضية
        today = date.today()
        self.start_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
        self.end_date = today.strftime("%Y-%m-%d")
        self.load_report()
    
    def on_enter(self):
        """عند دخول الشاشة"""
        self.load_report()
        Logger.info("OPS Reports: Screen entered")
    
    def open_date_picker(self, is_start=True):
        """فتح منتقي التاريخ"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # منتقي التاريخ
        date_picker = DatePicker()
        content.add_widget(date_picker)
        
        # أزرار التحكم
        buttons = BoxLayout(size_hint_y=None, height=50, spacing=10)
        btn_ok = Button(text="تأكيد", font_name='ArabicFont', background_color=(0.2, 0.6, 0.2, 1))
        btn_cancel = Button(text="إلغاء", font_name='ArabicFont', background_color=(0.6, 0.2, 0.2, 1))
        buttons.add_widget(btn_ok)
        buttons.add_widget(btn_cancel)
        content.add_widget(buttons)
        
        popup = Popup(title="اختر التاريخ", content=content, size_hint=(0.8, 0.8))
        
        def set_date(instance):
            selected_date = date_picker.get_selected_date()
            if selected_date:
                if is_start:
                    self.start_date = selected_date.strftime("%Y-%m-%d")
                else:
                    self.end_date = selected_date.strftime("%Y-%m-%d")
            popup.dismiss()
        
        btn_ok.bind(on_press=set_date)
        btn_cancel.bind(on_press=popup.dismiss)
        
        popup.open()
    
    def load_report(self):
        """تحميل بيانات التقرير"""
        self.loading = True
        try:
            # تنظيف الجدول
            self.report_list.data = []
            
            start = self.start_date
            end = self.end_date
            
            try:
                opening = float(self.opening_balance) if self.opening_balance else 0.0
            except ValueError:
                opening = 0.0
                self.opening_balance = "0"
            
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            # استعلام المبيعات
            query = """
                SELECT s.barcode, 
                       COALESCE(p.name, 'منتج غير معروف') as name, 
                       s.quantity, 
                       s.total, 
                       s.date 
                FROM sales s
                LEFT JOIN products p ON s.barcode = p.barcode
                WHERE date(s.date) BETWEEN date(?) AND date(?)
                ORDER BY s.date DESC
            """
            c.execute(query, (start, end))
            sales = c.fetchall()
            
            total_sales_sum = 0
            total_items_sum = 0
            
            data = []
            for sale in sales:
                data.append({
                    'barcode': sale['barcode'],
                    'name': sale['name'],
                    'qty': sale['quantity'],
                    'total': sale['total'],
                    'date': sale['date']
                })
                total_sales_sum += sale['total']
                total_items_sum += sale['quantity']
            
            self.report_list.data = data
            
            net_sales_sum = total_sales_sum - opening
            self.total_sales = f"₪ {total_sales_sum:.2f}"
            self.total_items = str(total_items_sum)
            self.net_sales = f"₪ {net_sales_sum:.2f}"
            
            conn.close()
            Logger.info(f"OPS Reports: Loaded {len(data)} sales records")
            
        except Exception as e:
            Logger.error(f"OPS Reports: Error loading report - {e}")
            self.show_popup("خطأ", f"حدث خطأ في تحميل البيانات: {str(e)}")
        finally:
            self.loading = False
    
    def print_report(self):
        """طباعة التقرير PDF"""
        if not PDF_AVAILABLE:
            self.show_popup("تنبيه", "خدمة الطباعة غير متوفرة حالياً")
            return
        
        try:
            self.loading = True
            
            # جمع بيانات المبيعات
            sales_data = []
            for item in self.report_list.data:
                sales_data.append({
                    'barcode': item['barcode'],
                    'name': item['name'],
                    'quantity': item['qty'],
                    'price': item['total'] / item['qty'] if item['qty'] > 0 else 0,
                    'total': item['total'],
                    'date': item['date']
                })
            
            total_sales_num = float(self.total_sales.replace('₪ ', ''))
            net_sales_num = float(self.net_sales.replace('₪ ', ''))
            
            result = create_sales_report(
                sales_data, 
                self.start_date, 
                self.end_date, 
                total_sales_num, 
                net_sales_num
            )
            
            self.loading = False
            
            if result:
                self.show_popup("نجاح", "✅ تم إنشاء التقرير بنجاح\nسيتم فتحه تلقائياً")
            else:
                self.show_popup("خطأ", "فشل إنشاء التقرير")
                
        except Exception as e:
            self.loading = False
            Logger.error(f"OPS Reports: Error printing report - {e}")
            self.show_popup("خطأ", f"حدث خطأ: {str(e)}")
    
    def go_back(self):
        """العودة للشاشة الرئيسية"""
        self.manager.current = 'dashboard'
    
    def show_popup(self, title, message):
        """عرض نافذة منبثقة"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=message, font_name='ArabicFont', halign='center', text_size=(400, None)))
        
        btn = Button(text="موافق", size_hint_y=0.3, font_name='ArabicFont')
        popup = Popup(title=title, content=content, size_hint=(0.8, 0.5))
        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        
        popup.open()


class DailySalesReportScreen(Screen):
    """شاشة تقرير المبيعات المتقدم"""
    
    # متغيرات الإحصائيات
    total_sales = StringProperty("₪ 0.00")
    total_items = StringProperty("0")
    net_sales = StringProperty("₪ 0.00")
    
    # متغيرات التاريخ
    start_date = StringProperty("")
    end_date = StringProperty("")
    opening_balance = StringProperty("0")
    
    # حالة التحميل
    loading = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # تعيين التواريخ الافتراضية
        today = date.today()
        self.start_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
        self.end_date = today.strftime("%Y-%m-%d")
        self.load_report()
    
    def on_enter(self):
        """عند دخول الشاشة"""
        self.load_report()
        Logger.info("OPS Daily Sales Report: Screen entered")
    
    def open_start_date_picker(self):
        """فتح منتقي تاريخ البداية"""
        self._open_date_picker(is_start=True)
    
    def open_end_date_picker(self):
        """فتح منتقي تاريخ النهاية"""
        self._open_date_picker(is_start=False)
    
    def _open_date_picker(self, is_start=True):
        """فتح منتقي التاريخ"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        date_picker = DatePicker()
        content.add_widget(date_picker)
        
        buttons = BoxLayout(size_hint_y=None, height=50, spacing=10)
        btn_ok = Button(text="تأكيد", font_name='ArabicFont', background_color=(0.2, 0.6, 0.2, 1))
        btn_cancel = Button(text="إلغاء", font_name='ArabicFont', background_color=(0.6, 0.2, 0.2, 1))
        buttons.add_widget(btn_ok)
        buttons.add_widget(btn_cancel)
        content.add_widget(buttons)
        
        popup = Popup(title="اختر التاريخ", content=content, size_hint=(0.8, 0.8))
        
        def set_date(instance):
            selected_date = date_picker.get_selected_date()
            if selected_date:
                if is_start:
                    self.start_date = selected_date.strftime("%Y-%m-%d")
                else:
                    self.end_date = selected_date.strftime("%Y-%m-%d")
            popup.dismiss()
        
        btn_ok.bind(on_press=set_date)
        btn_cancel.bind(on_press=popup.dismiss)
        
        popup.open()
    
    def load_report(self):
        """تحميل بيانات التقرير"""
        self.loading = True
        try:
            # تنظيف الجدول
            self.report_list.data = []
            
            start = self.start_date
            end = self.end_date
            
            try:
                opening = float(self.opening_balance) if self.opening_balance else 0.0
            except ValueError:
                opening = 0.0
                self.opening_balance = "0"
            
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            # استعلام المبيعات
            query = """
                SELECT s.barcode, 
                       COALESCE(p.name, 'منتج غير معروف') as name, 
                       s.quantity, 
                       s.total, 
                       s.date 
                FROM sales s
                LEFT JOIN products p ON s.barcode = p.barcode
                WHERE date(s.date) BETWEEN date(?) AND date(?)
                ORDER BY s.date DESC
            """
            c.execute(query, (start, end))
            sales = c.fetchall()
            
            total_sales_sum = 0
            total_items_sum = 0
            
            data = []
            for sale in sales:
                data.append({
                    'barcode': sale['barcode'],
                    'name': sale['name'],
                    'qty': sale['quantity'],
                    'total': sale['total'],
                    'date': sale['date']
                })
                total_sales_sum += sale['total']
                total_items_sum += sale['quantity']
            
            self.report_list.data = data
            
            net_sales_sum = total_sales_sum - opening
            self.total_sales = f"₪ {total_sales_sum:.2f}"
            self.total_items = str(total_items_sum)
            self.net_sales = f"₪ {net_sales_sum:.2f}"
            
            conn.close()
            Logger.info(f"OPS Daily Sales Report: Loaded {len(data)} sales records")
            
        except Exception as e:
            Logger.error(f"OPS Daily Sales Report: Error loading report - {e}")
            self.show_popup("خطأ", f"حدث خطأ في تحميل البيانات: {str(e)}")
        finally:
            self.loading = False
    
    def print_report(self):
        """طباعة التقرير PDF"""
        if not PDF_AVAILABLE:
            self.show_popup("تنبيه", "خدمة الطباعة غير متوفرة حالياً")
            return
        
        try:
            self.loading = True
            
            # جمع بيانات المبيعات
            sales_data = []
            for item in self.report_list.data:
                sales_data.append({
                    'barcode': item['barcode'],
                    'name': item['name'],
                    'quantity': item['qty'],
                    'price': item['total'] / item['qty'] if item['qty'] > 0 else 0,
                    'total': item['total'],
                    'date': item['date']
                })
            
            total_sales_num = float(self.total_sales.replace('₪ ', ''))
            net_sales_num = float(self.net_sales.replace('₪ ', ''))
            
            result = create_sales_report(
                sales_data, 
                self.start_date, 
                self.end_date, 
                total_sales_num, 
                net_sales_num
            )
            
            self.loading = False
            
            if result:
                self.show_popup("نجاح", "✅ تم إنشاء التقرير بنجاح\nسيتم فتحه تلقائياً")
            else:
                self.show_popup("خطأ", "فشل إنشاء التقرير")
                
        except Exception as e:
            self.loading = False
            Logger.error(f"OPS Daily Sales Report: Error printing report - {e}")
            self.show_popup("خطأ", f"حدث خطأ: {str(e)}")
    
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