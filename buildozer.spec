[app]
title = Grade Architect
package.name = gradearchitect
package.domain = org.olumide
source.dir = .
source.include_exts = py,png,jpg,json
version = 0.1

# REQUIREMENTS (Crucial for FPDF)
requirements = python3,kivy==2.3.1,fpdf,pillow

# BRANDING
icon.filename = %(source.dir)s/icon.png
presplash.filename = %(source.dir)s/icon.png
android.presplash_color = #0f172a

# PERMISSIONS (For your PDF exports)
android.permissions = WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE, MANAGE_EXTERNAL_STORAGE

# ARCHITECTURE (Stick to one to speed up the build)
android.archs = arm64-v8a
