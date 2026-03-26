[app]
# (str) Title of your application
title = OPS

# (str) Package name
package.name = ops

# (str) Package domain (needed for android packaging)
package.domain = org.ops

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include
source.include_exts = py,png,jpg,kv,ttf,db

# (list) List of directory to include
source.include_dirs = assets, kv, screens, database, security, utils, widgets

# (str) Application versioning
version = 1.0.0

# (list) Application requirements
# تم حذف hostpython3 لتقليل التعارض وتثبيت النسخ المستقرة
requirements = python3, kivy, kivymd, pillow, arabic-reshaper, python-bidi, requests, sqlite3

# (str) Supported orientations
orientation = landscape

# (list) Permissions
android.permissions = INTERNET

# (int) Target Android API
android.api = 33

# (int) Minimum API your APK will support
android.minapi = 21

# (str) Android NDK version to use
android.ndk = 25b

# (bool) If True, then automatically accept SDK license
android.accept_sdk_license = True

# (list) Android architectures to build for
# بناء معمارية واحدة فقط لضمان عدم استهلاك ذاكرة السيرفر
android.archs = arm64-v8a

# (str) Bootstrap to use for android
bootstrap = sdl2

# (bool) Force the update of the android toolchain
android.skip_update = False

# ==================== Buildozer Settings ====================

[buildozer]
# (int) Log level (1 لتقليل حجم السجلات ومنع تعليق السيرفر)
log_level = 1

# (int) Display warning if buildozer is run as root
warn_on_root = 1