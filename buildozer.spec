[app]
title = OPS
package.name = ops
package.domain = org.ops
source.dir = .
source.include_exts = py,png,jpg,kv,ttf,db
source.include_dirs = assets, kv, screens, database, security, utils, widgets
version = 1.0.0

# المتطلبات الأساسية
requirements = python3, kivy, kivymd, pillow, arabic-reshaper, python-bidi, requests, sqlite3

orientation = landscape
android.permissions = INTERNET

# تعديل الإصدارات لتتوافق مع بيئة السيرفر الحالية
android.api = 33
android.minapi = 21
# ترك الـ NDK فارغاً ليقوم buildozer بتحميل النسخة المتوافقة تلقائياً
android.ndk_path = 
android.sdk_path = 
android.accept_sdk_license = True

# المعمارية المطلوبة
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1