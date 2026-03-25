[app]

# معلومات التطبيق
title = OPS
package.name = ops
package.domain = org.ops
version = 1.0.0

# المتطلبات
requirements = python3,kivy,kivymd,cython

# الإعدادات
orientation = landscape
fullscreen = 0
android.permissions = INTERNET

# الأيقونة والخط
icon.filename = assets/icon/logo.png
android.default_language = ar

# المسارات والملفات
source.dir = .
source.include_exts = py,png,jpg,kv,ttf,db,wav
source.exclude_exts = spec,pyc,pyo
source.exclude_patterns = __pycache__,docs

# إعدادات Android (اترك Buildozer يدير SDK/NDK تلقائياً)
bootstrap = sdl2
android.accept_sdk_license = True