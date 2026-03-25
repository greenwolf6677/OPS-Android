[app]

title = OPS
package.name = ops
package.domain = org.ops
version = 1.0.0

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