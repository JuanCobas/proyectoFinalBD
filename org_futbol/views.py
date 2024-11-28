from django.shortcuts import render, redirect

# Create your views here.

from django.views.generic import CreateView, TemplateView
from django.urls import reverse_lazy
from .forms import CustomUserCreationForm
from django.contrib.auth.views import LoginView
from django.views import View

# Vista para la página principal (home)
class HomeView(TemplateView):
    template_name = 'home.html'

class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('login')
    


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'

    def form_valid(self, form):
        # Llamamos al método `form_valid` de LoginView para que inicie sesión
        response = super().form_valid(form)

        # Redirigimos según el tipo de usuario
        user = self.request.user
        if user.tipo_usuario == 'jugador':
            return redirect('jugador_home')  # Asegúrate de tener esta ruta en tus urls
        elif user.tipo_usuario == 'organizador':
            return redirect('organizador_home')  # Asegúrate de tener esta ruta en tus urls
        elif user.tipo_usuario == 'representante':
            return redirect('representante_home')  # Asegúrate de tener esta ruta en tus urls
        elif user.tipo_usuario == 'tecnico':
            return redirect('tecnico_home')  # Asegúrate de tener esta ruta en tus urls

        # Si no coincide con ninguno de los casos anteriores, redirigimos a una página por defecto
        return redirect('home')  # O cualquier página predeterminada que quieras
    
# Vista para Jugador
class JugadorHomeView(View):
    def get(self, request):
        return render(request, 'jugador_home.html')  # Cambia el nombre del template según corresponda

# Vista para Organizador
class OrganizadorHomeView(View):
    def get(self, request):
        return render(request, 'organizador_home.html')  # Cambia el nombre del template según corresponda

# Vista para Representante
class RepresentanteHomeView(View):
    def get(self, request):
        return render(request, 'representante_home.html')  # Cambia el nombre del template según corresponda

# Vista para Técnico
class TecnicoHomeView(View):
    def get(self, request):
        return render(request, 'tecnico_home.html')  # Cambia el nombre del template según corresponda