from pyexpat.errors import messages
from django.db import connection
from django.shortcuts import render, redirect

# Create your views here.

from django.views.generic import CreateView, TemplateView
from django.urls import reverse_lazy

from proyecto_BD.settings import MEDIA_ROOT
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
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
import os
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from datetime import date, datetime

class JugadorHomeView(View):
    def get(self, request):
        user_id = request.user.id

        with connection.cursor() as cursor:
            # Fetch player data with team details, including Esta_en_equipo
            cursor.execute("""
                SELECT j.Num_socio, j.DNI, j.Nombre, j.Apellido, j.Fecha_nacimiento, 
                    j.Telefono, j.Direccion_numero_Calle, j.URL_foto, j.mail, 
                    DATEDIFF(YEAR, j.Fecha_nacimiento, GETDATE()) AS edad,
                    CASE 
                        WHEN DATEDIFF(YEAR, j.Fecha_nacimiento, GETDATE()) BETWEEN 7 AND 13 THEN 'Niños'
                        WHEN DATEDIFF(YEAR, j.Fecha_nacimiento, GETDATE()) BETWEEN 14 AND 17 THEN 'Adolescentes'
                        WHEN DATEDIFF(YEAR, j.Fecha_nacimiento, GETDATE()) BETWEEN 18 AND 54 THEN 'Adultos'
                        WHEN DATEDIFF(YEAR, j.Fecha_nacimiento, GETDATE()) >= 55 THEN 'Adultos Mayores'
                        ELSE 'Categoría no definida'
                    END AS categoria,
                    e.Nombre AS nombre_equipo,
                    c.Nombre_categoria AS categoria_equipo,
                    d.nombre_division AS division_equipo,
                    j.Esta_en_equipo  -- Agregamos la columna Esta_en_equipo
                FROM Jugador j
                LEFT JOIN Equipo e ON j.Num_equipo = e.Num_equipo
                LEFT JOIN Categoria c ON e.ID_Categoria = c.ID_Categoria
                LEFT JOIN Division d ON e.ID_Division = d.ID_Division
                INNER JOIN org_futbol_customuser u ON j.user_id = u.id
                WHERE u.id = %s
            """, [user_id])

            jugador_data = cursor.fetchone()

        # Fetch available teams
        # Si se encontró el jugador, filtrar equipos por edad
        if jugador_data:
            edad_jugador = jugador_data[9]  # Edad calculada
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT E.Num_equipo, E.Nombre, C.Nombre_categoria AS Categoria, 
                        D.nombre_division AS Division,
                        C.Edad_minima, C.Edad_maxima
                    FROM Equipo E
                    JOIN Division D ON E.ID_Division = D.ID_Division
                    JOIN Categoria C ON E.ID_Categoria = C.ID_Categoria
                    WHERE %s BETWEEN C.Edad_minima AND C.Edad_maxima
                """, [edad_jugador])
                equipos = cursor.fetchall()

            if jugador_data:
                # Handle profile photo
                foto_path = jugador_data[7] if jugador_data[7] else None
                if foto_path and not os.path.exists(os.path.join(settings.MEDIA_ROOT, foto_path)):
                    foto_path = None

                context = {
                    'jugador': jugador_data,
                    'foto_url': f'{settings.MEDIA_URL}{foto_path}' if foto_path else None,
                    'edad': jugador_data[9],
                    'categoria': jugador_data[10],

                    'equipo_actual': {
                        'nombre': jugador_data[11] or 'Sin equipo',
                        'categoria': jugador_data[12] or 'N/A',
                        'division': jugador_data[13] or 'N/A'
                    },

                    'equipos': equipos,

                    # Incluir la información del estado 'Esta_en_equipo'
                    'esta_en_equipo': jugador_data[14]  
                }
            else:
                context = {
                    'mensaje_error': "No se encontraron datos del jugador."
                }
        else:
            # Si no se encuentra el jugador, establecer un contexto de error
            context = {
                'mensaje_error': "No se encontraron datos del jugador."
            }

        return render(request, 'jugador_home.html', context)

    def post(self, request):
        user_id = request.user.id
        
        # Retrieve form data
        nuevo_nombre = request.POST.get('nuevo_nombre')
        nuevo_apellido = request.POST.get('nuevo_apellido')
        nuevo_telefono = request.POST.get('nuevo_telefono')
        nueva_direccion = request.POST.get('nueva_direccion')
        nueva_foto = request.FILES.get('nueva_foto')
        nuevo_email = request.POST.get('nuevo_email')
        nueva_fecha_nacimiento = request.POST.get('nueva_fecha_nacimiento')
        equipo_seleccionado = request.POST.get('equipo_seleccionado')
        nuevo_dni = request.POST.get('nuevo_dni')

        try:
            with connection.cursor() as cursor:
                # Primero, recuperar el Num_socio correcto
                cursor.execute("""
                    SELECT Num_socio 
                    FROM Jugador 
                    WHERE user_id = %s
                """, [user_id])
                
                resultado = cursor.fetchone()
                if not resultado:
                    messages.error(request, 'Jugador no encontrado.')
                    return redirect('jugador_home')
                
                num_socio = resultado[0]  # Obtener el Num_socio real

                # Fetch current player data to use as fallback
                cursor.execute("""
                    SELECT Nombre, Apellido, Telefono, Direccion_numero_Calle, 
                        mail, Fecha_nacimiento, DNI, URL_foto, Num_equipo
                    FROM Jugador 
                    WHERE Num_socio = %s
                """, [num_socio])
                jugador_actual = cursor.fetchone()

                if not jugador_actual:
                    messages.error(request, 'Datos del jugador no encontrados.')
                    return redirect('jugador_home')

                # Use new values or fallback to existing values
                nombre = nuevo_nombre or jugador_actual[0]
                apellido = nuevo_apellido or jugador_actual[1]
                telefono = nuevo_telefono or jugador_actual[2]
                direccion = nueva_direccion or jugador_actual[3]
                email = nuevo_email or jugador_actual[4]
                
                # Validar y formatear fecha de nacimiento
                if nueva_fecha_nacimiento:
                    try:
                        # Convertir fecha al formato correcto si es necesario
                        fecha_nacimiento = datetime.strptime(nueva_fecha_nacimiento, '%Y-%m-%d').date()
                    except ValueError:
                        fecha_nacimiento = jugador_actual[5]
                else:
                    fecha_nacimiento = jugador_actual[5]
                
                dni = nuevo_dni or jugador_actual[6]
                
                # Handle profile photo
                foto_url = jugador_actual[7]
                if nueva_foto:
                    try:
                        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'fotos_jugadores'))
                        foto_path = fs.save(f'{num_socio}.jpg', nueva_foto)
                        foto_url = f'fotos_jugadores/{os.path.basename(foto_path)}'
                    except Exception as e:
                        messages.warning(request, f'Error al subir la foto: {e}')

                # Determine team
                num_equipo = equipo_seleccionado or jugador_actual[8]

                # Prepare update query
                update_query = """
                    UPDATE Jugador 
                    SET Nombre = %s, 
                        Apellido = %s, 
                        Telefono = %s, 
                        Direccion_numero_Calle = %s, 
                        mail = %s, 
                        Fecha_nacimiento = %s,
                        DNI = %s,
                        URL_foto = %s,
                        Num_equipo = %s
                    WHERE Num_socio = %s
                """
                
                # Execute update
                cursor.execute(update_query, [
                    nombre, apellido, telefono, direccion, 
                    email, fecha_nacimiento, dni, foto_url, 
                    num_equipo, num_socio
                ])

                # If a new team was selected, fetch its details
                if equipo_seleccionado:
                    cursor.execute("""
                        SELECT E.Nombre, C.Nombre_categoria, D.nombre_division
                        FROM Equipo E
                        JOIN Categoria C ON E.ID_Categoria = C.ID_Categoria
                        JOIN Division D ON E.ID_Division = D.ID_Division
                        WHERE E.Num_equipo = %s
                    """, [num_equipo])
                    equipo_detalles = cursor.fetchone()

                    if equipo_detalles:
                        messages.success(request, 
                            f'Datos actualizados. Inscrito en el equipo: {equipo_detalles[0]} - {equipo_detalles[1]} - {equipo_detalles[2]}'
                        )
                    else:
                        messages.success(request, 'Datos actualizados exitosamente.')
                else:
                    messages.success(request, 'Datos actualizados exitosamente.')

        except Exception as e:
            messages.error(request, f'Error al actualizar los datos: {str(e)}')
            # Opcional: loggear el error completo
            import traceback
            print(traceback.format_exc())

        return redirect('jugador_home')

# Vista para Organizador
class OrganizadorHomeView(View):
    def get(self, request):
        user_id = request.user.id

        # Obtener los datos del organizador desde la base de datos
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT o.Nombre, o.Apellido, o.Telefono, o.mail, u.email AS user_email
                FROM Organizador o
                INNER JOIN org_futbol_customuser u ON o.user_id = u.id
                WHERE u.id = %s
            """, [user_id])

            organizador_data = cursor.fetchone()

            # Obtener torneos creados por el organizador
            cursor.execute("""
                SELECT ID_Torneo, Nombre, Periodo_inicio, Periodo_fin
                FROM Torneo
                WHERE ID_Organizador = (
                    SELECT ID_Organizador FROM Organizador WHERE user_id = %s
                )
            """, [user_id])
            torneos = cursor.fetchall()

            # Obtener las categorías y divisiones para el formulario
            cursor.execute("SELECT ID_Categoria, Nombre_categoria FROM Categoria")
            categorias = cursor.fetchall()

            cursor.execute("SELECT ID_Division, nombre_division FROM Division")
            divisiones = cursor.fetchall()

        context = {
            'organizador': organizador_data,
            'torneos': torneos,
            'categorias': categorias,
            'divisiones': divisiones,
        }

        return render(request, 'organizador_home.html', context)

    def post(self, request):
        user_id = request.user.id

        # Datos de edición del perfil
        if 'editar_perfil' in request.POST:
            nuevo_nombre = request.POST.get('nuevo_nombre')
            nuevo_apellido = request.POST.get('nuevo_apellido')
            nuevo_telefono = request.POST.get('nuevo_telefono')
            nuevo_email = request.POST.get('nuevo_email')

            try:
                if not (nuevo_nombre and nuevo_apellido and nuevo_telefono and nuevo_email):
                    messages.error(request, 'Todos los campos son obligatorios.')
                    return redirect('organizador_home')

                with connection.cursor() as cursor:
                    cursor.execute("""
                        UPDATE Organizador
                        SET Nombre = %s, Apellido = %s, Telefono = %s, mail = %s
                        WHERE user_id = %s
                    """, [nuevo_nombre, nuevo_apellido, nuevo_telefono, nuevo_email, user_id])

                messages.success(request, 'Datos actualizados correctamente.')
                return redirect('organizador_home')
            except Exception as e:
                messages.error(request, f'Error al actualizar los datos: {e}')
                return redirect('organizador_home')

        # Datos para crear un torneo
        elif 'crear_torneo' in request.POST:
            nombre_torneo = request.POST.get('nombre_torneo')
            periodo_inicio = request.POST.get('periodo_inicio')
            periodo_fin = request.POST.get('periodo_fin')
            id_categoria = request.POST.get('id_categoria')
            id_division = request.POST.get('id_division')

            try:
                if not (nombre_torneo and periodo_inicio and periodo_fin and id_categoria and id_division):
                    messages.error(request, 'Todos los campos del torneo son obligatorios.')
                    return redirect('organizador_home')

                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO Torneo (ID_Organizador, Nombre, Periodo_inicio, Periodo_fin, Estado_torneo)
                        VALUES (
                            (SELECT ID_Organizador FROM Organizador WHERE user_id = %s),
                            %s, %s, %s, 'En preparación'
                        )
                    """, [user_id, nombre_torneo, periodo_inicio, periodo_fin])

                messages.success(request, 'Torneo creado exitosamente.')
                return redirect('organizador_home')
            except Exception as e:
                messages.error(request, f'Error al crear el torneo: {e}')
                return redirect('organizador_home')


# Vista para Representante
from django.shortcuts import render, redirect
from django.db import connection
from django.views import View

from django.db import connection, transaction
from django.shortcuts import render, redirect
from django.views import View
from django.shortcuts import render, redirect
from django.db import transaction, connection
from django.views import View
class RepresentanteHomeView(View):
    def get(self, request):
        user_id = request.user.id

        # Obtener datos del representante
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT u.username, u.email, o.id_representante, o.nombre
                FROM org_futbol_customuser u
                INNER JOIN Representante o ON u.id = o.user_id
                WHERE u.id = %s
            """, [user_id])

            representante_data = cursor.fetchone()

        if representante_data:
            context = {
                'username': representante_data[0],
                'email': representante_data[1],
                'id_representante': representante_data[2],
                'nombre': representante_data[3],  # Agregar el nombre al contexto
            }
            id_representante = representante_data[2]
        else:
            context = {
                'mensaje_error': "No se encontraron datos del organizador."
            }
            return render(request, 'representante_home.html', context)

        # Obtener todas las divisiones y categorías
        with connection.cursor() as cursor:
            cursor.execute("SELECT ID_Division, nombre_division FROM Division")
            divisiones = cursor.fetchall()

            cursor.execute("SELECT ID_Categoria, Nombre_categoria FROM Categoria")
            categorias = cursor.fetchall()

            # Obtener equipo asociado al representante
            cursor.execute("""
                SELECT e.Num_equipo, e.Nombre, d.nombre_division, c.Nombre_categoria, e.ID_Division, e.ID_Categoria
                FROM Equipo e
                INNER JOIN Division d ON e.ID_Division = d.ID_Division
                INNER JOIN Categoria c ON e.ID_Categoria = c.ID_Categoria
                WHERE e.id_representante = %s
            """, [id_representante])

            equipo_data = cursor.fetchone()

            if equipo_data:
                # Obtener los jugadores asociados al equipo
                cursor.execute("""
                    SELECT j.Num_socio, j.Nombre, j.Apellido
                    FROM Jugador j
                    WHERE j.Num_equipo = %s
                """, [equipo_data[0]])
                jugadores = cursor.fetchall()
                context['jugadores'] = jugadores

        context.update({
            'divisiones': divisiones,
            'categorias': categorias,
            'equipo': equipo_data,  # Puede ser None si no hay equipo registrado
        })

        return render(request, 'representante_home.html', context)

    def post(self, request):
    # Cambiar el estado de un jugador
        if 'cambiar_estado' in request.POST:
            num_jugador = request.POST.get('num_jugador')
            
            with transaction.atomic(), connection.cursor() as cursor:
                # Cambia el estado basado en el estado actual
                cursor.execute("""
                    UPDATE Jugador
                    SET Esta_en_equipo = CASE 
                        WHEN Esta_en_equipo = 1 THEN 0 
                        ELSE 1 
                    END
                    WHERE Num_socio = %s
                """, [num_jugador])

            return redirect('representante_home')

        # Verificar si el representante ya tiene un equipo asociado
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT Num_equipo
                FROM Equipo
                WHERE id_representante = (
                    SELECT id_representante
                    FROM Representante
                    WHERE user_id = %s
                )
            """, [request.user.id])

            equipo_existente = cursor.fetchone()

        if equipo_existente:
            # Si ya existe un equipo, actualizar el equipo
            equipo_id = equipo_existente[0]
            
            # Obtener los datos del formulario
            nombre_equipo = request.POST.get('nombre_equipo')
            id_division = request.POST.get('id_division')
            id_categoria = request.POST.get('id_categoria')

            # Verificar si todos los campos requeridos están presentes
            if not nombre_equipo or not id_division or not id_categoria:
                return render(request, 'representante_home.html', {
                    'mensaje_error': 'Todos los campos son obligatorios.',
                })

            # Actualizar el equipo en la base de datos
            with transaction.atomic(), connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE Equipo 
                    SET Nombre = %s, ID_Division = %s, ID_Categoria = %s
                    WHERE Num_equipo = %s
                """, [nombre_equipo, id_division, id_categoria, equipo_id])

            return redirect('representante_home')
         # Cambiar el nombre del representante
        if 'cambiar_nombre' in request.POST:
            nuevo_nombre = request.POST.get('nuevo_nombre')
            
            if not nuevo_nombre:
                return render(request, 'representante_home.html', {
                    'mensaje_error': 'El nombre no puede estar vacío.',
                })
            
            with transaction.atomic(), connection.cursor() as cursor:
                # Actualizar el nombre del representante
                cursor.execute("""
                    UPDATE Representante
                    SET nombre = %s
                    WHERE user_id = %s
                """, [nuevo_nombre, request.user.id])
            
            return redirect('representante_home')

        # Si no hay equipo, registrar uno nuevo
        nombre_equipo = request.POST.get('nombre_equipo')
        id_division = request.POST.get('id_division')
        id_categoria = request.POST.get('id_categoria')

        # Verificar si todos los campos requeridos están presentes
        if not nombre_equipo or not id_division or not id_categoria:
            return render(request, 'representante_home.html', {
                'mensaje_error': 'Todos los campos son obligatorios.',
            })

        # Crear el equipo en la base de datos
        with transaction.atomic(), connection.cursor() as cursor:
            cursor.execute("""
                SELECT id_representante 
                FROM Representante 
                WHERE user_id = %s
            """, [request.user.id])

            representante_result = cursor.fetchone()
            if not representante_result:
                return render(request, 'representante_home.html', {
                    'mensaje_error': 'No se encontró el representante asociado a este usuario.',
                })

            id_representante = representante_result[0]

            # Insertar el equipo
            cursor.execute("""
                INSERT INTO Equipo (Nombre, ID_Division, ID_Categoria, id_representante)
                VALUES (%s, %s, %s, %s)
            """, [nombre_equipo, id_division, id_categoria, id_representante])

        return redirect('representante_home')


