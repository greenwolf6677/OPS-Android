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

# (list) List of directory to include (هنا التعديل الجذري بناءً على صورك)
source.include_dirs = assets, database, kv, screens, security, utils, widgets

# (list) List of exclusions
source.exclude_dirs = tests, bin, venv, .git, .github

# (list) Application requirements
# أضفت لك fpdf2 للـ PDF و six/sh لضمان التوافق
requirements = python3, kivy==2.3.0, kivymd==1.2.0, pillow, arabic-reshaper, python-bidi, six, requests, sqlite3, fpdf2

# (str) Custom source folders for requirements
# (list) Garden requirements
# (str) Presplash of the application
# (str) Icon of the application
# (str) Supported orientations
orientation = portrait

# (list) Permissions
android.permissions = INTERNET, CAMERA, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (str) Android NDK version to use
android.ndk = 25b

# (bool) Use --private data storage (True) or --dir public storage (False)
android.private_storage = True

# (list) The Android archs to build for (تقليلها لسرعة البناء ومنع الأخطاء)
android.archs = arm64-v8a

# (bool) enables Android auto backup
android.allow_backup = True

# (list) List of Java files to add to the android project
# (list) Gradle dependencies
# android.gradle_dependencies = 

# (list) add extra settings to the main activity
# (list) List of service to declare

[buildozer]
# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = off, 1 = on)
warn_on_root = 1