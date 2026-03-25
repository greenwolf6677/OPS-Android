"""
OPS Utilities Module
الوحدات المساعدة لنظام OPS
"""

from .helpers import (
    format_currency,
    format_date,
    format_datetime,
    generate_id,
    generate_barcode,
    validate_email,
    validate_phone,
    truncate_text,
    sanitize_input,
    calculate_percentage,
    calculate_discount,
    get_current_time,
    get_current_date,
    time_ago,
    dict_to_list,
    list_to_dict,
    group_by,
    sort_by_key,
    filter_by_value,
    safe_divide,
    round_number,
    is_number,
    is_integer,
    is_float
)

from .arabic_text import (
    format_arabic,
    normalize_arabic,
    search_arabic,
    remove_diacritics,
    is_arabic_char,
    get_arabic_chars,
    arabic_to_slug,
    arabic_collator,
    ARABIC_LETTERS,
    ARABIC_NUMBERS
)

__all__ = [
    # helpers
    'format_currency',
    'format_date', 
    'format_datetime',
    'generate_id',
    'generate_barcode',
    'validate_email',
    'validate_phone',
    'truncate_text',
    'sanitize_input',
    'calculate_percentage',
    'calculate_discount',
    'get_current_time',
    'get_current_date',
    'time_ago',
    'dict_to_list',
    'list_to_dict',
    'group_by',
    'sort_by_key',
    'filter_by_value',
    'safe_divide',
    'round_number',
    'is_number',
    'is_integer',
    'is_float',
    
    # arabic_text
    'format_arabic',
    'normalize_arabic', 
    'search_arabic',
    'remove_diacritics',
    'is_arabic_char',
    'get_arabic_chars',
    'arabic_to_slug',
    'arabic_collator',
    'ARABIC_LETTERS',
    'ARABIC_NUMBERS'
]