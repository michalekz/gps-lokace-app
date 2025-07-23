[app]

# Název aplikace
title = GPS Lokace

# Balíček
package.name = gpslokace
package.domain = org.test

# Verze
version = 1.0

# Zdrojové soubory
source.dir = .
source.include_exts = py,png,jpg,kv,atlas

# Hlavní soubor
source.main = main_kivy.py

# Požadavky
requirements = python3,kivy,requests,urllib3,certifi

# Ikona (volitelné)
#icon.filename = %(source.dir)s/icon.png

# Orientace
orientation = portrait

# Oprávnění
android.permissions = INTERNET,ACCESS_NETWORK_STATE

# Intent filtry pro sdílení
android.add_activities = org.test.gpslokace.ShareActivity

# Gradle
android.gradle_dependencies = androidx.core:core:1.6.0

# Android manifest template
android.manifest_template = ./android_manifest.tmpl.xml

# APK arch
android.archs = arm64-v8a, armeabi-v7a

[buildozer]

# Složky
bin_dir = ./bin
build_dir = ./.buildozer

# Log level
log_level = 2

# Avoid error with gradle
android.accept_sdk_license = True