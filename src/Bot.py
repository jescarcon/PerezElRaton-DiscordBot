#region -------------------- Imports --------------------

import asyncio
import discord
from discord.ext import commands
import psycopg2
from psycopg2 import sql

#endregion

#region -------------------- Configs --------------------

# Configuración del bot
TOKEN = 'TOKEN_DISCORD'
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True 

bot = commands.Bot(command_prefix='/', intents=intents)

# Configuración de la base de datos
conn = psycopg2.connect(
    dbname="DATABASE_NAME",  # Nombre de tu base de datos
    user="DATABASE_USER",     # Usuario de PostgreSQL
    password="DATABASE_PASSWORD",  # Contraseña
    host="HOST_NAME",    # Host
    port="DATABASE_PORT"          # Puerto
)

#endregion

#region -------------------- Lógica --------------------

cursor = conn.cursor()

#region ----------Inicio----------
# Evento de inicio del bot
@bot.event
async def on_ready():
    try:
        await asyncio.sleep(3)  # Espera 3 segundos antes de sincronizar
        await bot.tree.sync()  # Sincroniza los comandos slash
        print(f"Bot conectado como {bot.user} y comandos slash sincronizados.")
    except Exception as e:
        print(f"Error al sincronizar comandos slash: {e}")

#endregion

