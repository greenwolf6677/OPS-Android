"""
OPS Security Module
وحدة الأمان والحماية لنظام OPS
"""

from .android_security import (
    run_security,
    check_license,
    activate_program,
    generate_activation_code,
    get_license_info,
    get_machine_id,
    encrypt_data,
    decrypt_data,
    secure_db_connection
)

__all__ = [
    'run_security',
    'check_license',
    'activate_program',
    'generate_activation_code',
    'get_license_info',
    'get_machine_id',
    'encrypt_data',
    'decrypt_data',
    'secure_db_connection'
]