# Vista para Técnico
class TecnicoHomeView(View):
    def get(self, request):
        user_id = request.user.id

        # Obtener los datos del director técnico desde la base de datos
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT t.ID_Tecnico, t.Nombre, t.Apellido, t.Telefono, u.email AS user_email
                FROM Director_tecnico t
                INNER JOIN org_futbol_customuser u ON t.user_id = u.id
                WHERE u.id = %s
            """, [user_id])

            tecnico_data = cursor.fetchone()

        # Obtener los equipos disponibles con su categoría y división
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT E.Num_equipo, E.Nombre, C.Nombre_categoria AS Categoria, D.nombre_division AS Division
                FROM Equipo E
                JOIN Division D ON E.ID_Division = D.ID_Division
                JOIN Categoria C ON E.ID_Categoria = C.ID_Categoria
            """)
            equipos = cursor.fetchall()

        # Obtener los equipos del director técnico
        equipos_tecnico = []
        if tecnico_data:
            tecnico_id = tecnico_data[0]  # ID_Tecnico
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT E.Num_equipo, E.Nombre, C.Nombre_categoria AS Categoria, D.nombre_division AS Division
                    FROM Equipo E
                    JOIN Division D ON E.ID_Division = D.ID_Division
                    JOIN Categoria C ON E.ID_Categoria = C.ID_Categoria
                    WHERE E.ID_Tecnico = %s
                """, [tecnico_id])
                equipos_tecnico = cursor.fetchall()

        if tecnico_data:
            context = {
                'tecnico': tecnico_data,
                'equipos': equipos,
                'equipos_tecnico': equipos_tecnico,
            }
        else:
            context = {
                'mensaje_error': "No se encontraron datos del director técnico."
            }

        return render(request, 'tecnico_home.html', context)
    def post(self, request):
        user_id = request.user.id
        nuevo_nombre = request.POST.get('nuevo_nombre')
        nuevo_apellido = request.POST.get('nuevo_apellido')
        nuevo_telefono = request.POST.get('nuevo_telefono')
        nuevo_email = request.POST.get('nuevo_email')
        equipo_seleccionado = request.POST.get('equipo_seleccionado')

        try:
            # Verificar que todos los campos estén presentes
            if not (nuevo_nombre and nuevo_apellido and nuevo_telefono and nuevo_email and equipo_seleccionado):
                messages.error(request, 'Todos los campos son obligatorios.')
                return redirect('tecnico_home')

            # Actualizar los datos del técnico
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE Director_tecnico
                    SET Nombre = %s, Apellido = %s, Telefono = %s
                    WHERE user_id = %s
                """, [nuevo_nombre, nuevo_apellido, nuevo_telefono, user_id])

            # Actualizar el equipo asignado al técnico
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE Equipo
                    SET ID_Tecnico = (
                        SELECT ID_Tecnico
                        FROM Director_tecnico
                        WHERE user_id = %s
                    )
                    WHERE Num_equipo = %s
                """, [user_id, equipo_seleccionado])

            # Confirmar éxito
            messages.success(request, 'Datos actualizados correctamente.')
            return redirect('tecnico_home')

        except Exception as e:
            messages.error(request, f'Error al actualizar los datos: {e}')
            return redirect('tecnico_home')



from django.views.generic import View
from django.shortcuts import render

class EditarEquipoView(View):
    def get(self, request):
        # Lógica para mostrar el formulario de edición
        return render(request, 'editar_equipo.html')