#region ----------Registro----------
# Comando para registrar al usuario
@bot.tree.command(name="registro", description="Registra tu usuario en la base de datos")
async def register(interaction: discord.Interaction):
    user_id = interaction.user.id
    username = interaction.user.name
    
    try:
        # Verificar si el usuario ya está registrado
        cursor.execute("SELECT * FROM users WHERE discord_id = %s", (user_id,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            # Si el usuario ya está registrado
            await interaction.response.send_message(f"Ya estás registrado, {username}.", ephemeral=True)
        else:
            # Registrar al usuario si no existe
            cursor.execute("INSERT INTO users (discord_id, username) VALUES (%s, %s)", (user_id, username))
            conn.commit()
            await interaction.response.send_message(f"Usuario {username} registrado con éxito.", ephemeral=True)
    except Exception as e:
        print(f"Error: {e}")
        await interaction.response.send_message("Hubo un error al intentar registrar tu usuario.", ephemeral=True)
#endregion

#region ----------Información----------
@bot.tree.command(name="perez-info", description="Obtén información sobre Pérez el Ratón y sus comandos.")
async def perez_info(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🐭 Bienvenid@ a Pérez el Ratón 🐭",
        description=( 
            "¡Hola! Soy **Pérez el Ratón**, tu bot asistente en Ratones en las Gavias. 🏰\n"
            "Estoy aquí para ayudarte a gestionar todo con facilidad y mantener la comunidad organizada. 📚\n\n"
            "Aquí tienes una lista de mis comandos principales para empezar:"
        ),
        color=discord.Color.purple()
    )
    embed.add_field(
        name="🔹 **/partida**",
        value="Crea una nueva partida privada en la categoría de partidas. Incluye opciones para añadir, eliminar participantes y más. 🎲",
        inline=False
    )
    embed.add_field(
        name="🔹 **/añadir** y **/eliminar**",
        value="Añade o elimina participantes de tu partida privada. 👥",
        inline=False
    )
    embed.add_field(
        name="🔹 **/tiempo**",
        value="Consulta cuánto tiempo queda para que tu partida expire. ⏳",
        inline=False
    )
    embed.add_field(
        name="🔹 **/ampliar**",
        value="Amplía el tiempo de tu partida privada en 24 horas. ⏰",
        inline=False
    )
    embed.add_field(
        name="🔹 **/cerrar**",
        value="Cierra manualmente una partida que ya haya cumplido su propósito. ✅",
        inline=False
    )
    embed.add_field(
        name="🔹 **/registro**",
        value=(
            "Regístrate en el sistema de votaciones para Másters.\n"
        ),
        inline=False
    )
    embed.add_field(
        name="🔹 **/voto**",
        value=(
            "Vota a un usuario con una puntuación del 1 al 10. 🌟\n"
            "Ejemplo: `/voto 8 @Usuario` para otorgar una calificación de 8 a un miembro."
        ),
        inline=False
    )
    embed.add_field(
        name="🔹 **/puntos**",
        value=(
            "Consulta la puntuación promedio de cualquier usuario o la tuya propia. 📊\n"
            "Ejemplo: `/puntos @Usuario` para ver su puntuación media."
        ),
        inline=False
    )
    embed.add_field(
        name="🔹 **/perez-info**",
        value="¡Este mismo comando! Úsalo para conocer más sobre lo que puedo hacer. 💡",
        inline=False
    )
    embed.set_footer(
        text="¡Espero que disfrutes de tus aventuras aquí! Si necesitas ayuda, no dudes en pedírmela. 🐾"
    )

    # Enviar mensaje efímero (visible solo para el usuario)
    await interaction.response.send_message(embed=embed, ephemeral=True)

#endregion

#region ----------Control de Sugerencias----------
#Eliminará los mensajes que no sigan la plantilla
@bot.event
async def on_message(message):
    # ID del canal "📝sugerencias📌"
    specific_channel_name = "📝sugerencias📌"
    guild = message.guild
    specific_channel = discord.utils.get(guild.text_channels, name=specific_channel_name)

    if not specific_channel:
        print(f"El canal '{specific_channel_name}' no existe. Verifica el nombre.")
        return

    if message.channel.id == specific_channel.id and not message.author.bot:
        # Estructura esperada
        expected_structure = ["**Tema**:", "**Descripción**:"]

        # Comprobar si el mensaje contiene la estructura esperada
        if not all(keyword in message.content for keyword in expected_structure):
            # Eliminar el mensaje que no cumpla con la estructura
            await message.delete()
            # Enviar un mensaje de advertencia
            warning_msg = await message.channel.send(
                f"{message.author.mention}, tu mensaje no cumple con la estructura requerida:\n"
                "```\n**Tema**: [Describe el tema]\n**Descripción**: [Añade tu descripción]\n```"
            )
            # Opcional: Eliminar el mensaje de advertencia después de un tiempo
            await asyncio.sleep(10)
            await warning_msg.delete()

    # Asegurarse de que los comandos del bot sigan funcionando
    await bot.process_commands(message)

#endregion

#region ----------Control de Partidas----------

import random
from datetime import datetime, timedelta
import asyncio

partidas = {}  # Diccionario para almacenar información de las partidas

@bot.tree.command(name="partida", description="Crea una nueva partida con canal de texto")
async def partida(interaction: discord.Interaction):
    guild = interaction.guild
    creator = interaction.user
    
    # Generar un ID único para la partida
    partida_id = f"partida-{random.randint(100000, 999999)}"
    
    # Obtener o crear la categoría "Partidas"
    partida_category = discord.utils.get(guild.categories, name="Partidas")
    if not partida_category:
        partida_category = await guild.create_category("Partidas")
    
    # Crear permisos para el canal
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),  # Ocultar para todos
        creator: discord.PermissionOverwrite(read_messages=True, send_messages=True)  # Permitir al creador
    }
    
    # Crear el canal de texto
    text_channel = await partida_category.create_text_channel(f"{partida_id}", overwrites=overwrites)
    
    # Guardar información de la partida
    expiration_time = datetime.now() + timedelta(minutes=10)
    partidas[text_channel.id] = {
        "creator": creator.id,
        "participants": [creator.id],
        "expiration_time": expiration_time,
        "category": partida_category,
        "channel": text_channel
    }
    
    # Mensaje privado al creador
    private_message = (
        f"**¡Partida creada con éxito!** 🎲\n\n"
        f"🔹 Canal de texto: {text_channel.mention}\n"
        f"🔹 Duración inicial: 10 minutos\n\n"
        f"¡Buena suerte y diviértanse! 🎲"
    )
    await interaction.response.send_message(private_message, ephemeral=True)
    
    # Mensaje público en el canal creado
    channel_message = (
        f"**¡Bienvenidos al canal de partida {partida_id}!** 🎮\n\n"
        f"🔸 El creador de la partida es: {creator.mention}\n\n"
        f"**Comandos disponibles para los participantes:**\n"
        f"🙋‍♂️ `/añadir @usuario` - Añade participantes a la partida.\n"
        f"❌ `/eliminar @usuario` - Elimina participantes de la partida.\n"
        f"⏳ `/tiempo` - Consulta el tiempo restante de la partida.\n"
        f"🔄 `/ampliar` - Amplía la duración de la partida en 24 horas.\n"
        f"✅ `/cerrar` - Cierra manualmente la partida.\n\n"
        f"Cualquier problema contacta con dirección o nuestros moderadores, ¡estarán a tu servicio!\n\n¡Buena suerte y diviértanse! 🎲"
    )
    await text_channel.send(channel_message)
    
    # Avisar y eliminar el canal automáticamente
    asyncio.create_task(monitor_partida(text_channel.id, expiration_time))

