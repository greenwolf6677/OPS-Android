[app]

# (str) Title of your application
title = OPS

# (str) Package name
package.name = ops

# (str) Package domain (needed for android packaging)
package.domain = org.ops

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,ttf,db

# (list) List of directory to include
# تم إضافة كافة المجلدات لضمان عدم نسيان أي ملف برمجي أو تصميم
source.include_dirs = assets, kv, screens, database, security, utils, widgets

# (str) Application versioning
version = 1.0.0

# (list) Application requirements
# تمت إضافة hostpython3 و sqlite3 و kivymd لضمان عمل النظام بالكامل
requirements = python3, hostpython3, kivy==2.2.1, kivymd, pillow, arabic-reshaper, python-bidi, sqlite3, cryptography, requests, urllib3, charset-normalizer, idna

# (str) Supported orientations
orientation = landscape

# (list) Permissions
# أندرويد 11+ يكتفي بـ INTERNET إذا كنت تخزن البيانات في user_data_dir
android.permissions = INTERNET

# (int) Target Android API, should be as high as possible.
android.api = 31

# (int) Minimum API your APK will support.
android.minapi = 21

# (int) Android SDK version to use
android.sdk = 31

# (str) Android NDK version to use
android.ndk = 25b

# (bool) Use --private data storage (True) or --dir public storage (False)
android.private_storage = True

# (str) Android NDK directory (if empty, it will be automatically downloaded)
android.ndk_path = 

# (str) Android SDK directory (if empty, it will be automatically downloaded)
android.sdk_path = 

# (bool) If True, then skip trying to update the Android sdk
android.skip_update = False

# (bool) If True, then automatically accept SDK license
android.accept_sdk_license = True

# (list) Android architectures to build for
android.archs = armeabi-v7a, arm64-v8a

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
# android.arch = arm64-v8a

# (str) Bootstrap to use for android
bootstrap = sdl2

# (str) Path to a custom whitelist file
# android.whitelist =

# ==================== Buildozer Settings ====================

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = no, 1 = yes)
warn_on_root = 1

# (str) Path to build artifact storage, cache, and prefix
# build_dir = ./.buildozer

# (str) Path to bin directory where the apk will be stored
# bin_dir = ./bin