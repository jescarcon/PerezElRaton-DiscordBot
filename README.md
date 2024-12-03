# 🐭PerezElRaton-DiscordBot🐭
Bot de Discord creado para gestionar una comunidad de una Asociación de Rol, es capaz de generar salas temporales y privadas para los jugadores , integré también un sistema de valoraciones para evaluar a los directores de partidas. 

---

## Características principales
- **Gestión de partidas**: Crear canales de texto privados para partidas con permisos personalizados.
- **Registro de usuarios**: Los usuarios pueden registrarse en una base de datos PostgreSQL para gestionar un sistema de valoración de los organizadores de partida.
- **Sistema de votación**: Vota a otros usuarios con una calificación del 1 al 10 y consulta las puntuaciones de los usuarios.
- **Moderación de sugerencias**: Asegura que los mensajes en el canal de sugerencias sigan una estructura definida.
- **Comandos de limpieza**: Permite limpiar canales de texto donde se usen comandos de otros bots, ya que los de este bot, no se muestra al público al usarse, puede borrar todo el contenido o borrar X líneas.
- **Comandos informativos**: Accede a detalles sobre el bot y las reglas de uso.

---

## Tecnologías utilizadas
- **Python 3.9+**
- **discord.py 2.x**
- **PostgreSQL** para la gestión de la base de datos.
- **psycopg2** como cliente de base de datos.

---
## Comandos disponibles

🎲 Gestión de partidas
- /partida: Crea una nueva partida privada.
- /añadir @usuario: Añade participantes a una partida.
- /eliminar @usuario: Elimina participantes de una partida.
- /tiempo: Consulta cuánto tiempo queda antes de que la partida expire.
- /ampliar: Extiende el tiempo de la partida.
- /cerrar: Cierra la partida manualmente.

🌟 Sistema de votación
- /registro: Registra tu usuario en la base de datos.
- /voto 1-10 @usuario: Vota a un usuario.
- /puntos @usuario: Consulta la puntuación media de un usuario.
