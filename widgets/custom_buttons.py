"""
Custom Buttons Widgets
أزرار مخصصة للتطبيق
"""

from kivy.uix.button import Button
from kivy.properties import StringProperty, NumericProperty, ColorProperty
from kivy.animation import Animation
from kivy.clock import Clock


class CustomButton(Button):
    """
    زر مخصص مع تأثيرات حركية
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0.2, 0.5, 0.8, 1)
        self.font_name = 'ArabicFont'
        self.font_size = 16
        self.bold = True
        self.padding = [10, 8]
        
        # ربط الأحداث
        self.bind(on_press=self.on_press_animate)
        self.bind(on_release=self.on_release_animate)
    
    def on_press_animate(self, instance):
        """تأثير عند الضغط"""
        anim = Animation(size_hint=(self.size_hint_x, self.size_hint_y * 0.95), 
                         duration=0.05)
        anim.start(self)
    
    def on_release_animate(self, instance):
        """تأثير عند الرفع"""
        anim = Animation(size_hint=(self.size_hint_x, self.size_hint_y), 
                         duration=0.05)
        anim.start(self)


class IconButton(CustomButton):
    """
    زر مع أيقونة ونص
    """
    
    icon = StringProperty("")
    button_text = StringProperty("")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(icon=self.update_text)
        self.bind(button_text=self.update_text)
        self.update_text()
    
    def update_text(self, *args):
        """تحديث النص مع الأيقونة"""
        if self.icon:
            self.text = f"{self.icon} {self.button_text}"
        else:
            self.text = self.button_text


class ActionButton(CustomButton):
    """
    زر إجراء (إضافة، تعديل، حذف)
    """
    
    action_type = StringProperty("add")  # add, edit, delete, save, cancel
    
    action_colors = {
        'add': (0.2, 0.6, 0.2, 1),      # أخضر
        'edit': (0.2, 0.5, 0.8, 1),     # أزرق
        'delete': (0.8, 0.2, 0.2, 1),   # أحمر
        'save': (0.2, 0.6, 0.2, 1),     # أخضر
        'cancel': (0.6, 0.6, 0.6, 1),   # رمادي
        'search': (0.2, 0.5, 0.8, 1),   # أزرق
        'print': (0.2, 0.5, 0.7, 1),    # أزرق داكن
        'refresh': (0.2, 0.6, 0.8, 1),  # سماوي
    }
    
    action_icons = {
        'add': "➕",
        'edit': "✏️",
        'delete': "🗑️",
        'save': "💾",
        'cancel': "❌",
        'search': "🔍",
        'print': "🖨️",
        'refresh': "🔄",
    }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(action_type=self.update_action)
        self.update_action()
    
    def update_action(self, *args):
        """تحديث شكل الزر حسب نوع الإجراء"""
        self.background_color = self.action_colors.get(self.action_type, (0.2, 0.5, 0.8, 1))
        
        icon = self.action_icons.get(self.action_type, "")
        text = self.text or self.action_type
        
        if icon:
            self.text = f"{icon} {text}"