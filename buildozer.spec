[app]

# (str) Title of your application
title = OPS

# (str) Package name
package.name = ops
package.domain = org.ops

# (str) Version of your application
version = 1.0.0

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include
source.include_exts = py,png,jpg,kv,ttf,db

# (list) List of directory to include
source.include_dirs = assets, database, kv, screens, security, utils, widgets

# (list) List of exclusions
source.exclude_dirs = tests, bin, venv, .git, .github, __pycache__

# (list) Application requirements
requirements = python3,kivy,kivymd,pillow,arabic-reshaper,python-bidi,requests,sqlite3,fpdf2

# (str) Supported orientations
orientation = landscape

# (list) Permissions
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE

# (int) Target Android API
android.api = 30

# (int) Minimum API
android.minapi = 21

# (str) Android NDK version
android.ndk = 25b

# (bool) Use private data storage
android.private_storage = True

# (list) Android archs to build for
android.archs = arm64-v8a

# (bool) Enable auto backup
android.allow_backup = True

# (bool) Accept SDK license (مهم جداً)
android.accept_sdk_license = True

# (str) Bootstrap
bootstrap = sdl2

[buildozer]
# (int) Log level
log_level = 2

# (int) Display warning if buildozer is run as root
warn_on_root = 1