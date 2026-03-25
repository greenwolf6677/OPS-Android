"""
OPS Arabic Text Utilities
معالجة النصوص العربية
"""

import re
import unicodedata
from bidi.algorithm import get_display
import arabic_reshaper

# ==================== ثوابت ====================

# الحروف العربية
ARABIC_LETTERS = 'ابتثجحخدذرزسشصضطظعغفقكلمنهوي'
ARABIC_LETTERS_SET = set(ARABIC_LETTERS)

# الأرقام العربية
ARABIC_NUMBERS = '٠١٢٣٤٥٦٧٨٩'
ARABIC_NUMBERS_MAP = {
    '0': '٠', '1': '١', '2': '٢', '3': '٣', '4': '٤',
    '5': '٥', '6': '٦', '7': '٧', '8': '٨', '9': '٩'
}

# علامات التشكيل
DIACRITICS = 'ًٌٍَُِّْ'


# ==================== التنسيق الأساسي ====================

def format_arabic(text):
    """
    تحويل النص العربي ليظهر متصلاً وصحيحاً
    يستخدم للطباعة في PDF والواجهات
    """
    if not text:
        return ""
    try:
        reshaped_text = arabic_reshaper.reshape(str(text))
        return get_display(reshaped_text)
    except:
        return str(text)


