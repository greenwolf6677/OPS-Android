[app]

# اسم التطبيق (بدون مسافات)
title = OPS

# اسم الحزمة (بحروف صغيرة فقط)
package.name = ops
package.domain = org.ops

# الإصدار
version = 1.0.0

# متطلبات التطبيق
requirements = python3,kivy,kivymd,sqlite3,fpdf2,Pillow,plyer,pyjnius,cryptography,requests

# إعدادات العرض
orientation = landscape
fullscreen = 0

# الأذونات
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE, VIBRATE

# الأيقونة
icon.filename = assets/icon/logo.png

# شاشة البداية
presplash.filename = assets/icon/logo.png

# اللغة العربية
android.default_language = ar
android.accept_sdk_license = True

# دقة SDK و NDK (استخدم NDK 25b)
android.ndk = 25b
android.sdk = 30
android.minapi = 21

# أسماء الشاشات
android.manifest.launch_mode = singleTask

# تضمين مجلدات المصدر
source.include_exts = py,png,jpg,kv,ttf,db,wav

# المجلدات المستبعدة
source.exclude_exts = spec,pyc,pyo
source.exclude_patterns = __pycache__,docs

# مسار مجلد المصادر
source.dir = .

# إعدادات Logging
android.logcat_filters = *:S python:D

# bootstrap
bootstrap = sdl2