from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.

class CustomUser(AbstractUser):
    TIPO_USUARIO_CHOICES = [
        ('jugador', 'Jugador'),
        ('organizador', 'Organizador'),
        ('representante', 'Representante'),
        ('tecnico', 'Técnico'),
    ]
    tipo_usuario = models.CharField(max_length=20, choices=TIPO_USUARIO_CHOICES, default='jugador')

    def __str__(self):
        return f"{self.username} ({self.tipo_usuario})"
