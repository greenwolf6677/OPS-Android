[app]

title = OPS
package.name = ops
package.domain = org.ops
version = 1.0.0

requirements = python3,kivy,kivymd

orientation = landscape
fullscreen = 0

android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE

icon.filename = assets/icon/logo.png
android.default_language = ar

android.ndk = 25b
android.sdk = 30
android.minapi = 21

source.dir = .
source.include_exts = py,png,jpg,kv,ttf,db,wav
source.exclude_exts = spec,pyc,pyo
source.exclude_patterns = __pycache__,docs

android.accept_sdk_license = True
bootstrap = sdl2

# منع بعض المكتبات التي تسبب مشاكل
android.add_src = 
android.gradle_dependencies = 