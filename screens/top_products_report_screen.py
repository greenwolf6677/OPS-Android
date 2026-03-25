"""
OPS Top Products Report Screen
شاشة تقرير الأصناف الأكثر مبيعاً
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.utils import platform

import sqlite3
from datetime import datetime, date, timedelta
from database import get_db_connection

# استيراد دوال PDF
try:
    from utils.pdf_generator import create_top_products_report
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    Logger.warning("OPS Reports: PDF generator not available")


class TopProductItem(BoxLayout):
    """عنصر منتج في قائمة الأكثر مبيعاً"""
    rank = NumericProperty(0)
    name = StringProperty("")
    total_qty = NumericProperty(0)
    total_sales = NumericProperty(0)
    avg_price = NumericProperty(0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 45
        self.padding = [5, 5]
        self.spacing = 5


class TopProductsRecycleView(RecycleView):
    """عرض قائمة الأصناف الأكثر مبيعاً"""
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


class TopProductsReportScreen(Screen):
    """شاشة تقرير الأصناف الأكثر مبيعاً"""
    
    # متغيرات الفلترة
    start_date = StringProperty("")
    end_date = StringProperty("")
    limit = StringProperty("10")
    
    # متغيرات الإحصائيات
    total_products = StringProperty("0")
    total_sales = StringProperty("₪ 0.00")
    
    # حالة التحميل
    loading = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        today = date.today()
        self.start_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
        self.end_date = today.strftime("%Y-%m-%d")
        self.load_report()
    
    def on_enter(self):
        """عند دخول الشاشة"""
        self.load_report()
        Logger.info("OPS Top Products Report: Screen entered")
    
    def open_start_date_picker(self):
        """فتح منتقي تاريخ البداية"""
        self._open_date_picker(is_start=True)
    
    def open_end_date_picker(self):
        """فتح منتقي تاريخ النهاية"""
        self._open_date_picker(is_start=False)
    
    def _open_date_picker(self, is_start=True):
        """فتح منتقي التاريخ"""
        from kivy.uix.calendar import CalendarWidget
        from kivy.uix.modalview import ModalView
        
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        calendar = CalendarWidget()
        content.add_widget(calendar)
        
        buttons = BoxLayout(size_hint_y=None, height=50, spacing=10)
        btn_ok = Button(text="تأكيد", font_name='ArabicFont', background_color=(0.2, 0.6, 0.2, 1))
        btn_cancel = Button(text="إلغاء", font_name='ArabicFont', background_color=(0.6, 0.2, 0.2, 1))
        buttons.add_widget(btn_ok)
        buttons.add_widget(btn_cancel)
        content.add_widget(buttons)
        
        popup = Popup(title="اختر التاريخ", content=content, size_hint=(0.8, 0.8))
        
        def set_date(instance):
            selected_date = calendar.get_selected_date()
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
            self.products_list.data = []
            
            start = self.start_date
            end = self.end_date
            limit_num = int(self.limit) if self.limit.isdigit() else 10
            
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            query = """
                SELECT 
                    COALESCE(p.name, 'منتج غير معروف') as name,
                    SUM(s.quantity) as total_qty,
                    SUM(s.total) as total_sales,
                    AVG(s.price) as avg_price
                FROM sales s
                LEFT JOIN products p ON s.barcode = p.barcode
                WHERE date(s.date) BETWEEN date(?) AND date(?)
                GROUP BY s.barcode
                ORDER BY total_qty DESC, total_sales DESC
                LIMIT ?
            """
            c.execute(query, (start, end, limit_num))
            results = c.fetchall()
            
            data = []
            total_sales_sum = 0
            
            for i, row in enumerate(results, 1):
                data.append({
                    'rank': i,
                    'name': row['name'],
                    'total_qty': row['total_qty'],
                    'total_sales': row['total_sales'],
                    'avg_price': row['avg_price']
                })
                total_sales_sum += row['total_sales']
            
            self.products_list.data = data
            self.total_products = str(len(data))
            self.total_sales = f"₪ {total_sales_sum:.2f}"
            
            conn.close()
            Logger.info(f"OPS Top Products Report: Loaded {len(data)} products")
            
        except Exception as e:
            Logger.error(f"OPS Top Products Report: Error loading report - {e}")
            self.show_popup("خطأ", f"حدث خطأ: {str(e)}")
        finally:
            self.loading = False
    
    def print_report(self):
        """طباعة التقرير PDF"""
        if not PDF_AVAILABLE:
            self.show_popup("تنبيه", "خدمة الطباعة غير متوفرة حالياً")
            return
        
        try:
            self.loading = True
            
            products_data = []
            for item in self.products_list.data:
                products_data.append({
                    'rank': item['rank'],
                    'name': item['name'],
                    'total_qty': item['total_qty'],
                    'total_sales': item['total_sales'],
                    'avg_price': item['avg_price']
                })
            
            total_sales_num = float(self.total_sales.replace('₪ ', ''))
            
            result = create_top_products_report(
                products_data, 
                self.start_date, 
                self.end_date, 
                total_sales_num
            )
            
            self.loading = False
            
            if result:
                self.show_popup("نجاح", "✅ تم إنشاء التقرير بنجاح")
            else:
                self.show_popup("خطأ", "فشل إنشاء التقرير")
                
        except Exception as e:
            self.loading = False
            Logger.error(f"OPS Top Products Report: Error printing report - {e}")
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