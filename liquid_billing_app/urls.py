# liquid_billing_app/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView # Importa RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('app/', include('invoicing.urls')),
    path('', RedirectView.as_view(url='/app/', permanent=True)), # ¡Añade esta línea!
]
