[app]

title = OPS
package.name = ops
package.domain = org.ops
version = 1.0.0

# المتطلبات

requirements = python3,kivy,kivymd,cython

# إعدادات العرض

orientation = landscape
fullscreen = 0

# الصلاحيات

android.permissions = INTERNET

# الأيقونة (تأكد الملف موجود)

icon.filename = assets/icon/logo.png

# اللغة

android.default_language = ar

# إعدادات الأندرويد

android.api = 31
android.minapi = 21

# ملفات المشروع

source.dir = .
source.include_exts = py,png,jpg,kv,ttf,db,wav
source.exclude_exts = spec,pyc,pyo
source.exclude_patterns = **pycache**,docs

# قبول الرخصة تلقائيًا

android.accept_sdk_license = True

# نوع التشغيل

bootstrap = sdl2
