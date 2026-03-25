"""
Data Table Widget
جدول بيانات مخصص مع دعم التمرير والتحديد
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.properties import ListProperty, StringProperty, NumericProperty, BooleanProperty
from kivy.clock import Clock


class TableColumn:
    """تعريف عمود في الجدول"""
    
    def __init__(self, title, width=100, align='center', key=None):
        self.title = title
        self.width = width
        self.align = align
        self.key = key or title


class DataTable(BoxLayout):
    """
    جدول بيانات متقدم مع:
    - رأس ثابت
    - تمرير عمودي وأفقي
    - تحديد الصفوف
    - تنسيق مخصص
    """
    
    columns = ListProperty([])
    data = ListProperty([])
    selectable = BooleanProperty(True)
    on_row_click = None
    selected_row = NumericProperty(-1)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self._build_ui()
        self.bind(data=self.refresh)
        self.bind(columns=self.refresh)
    
    def _build_ui(self):
        """بناء واجهة الجدول"""
        
        # إطار الجدول الرئيسي
        self.table_container = BoxLayout(orientation='vertical', size_hint_y=1)
        self.add_widget(self.table_container)
    
    def refresh(self, *args):
        """تحديث عرض الجدول"""
        self.table_container.clear_widgets()
        
        # إنشاء رأس الجدول
        self._create_header()
        
        # إنشاء محتوى الجدول مع تمرير
        scroll = ScrollView()
        content = GridLayout(cols=len(self.columns), size_hint_y=None, spacing=1)
        content.bind(minimum_height=content.setter('height'))
        
        # إضافة الصفوف
        for row_index, row_data in enumerate(self.data):
            for col_index, col in enumerate(self.columns):
                cell_value = row_data.get(col.key, '') if isinstance(row_data, dict) else row_data[col_index]
                
                cell = Label(
                    text=str(cell_value),
                    font_name='ArabicFont',
                    font_size=12,
                    size_hint_x=None,
                    width=col.width,
                    halign=col.align,
                    valign='middle',
                    text_size=(col.width, None)
                )
                
                # تلوين الصف المحدد
                if self.selectable and row_index == self.selected_row:
                    cell.color = (1, 1, 1, 1)
                    cell.canvas.before.clear()
                    with cell.canvas.before:
                        from kivy.graphics import Color, Rectangle
                        Color(0.2, 0.5, 0.8, 1)
                        Rectangle(pos=cell.pos, size=cell.size)
                
                content.add_widget(cell)
        
        scroll.add_widget(content)
        self.table_container.add_widget(scroll)
    
    def _create_header(self):
        """إنشاء رأس الجدول"""
        header_layout = GridLayout(cols=len(self.columns), size_hint_y=None, height=45, spacing=1)
        
        for col in self.columns:
            header_cell = Label(
                text=col.title,
                font_name='ArabicFont',
                font_size=14,
                bold=True,
                size_hint_x=None,
                width=col.width,
                halign='center',
                valign='middle',
                color=(1, 1, 1, 1),
                text_size=(col.width, None)
            )
            header_cell.canvas.before.clear()
            with header_cell.canvas.before:
                from kivy.graphics import Color, Rectangle
                Color(0.2, 0.3, 0.4, 1)
                Rectangle(pos=header_cell.pos, size=header_cell.size)
            
            header_layout.add_widget(header_cell)
        
        self.table_container.add_widget(header_layout)
    
    def set_data(self, data):
        """تعيين بيانات الجدول"""
        self.data = data
    
    def set_columns(self, columns):
        """تعيين أعمدة الجدول"""
        self.columns = columns
    
    def select_row(self, index):
        """تحديد صف"""
        if 0 <= index < len(self.data):
            self.selected_row = index
            self.refresh()
            
            if self.on_row_click:
                self.on_row_click(self.data[index], index)
    
    def clear(self):
        """مسح الجدول"""
        self.data = []
        self.selected_row = -1
        self.refresh()


class EditableDataTable(DataTable):
    """
    جدول بيانات قابل للتعديل
    """
    
    editable = BooleanProperty(True)
    on_cell_edit = None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.editable_cells = {}
    
    def _create_cell(self, row_index, col_index, col, value):
        """إنشاء خلية قابلة للتعديل"""
        from kivy.uix.textinput import TextInput
        
        cell = TextInput(
            text=str(value),
            font_name='ArabicFont',
            font_size=12,
            size_hint_x=None,
            width=col.width,
            halign=col.align,
            multiline=False,
            background_color=(1, 1, 1, 1)
        )
        
        # ربط تغيير القيمة
        cell.bind(text=lambda instance, val: self._on_cell_edit(row_index, col_index, col, val))
        
        return cell
    
    def _on_cell_edit(self, row, col, column, value):
        """معالجة تعديل الخلية"""
        if self.on_cell_edit:
            self.on_cell_edit(row, col, value)