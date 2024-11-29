from django import views
from django.urls import path
from .views import RegisterView, HomeView, CustomLoginView, JugadorHomeView, OrganizadorHomeView, RepresentanteHomeView, TecnicoHomeView
from django.contrib.auth.views import LoginView, LogoutView
from django.conf import settings
from django.conf.urls.static import static
from . import views  # Importa las vistas desde el archivo views.py

urlpatterns = [
    path('', HomeView.as_view(), name='home'),  # Ruta vacía que lleva a la página principal
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),  # Cambia a CustomLoginView
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
     # Rutas para los distintos tipos de usuario
    # Rutas para los distintos tipos de usuario
    path('jugador/', JugadorHomeView.as_view(), name='jugador_home'),  # Corrige con la vista real
    path('organizador/', OrganizadorHomeView.as_view(), name='organizador_home'),  # Corrige con la vista real
    path('representante/', RepresentanteHomeView.as_view(), name='representante_home'),  # Corrige con la vista real
    path('tecnico/', TecnicoHomeView.as_view(), name='tecnico_home'),  # Corrige con la vista real
    path('eliminar_equipo/', RepresentanteHomeView.as_view(), name='eliminar_equipo'),
    path('editar_equipo/', views.EditarEquipoView.as_view(), name='editar_equipo'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)