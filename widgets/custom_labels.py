"""
Custom Labels Widgets
تسميات مخصصة للتطبيق
"""

from kivy.uix.label import Label
from kivy.properties import StringProperty, NumericProperty, ColorProperty


class CustomLabel(Label):
    """
    تسمية مخصصة مع دعم اللغة العربية
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_name = 'ArabicFont'
        self.font_size = 14
        self.halign = 'right'
        self.valign = 'middle'
        self.text_size = (self.width, None)
        self.bind(width=self.update_text_size)
    
    def update_text_size(self, instance, value):
        """تحديث حجم النص"""
        self.text_size = (value, None)


class TitleLabel(CustomLabel):
    """
    تسمية للعناوين الرئيسية
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_size = 24
        self.bold = True
        self.color = (0.2, 0.3, 0.4, 1)


class SubtitleLabel(CustomLabel):
    """
    تسمية للعناوين الفرعية
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_size = 18
        self.bold = True
        self.color = (0.3, 0.4, 0.5, 1)


class ErrorLabel(CustomLabel):
    """
    تسمية لعرض الأخطاء
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_size = 14
        self.color = (0.9, 0.2, 0.2, 1)
        self.bold = True


class SuccessLabel(CustomLabel):
    """
    تسمية لعرض رسائل النجاح
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_size = 14
        self.color = (0.2, 0.7, 0.2, 1)
        self.bold = True


class WarningLabel(CustomLabel):
    """
    تسمية لعرض التحذيرات
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_size = 14
        self.color = (0.9, 0.6, 0.1, 1)
        self.bold = True


class InfoLabel(CustomLabel):
    """
    تسمية للمعلومات الإضافية
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_size = 12
        self.color = (0.5, 0.5, 0.5, 1)