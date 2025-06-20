from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')), # Django's auth URLs
    path('app/', include('invoicing.urls')), # App specific URLs
]