@bot.tree.command(name="añadir", description="Añade un participante a la partida")
async def añadir(interaction: discord.Interaction, user: discord.Member):
    guild = interaction.guild
    channel = interaction.channel
    partida = partidas.get(channel.id)
    
    if not partida or partida["creator"] != interaction.user.id:
        await interaction.response.send_message("No tienes permiso para agregar participantes a esta partida.", ephemeral=True)
        return
    
    # Evitar eliminar a Bot, Dirección o Moderador
    if any(role.name in ['Bot', 'Dirección', 'Moderador'] for role in user.roles):
        await interaction.response.send_message(f"No puedes eliminar al usuario {user.mention} ya que tiene un rol protegido.", ephemeral=True)
        return
    
    # Añadir permisos al participante en el canal de texto
    await channel.set_permissions(user, read_messages=True, send_messages=True)
    partida["participants"].append(user.id)
    
    await interaction.response.send_message(f"{user.mention} ha sido añadido a la partida.")

@bot.tree.command(name="eliminar", description="Elimina un participante de la partida")
async def eliminar(interaction: discord.Interaction, user: discord.Member):
    guild = interaction.guild
    channel = interaction.channel
    partida = partidas.get(channel.id)
    
    if not partida or partida["creator"] != interaction.user.id:
        await interaction.response.send_message("No tienes permiso para eliminar participantes de esta partida.", ephemeral=True)
        return
    
    # Evitar eliminar a Bot, Dirección o Moderador
    if any(role.name in ['Bot', 'Dirección', 'Moderador'] for role in user.roles):
        await interaction.response.send_message(f"No puedes eliminar al usuario {user.mention} ya que tiene un rol protegido.", ephemeral=True)
        return
    
    if user.id not in partida["participants"]:
        await interaction.response.send_message(f"{user.mention} no está en la partida.", ephemeral=True)
        return
    
    # Eliminar permisos del participante en el canal de texto
    await channel.set_permissions(user, read_messages=False, send_messages=False)
    partida["participants"].remove(user.id)
    
    await interaction.response.send_message(f"{user.mention} ha sido eliminado de la partida.")

@bot.tree.command(name="tiempo", description="Muestra el tiempo restante para la partida")
async def tiempo(interaction: discord.Interaction):
    channel = interaction.channel
    partida = partidas.get(channel.id)
    
    if not partida:
        await interaction.response.send_message("Esta partida no existe o ya ha expirado.", ephemeral=True)
        return
    
    time_left = partida["expiration_time"] - datetime.now()
    await interaction.response.send_message(f"Quedan {time_left.seconds // 60} minutos para que esta partida se cierre.")

@bot.tree.command(name="ampliar", description="Amplía la duración de la partida")
async def ampliar(interaction: discord.Interaction):
    channel = interaction.channel
    partida = partidas.get(channel.id)
    
    if not partida or partida["creator"] != interaction.user.id:
        await interaction.response.send_message("No tienes permiso para ampliar esta partida.", ephemeral=True)
        return
    
    partida["expiration_time"] += timedelta(days=1)  # Ampliar 24 horas
    await interaction.response.send_message("La duración de la partida ha sido ampliada en 24 horas.")

@bot.tree.command(name="cerrar", description="Cierra la partida manualmente")
async def cerrar(interaction: discord.Interaction):
    channel = interaction.channel
    partida = partidas.get(channel.id)
    
    if not partida or partida["creator"] != interaction.user.id:
        await interaction.response.send_message("No tienes permiso para cerrar esta partida.", ephemeral=True)
        return
    
    await channel.delete()
    
    partidas.pop(channel.id, None)
    
    await interaction.response.send_message(f"La partida ha sido cerrada.")

# Función para monitorear la duración de la partida y eliminar el canal cuando expire
async def monitor_partida(channel_id, expiration_time):
    await asyncio.sleep(480)  # Esperar 8 minutos
    partida = partidas.get(channel_id)
    if not partida:
        return  # La partida ya se cerró
    
    text_channel = partida["channel"]
    await text_channel.send("Quedan 2 minutos para que esta partida se cierre automáticamente.")
    
    await asyncio.sleep(120)  # Esperar 2 minutos más
    partida = partidas.pop(channel_id, None)
    if partida:
        await text_channel.send("La partida ha expirado. Cerrando el canal asociado...")
        await text_channel.delete()
        # Eliminar la categoría
        partida_category = partida["category"]
        await partida_category.delete()



#endregion

#region ----------Votaciones----------

