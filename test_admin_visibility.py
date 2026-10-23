"""
Test script to show EXACTLY what's in the admin panel
Run: python test_admin_visibility.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kaaf.settings')
django.setup()

from django.contrib import admin
from django.apps import apps

print("\n" + "=" * 70)
print(" DJANGO ADMIN PANEL - ALL REGISTERED MODELS")
print("=" * 70 + "\n")

# Group models by app
app_models = {}
for model, model_admin in admin.site._registry.items():
    app_label = model._meta.app_label
    app_config = apps.get_app_config(app_label)
    verbose_name = app_config.verbose_name
    
    if verbose_name not in app_models:
        app_models[verbose_name] = []
    
    model_name = model._meta.verbose_name_plural.title()
    app_models[verbose_name].append(model_name)

# Print in admin panel format
for app_name in sorted(app_models.keys()):
    print(f"📁 {app_name.upper()}")
    for model_name in sorted(app_models[app_name]):
        print(f"   • {model_name}")
    print()

print("=" * 70)
print(f"Total Apps: {len(app_models)}")
print(f"Total Models: {sum(len(models) for models in app_models.values())}")
print("=" * 70)

# Check specifically for exams
if 'Examination System' in app_models:
    print("\n✅ EXAMINATION SYSTEM IS REGISTERED!")
    print(f"   Models: {', '.join(app_models['Examination System'])}")
else:
    print("\n❌ EXAMINATION SYSTEM NOT FOUND!")

print("\n" + "=" * 70)
print("This is EXACTLY what you should see in /admin/")
print("=" * 70 + "\n")
