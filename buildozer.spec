[app]

# (str) Title of your application
title = OPS Android

# (str) Package name
package.name = ops_android

# (str) Package domain (needed for android packaging)
package.domain = org.ops

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let's be safe and include everything)
source.include_exts = py,png,jpg,kv,ttf,db

# (list) List of directory to include
source.include_dirs = assets, database, kv, screens, security, utils, widgets

# (list) List of exclusions
source.exclude_dirs = tests, bin, venv, .git, .github

# (str) Application versioning (method 1)
version = 1.0.0

# (list) Application requirements
# تم إضافة المكتبات الأساسية مع ضمان توافقها
requirements = python3, kivy==2.3.0, kivymd==1.2.0, pillow, arabic-reshaper, python-bidi, six, requests, sqlite3, fpdf2

# (str) Supported orientations
orientation = portrait

# (list) Permissions
# تم إضافة أذونات الكاميرا والتخزين والإنترنت
android.permissions = INTERNET, CAMERA, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE

# (int) Target Android API (يجب أن يكون 33 أو أكثر لعام 2026)
android.api = 33

# (int) Minimum API your APK will support (Android 5.0+)
android.minapi = 21

# (str) Android SDK version to use
android.sdk = 33

# (str) Android build-tools version to use
# تحديد النسخة يمنع النظام من تحميل النسخ التجريبية المسببة للأخطاء
android.build_tools_version = 33.0.0

# (str) Android NDK version to use
android.ndk = 25b

# (bool) If True, then automatically accept SDK license
# ضروري جداً لنجاح البناء في GitHub Actions
android.accept_sdk_license = True

# (bool) Use --private data storage (True)
android.private_storage = True

# (list) The Android archs to build for
# تقليلها لـ arm64-v8a يسرع البناء، وإضافة armeabi-v7a تدعم الهواتف القديمة
android.archs = arm64-v8a, armeabi-v7a

# (bool) enables Android auto backup
android.allow_backup = True

# (str) Presplash of the application (اختياري)
# presplash.filename = %(source.dir)s/assets/images/presplash.png

# (str) Icon of the application (اختياري)
# icon.filename = %(source.dir)s/assets/images/icon.png

# (int) Log level (2 = debug) ليعطيك تفاصيل الأخطاء كاملة
log_level = 2

# (str) Android entry point
android.entrypoint = main.py

[buildozer]

# (int) Display warning if buildozer is run as root (0 = off, 1 = on)
warn_on_root = 1

# (str) Path to build artifact storage, default is current directory
bin_dir = ./bin