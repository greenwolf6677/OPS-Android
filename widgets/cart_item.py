"""
Cart Item Widget
عرض عنصر في سلة المشتريات
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.clock import Clock


class CartItem(BoxLayout):
    """
    عنصر في سلة المشتريات يعرض:
    - اسم المنتج
    - السعر
    - الكمية
    - الإجمالي
    - زر حذف
    """
    
    barcode = StringProperty("")
    product_name = StringProperty("")
    price = NumericProperty(0.0)
    quantity = NumericProperty(1)
    subtotal = NumericProperty(0.0)
    discount = NumericProperty(0.0)
    is_selected = BooleanProperty(False)
    item_index = NumericProperty(0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 60
        self.padding = [5, 5]
        self.spacing = 5
        
        self._build_ui()
        self.bind(quantity=self.update_subtotal)
        self.bind(price=self.update_subtotal)
    
    def _build_ui(self):
        """بناء واجهة العنصر"""
        
        # اسم المنتج
        self.name_label = Label(
            text=self.product_name,
            font_size=14,
            font_name='ArabicFont',
            halign='right',
            text_size=(200, None),
            size_hint_x=0.35
        )
        self.add_widget(self.name_label)
        
        # السعر
        self.price_label = Label(
            text=f"{self.price:.2f}",
            font_size=14,
            font_name='ArabicFont',
            size_hint_x=0.12
        )
        self.add_widget(self.price_label)
        
        # الكمية
        self.qty_layout = BoxLayout(size_hint_x=0.15, spacing=5)
        
        self.qty_minus = Button(
            text="-",
            font_size=14,
            size_hint_x=0.3,
            background_color=(0.6, 0.2, 0.2, 1)
        )
        self.qty_minus.bind(on_press=self.decrease_qty)
        
        self.qty_label = Label(
            text=str(self.quantity),
            font_size=14,
            font_name='ArabicFont',
            size_hint_x=0.4
        )
        
        self.qty_plus = Button(
            text="+",
            font_size=14,
            size_hint_x=0.3,
            background_color=(0.2, 0.6, 0.2, 1)
        )
        self.qty_plus.bind(on_press=self.increase_qty)
        
        self.qty_layout.add_widget(self.qty_minus)
        self.qty_layout.add_widget(self.qty_label)
        self.qty_layout.add_widget(self.qty_plus)
        self.add_widget(self.qty_layout)
        
        # الإجمالي
        self.subtotal_label = Label(
            text=f"{self.subtotal:.2f}",
            font_size=14,
            font_name='ArabicFont',
            color=(0.2, 0.6, 0.2, 1),
            size_hint_x=0.15
        )
        self.add_widget(self.subtotal_label)
        
        # زر الحذف
        self.delete_btn = Button(
            text="🗑️",
            font_size=14,
            size_hint_x=0.08,
            background_color=(0.8, 0.2, 0.2, 1)
        )
        self.delete_btn.bind(on_press=self.on_delete)
        self.add_widget(self.delete_btn)
        
        # ربط الخصائص
        self.bind(product_name=self.update_name)
        self.bind(price=self.update_price)
        self.bind(quantity=self.update_quantity)
        self.bind(subtotal=self.update_subtotal_label)
    
    def update_name(self, instance, value):
        """تحديث اسم المنتج"""
        self.name_label.text = value
    
    def update_price(self, instance, value):
        """تحديث السعر"""
        self.price_label.text = f"{value:.2f}"
        self.update_subtotal()
    
    def update_quantity(self, instance, value):
        """تحديث الكمية"""
        self.qty_label.text = str(value)
        self.update_subtotal()
    
    def update_subtotal(self, *args):
        """تحديث الإجمالي"""
        self.subtotal = self.quantity * self.price - self.discount
    
    def update_subtotal_label(self, instance, value):
        """تحديث عرض الإجمالي"""
        self.subtotal_label.text = f"{value:.2f}"
    
    def increase_qty(self, instance):
        """زيادة الكمية"""
        self.quantity += 1
    
    def decrease_qty(self, instance):
        """نقصان الكمية"""
        if self.quantity > 1:
            self.quantity -= 1
    
    def on_delete(self, instance):
        """حذف العنصر"""
        if hasattr(self, 'parent') and hasattr(self.parent, 'remove_widget'):
            self.parent.remove_widget(self)
        
        # إرسال إشارة للحذف
        if hasattr(self, 'callback'):
            self.callback(self.item_index)
    
    def set_delete_callback(self, callback, index):
        """تعيين دالة الاستدعاء للحذف"""
        self.callback = callback
        self.item_index = index