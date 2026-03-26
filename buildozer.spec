[app]

# (str) Title of your application
title = OPS Android

# (str) Package name
package.name = ops_android

# (str) Package domain (needed for android packaging)
package.domain = org.ops

# (str) Source code where the main.py live
source.dir = .

# (str) Version of your application
version = 1.0.0

# (list) Source files to include
source.include_exts = py,png,jpg,kv,ttf,db

# (list) List of directory to include
source.include_dirs = assets, database, kv, screens, security, utils, widgets

# (list) List of exclusions
source.exclude_dirs = tests, bin, venv, .git, .github

# (list) Application requirements
# ملاحظة: تم ترتيب المكتبات لضمان بناء sqlite3 و pillow بشكل صحيح
requirements = python3, kivy==2.3.0, kivymd==1.2.0, pillow, arabic-reshaper, python-bidi, six, requests, sqlite3, fpdf2

# (str) Supported orientations
orientation = portrait

# (list) Permissions
android.permissions = INTERNET, CAMERA, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE

# (int) Target Android API
android.api = 33

# (int) Minimum API
android.minapi = 21

# (str) Android NDK version to use (إصدار مستقر جداً مع Kivy)
android.ndk = 25b

# (bool) Use --private data storage
android.private_storage = True

# (list) The Android archs to build for
android.archs = arm64-v8a, armeabi-v7a

# (bool) enables Android auto backup
android.allow_backup = True

# (bool) Indicate if the application should be etched for a logcat or not
android.logcat = True

# (int) Log level (2 = debug)
log_level = 2

[buildozer]
warn_on_root = 1