# Comando para votar a otro usuario
@bot.tree.command(name="voto", description="Vota a un usuario con un puntaje del 1 al 10.")
async def voto(interaction: discord.Interaction, score: float, member: discord.Member):
    voter_id = interaction.user.id
    voted_id = member.id

    # Verificar si el usuario intenta votarse a sí mismo
    if voter_id == voted_id:
        await interaction.response.send_message("No puedes votarte a ti mismo.", ephemeral=True)
        return

    # Verificar si la puntuación es válida
    if score < 1 or score > 10:
        await interaction.response.send_message("Por favor, vota con un número entre 1 y 10.", ephemeral=True)
        return

    try:
        # Verificar si el usuario al que se quiere votar está registrado
        cursor.execute("SELECT * FROM users WHERE discord_id = %s", (voted_id,))
        target_user = cursor.fetchone()

        if not target_user:
            await interaction.response.send_message(f"{member.display_name} no está registrado en el sistema de votaciones.", ephemeral=True)
            return

        # Verificar si el votante ya votó por el usuario
        cursor.execute("SELECT * FROM votes WHERE voter_id = %s AND voted_id = %s", (voter_id, voted_id))
        existing_vote = cursor.fetchone()

        if existing_vote:
            await interaction.response.send_message(f"Ya has votado a {member.display_name} anteriormente.", ephemeral=True)
            return

        # Registrar el voto en la tabla `votes`
        cursor.execute("INSERT INTO votes (voter_id, voted_id, score) VALUES (%s, %s, %s)", (voter_id, voted_id, score))

        # Actualizar los puntos y la cantidad de votos en la tabla `users`
        cursor.execute("UPDATE users SET votes = votes + 1, points = points + %s WHERE discord_id = %s", (score, voted_id))
        conn.commit()

        # Calcular la nueva puntuación media del usuario votado
        cursor.execute("SELECT points, votes FROM users WHERE discord_id = %s", (voted_id,))
        user_data = cursor.fetchone()
        total_points, total_votes = user_data
        average_points = total_points / total_votes if total_votes > 0 else 0

        await interaction.response.send_message(f"Has votado a {member.display_name} con éxito. Su puntuación media es ahora {average_points:.2f}.", ephemeral=True)

    except Exception as e:
        print(f"Error: {e}")
        await interaction.response.send_message("Hubo un error al intentar registrar tu voto.", ephemeral=True)


# Comando para ver el puntaje de un usuario
@bot.tree.command(name="puntos", description="Consulta tu puntuación o la de otro usuario.")
async def puntos(interaction: discord.Interaction, member: discord.Member = None):
    if member is None:
        member = interaction.user

    try:
        # Verificar si el usuario está registrado
        cursor.execute("SELECT points, votes FROM users WHERE discord_id = %s", (member.id,))
        user_data = cursor.fetchone()

        if user_data:
            total_points, total_votes = user_data
            # Calcular la media de puntos
            average_points = total_points / total_votes if total_votes > 0 else 0
            await interaction.response.send_message(f"{member.display_name} tiene una puntuación media de {average_points:.2f} con {total_votes} votos.", ephemeral=True)
        else:
            await interaction.response.send_message(f"{member.display_name} no está registrado en el sistema de votaciones.", ephemeral=True)

    except Exception as e:
        print(f"Error: {e}")
        await interaction.response.send_message("Hubo un error al intentar obtener la puntuación.", ephemeral=True)

#endregion

#region ----------Limpieza Canal de Texto----------
@bot.tree.command(name="limpiar", description="Elimina un número específico de mensajes o todos los mensajes en el canal actual.")
async def limpiar(interaction: discord.Interaction, cantidad: int = None):
    # Responder rápidamente para evitar el timeout
    await interaction.response.defer(ephemeral=True)
    
    try:
        if cantidad is None:
            # Eliminar todos los mensajes del canal
            deleted_messages = await interaction.channel.purge(limit=None)
            await interaction.followup.send(f"Se han eliminado {len(deleted_messages)} mensajes.", ephemeral=True)
        else:
            # Comprobar que la cantidad es un número positivo
            if cantidad <= 0:
                await interaction.followup.send("La cantidad de mensajes a eliminar debe ser un número mayor que 0.", ephemeral=True)
                return

            # Eliminar los mensajes
            deleted_messages = await interaction.channel.purge(limit=cantidad)
            await interaction.followup.send(f"Se han eliminado {len(deleted_messages)} mensajes.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"Hubo un error al intentar eliminar los mensajes: {e}", ephemeral=True)

#endregion

#region -------------------- Ejecutar --------------------

bot.run(TOKEN)
#endregion