def normalize_arabic(text):
    """
    تطبيع النص العربي (إزالة التشكيل وتوحيد الحروف)
    """
    if not text:
        return ""
    
    text = str(text)
    
    # إزالة التشكيل
    text = remove_diacritics(text)
    
    # توحيد الحروف المتشابهة
    replacements = {
        'ة': 'ه',  # التاء المربوطة
        'ى': 'ي',  # الألف المقصورة
        'ؤ': 'و',  # الواو المهموزة
        'ئ': 'ي',  # الياء المهموزة
        'أ': 'ا',  # الألف المهموزة
        'إ': 'ا',  # الألف المهموزة
        'آ': 'ا',  # الألف الممدودة
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text


def remove_diacritics(text):
    """إزالة علامات التشكيل من النص العربي"""
    if not text:
        return ""
    return ''.join(char for char in str(text) if char not in DIACRITICS)


# ==================== البحث ====================

def search_arabic(text, keyword, ignore_diacritics=True, ignore_case=True):
    """
    البحث في النص العربي
    """
    if not text or not keyword:
        return False
    
    text = str(text)
    keyword = str(keyword)
    
    if ignore_diacritics:
        text = remove_diacritics(text)
        keyword = remove_diacritics(keyword)
    
    if ignore_case:
        text = text.lower()
        keyword = keyword.lower()
    
    return keyword in text


def arabic_collator(text1, text2):
    """
    مقارنة نصوص عربية للترتيب
    """
    if not text1 and not text2:
        return 0
    if not text1:
        return -1
    if not text2:
        return 1
    
    # تطبيع النصوص قبل المقارنة
    t1 = normalize_arabic(str(text1))
    t2 = normalize_arabic(str(text2))
    
    if t1 < t2:
        return -1
    elif t1 > t2:
        return 1
    return 0


# ==================== التحقق ====================

def is_arabic_char(char):
    """التحقق من أن الحرف عربي"""
    if not char:
        return False
    # نطاق الحروف العربية في Unicode
    arabic_range = range(0x0600, 0x06FF)
    return ord(char) in arabic_range


def get_arabic_chars(text):
    """استخراج الأحرف العربية فقط"""
    if not text:
        return ""
    return ''.join(char for char in str(text) if is_arabic_char(char))


def has_arabic(text):
    """التحقق من وجود أحرف عربية في النص"""
    return bool(get_arabic_chars(text))


# ==================== التحويل ====================

def arabic_to_slug(text):
    """
    تحويل النص العربي إلى slug (رابط)
    مثال: "مرحبا بالعالم" -> "mrhaba-blaalm"
    """
    if not text:
        return ""
    
    # تطبيع النص
    text = normalize_arabic(text)
    
    # استبدال الحروف العربية بأقرب حرف لاتيني
    mapping = {
        'ا': 'a', 'ب': 'b', 'ت': 't', 'ث': 'th', 'ج': 'j', 'ح': 'h',
        'خ': 'kh', 'د': 'd', 'ذ': 'th', 'ر': 'r', 'ز': 'z', 'س': 's',
        'ش': 'sh', 'ص': 's', 'ض': 'd', 'ط': 't', 'ظ': 'z', 'ع': 'a',
        'غ': 'gh', 'ف': 'f', 'ق': 'q', 'ك': 'k', 'ل': 'l', 'م': 'm',
        'ن': 'n', 'ه': 'h', 'و': 'w', 'ي': 'y',
    }
    
    result = []
    for char in text:
        if char in mapping:
            result.append(mapping[char])
        elif char.isalnum():
            result.append(char.lower())
        elif char == ' ':
            result.append('-')
    
    # تنظيف النتيجة
    slug = ''.join(result)
    slug = re.sub(r'-+', '-', slug)
    slug = slug.strip('-')
    
    return slug


def convert_numbers(text, to_arabic=True):
    """
    تحويل الأرقام بين العربية والإنجليزية
    to_arabic=True: 123 -> ١٢٣
    to_arabic=False: ١٢٣ -> 123
    """
    if not text:
        return ""
    
    text = str(text)
    
    if to_arabic:
        # تحويل الأرقام الإنجليزية إلى عربية
        for eng, arb in ARABIC_NUMBERS_MAP.items():
            text = text.replace(eng, arb)
    else:
        # تحويل الأرقام العربية إلى إنجليزية
        for eng, arb in ARABIC_NUMBERS_MAP.items():
            text = text.replace(arb, eng)
    
    return text


# ==================== التحليل ====================

def word_count(text):
    """حساب عدد الكلمات في النص العربي"""
    if not text:
        return 0
    text = str(text)
    # تقسيم حسب المسافات وعلامات الترقيم
    words = re.split(r'[\s\.,;:!؟]+', text)
    return len([w for w in words if w])


def char_count(text, count_spaces=True):
    """حساب عدد الحروف في النص العربي"""
    if not text:
        return 0
    text = str(text)
    if not count_spaces:
        text = text.replace(' ', '')
    return len(text)


def get_sentences(text):
    """تقسيم النص إلى جمل"""
    if not text:
        return []
    # تقسيم حسب النقاط وعلامات الاستفهام والتعجب
    sentences = re.split(r'[.!?؟]+', str(text))
    return [s.strip() for s in sentences if s.strip()]


# ==================== التصحيح ====================

def fix_ligatures(text):
    """إصلاح مشاكل وصل الحروف"""
    if not text:
        return ""
    
    # إضافة مسافات بين الحروف المتصلة بشكل خاطئ
    text = re.sub(r'(?<=[ابتثجحخدذرزسشصضطظعغفقكلمنهوي])(?=[ابتثجحخدذرزسشصضطظعغفقكلمنهوي])', ' ', text)
    
    return text


def reverse_arabic(text):
    """عكس اتجاه النص العربي (للاستخدام في بعض الحالات)"""
    if not text:
        return ""
    return text[::-1]


# ==================== دوال للواجهة ====================

def truncate_arabic(text, max_length=50, suffix="..."):
    """قص النص العربي مع الحفاظ على الكلمات كاملة"""
    if not text:
        return ""
    text = str(text)
    if len(text) <= max_length:
        return text
    
    # البحث عن آخر مسافة قبل الحد الأقصى
    truncated = text[:max_length]
    last_space = truncated.rfind(' ')
    if last_space > 0:
        truncated = truncated[:last_space]
    
    return truncated + suffix


def highlight_search(text, keyword, before="<b>", after="</b>"):
    """تمييز الكلمات المطابقة للبحث في النص"""
    if not text or not keyword:
        return text
    
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    return pattern.sub(f"{before}{keyword}{after}", text)