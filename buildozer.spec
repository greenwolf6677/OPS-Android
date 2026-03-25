[app]

title = OPS
package.name = ops
package.domain = org.ops
version = 1.0.0

<<<<<<< HEAD
requirements = python3,kivy,kivymd,cython

orientation = landscape
fullscreen = 0

android.permissions = INTERNET

icon.filename = assets/icon/logo.png
android.default_language = ar

android.api = 31
android.minapi = 21

source.dir = .
source.include_exts = py,png,jpg,kv,ttf,db,wav
source.exclude_exts = spec,pyc,pyo
source.exclude_patterns = __pycache__,docs

android.accept_sdk_license = True
bootstrap = sdl2
=======
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
>>>>>>> dd728929031544e3f9f13691df9f3960576815a7
