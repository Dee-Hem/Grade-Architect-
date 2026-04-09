[app]
title = Grade Architect
package.name = gradearchitect
package.domain = org.olumide
source.dir = .
source.include_exts = py,png,jpg,json
version = 0.1
orientation = portrait

# REQUIREMENTS 
requirements = python3,kivy==2.3.1,fpdf,pillow

# BRANDING
icon.filename = %(source.dir)s/icon.png
presplash.filename = %(source.dir)s/icon.png
android.presplash_color = #0f172a

# PERMISSIONS 
android.permissions = WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE, INTERNET

# STABILITY SETTINGS
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
