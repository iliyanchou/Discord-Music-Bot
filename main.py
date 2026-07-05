import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp
import asyncio

# --- ТВОЯТ ТОКЕН ---
TOKEN = ''

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

YDL_OPTIONS = {
    'format': 'bestaudio',
    'noplaylist': True,
    'default_search': 'auto',
    'quiet': True
}

# --- СТРУКТУРА ЗА ДАННИТЕ ---
class GuildState:
    def __init__(self):
        self.queue = []      # Списък с чакащи песни (title, url)
        self.history = []    # Списък с минали песни
        self.current = None  # Текущата песен (title, url)
        self.loop = False    # Дали да повтаря (по желание за бъдеще)

guild_states = {}

def get_state(guild_id):
    if guild_id not in guild_states:
        guild_states[guild_id] = GuildState()
    return guild_states[guild_id]

class MusicBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("Slash командите са синхронизирани!")

    async def on_ready(self):
        print(f'{self.user} е на линия с новата система за опашки!')

bot = MusicBot()

# --- ЛОГИКА ЗА ПУСКАНЕ ---

def play_next(interaction, voice_client):
    guild_id = interaction.guild.id
    state = get_state(guild_id)

    # 1. Запазваме текущата в историята (ако е имало такава)
    if state.current:
        state.history.append(state.current)

    # 2. Проверяваме дали има следваща в опашката
    if len(state.queue) > 0:
        # Взимаме първата от опашката (махаме я от списъка)
        title, url = state.queue.pop(0)
        state.current = (title, url)

        # Подготовка на аудиото
        source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)
        
        # Пускане + callback за следващата
        voice_client.play(source, after=lambda e: check_queue_loop(interaction, voice_client))
        print(f"Пускам: {title}")
    else:
        state.current = None
        print("Опашката свърши.")

def check_queue_loop(interaction, voice_client):
    """Тази функция се вика от thread-а на ffmpeg, затова трябва да е внимателна"""
    fut = asyncio.run_coroutine_threadsafe(next_song_task(interaction, voice_client), bot.loop)
    try:
        fut.result()
    except:
        pass

async def next_song_task(interaction, voice_client):
    play_next(interaction, voice_client)

async def search_song(query):
    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
        try:
            info = ydl.extract_info(query, download=False)
            if 'entries' in info:
                info = info['entries'][0]
            return info['title'], info['url']
        except:
            return None, None

# --- ОСНОВНИ КОМАНДИ ---

@bot.tree.command(name="play", description="Пуска песен или я добавя в опашката")
@app_commands.describe(query="Линк или име на песента")
async def play(interaction: discord.Interaction, query: str):
    await interaction.response.defer()
    
    if not interaction.user.voice:
        await interaction.followup.send("Влез в гласов канал първо!")
        return

    channel = interaction.user.voice.channel
    voice_client = discord.utils.get(bot.voice_clients, guild=interaction.guild)

    if not voice_client:
        voice_client = await channel.connect()
    elif voice_client.channel != channel:
        await voice_client.move_to(channel)

    # Търсене
    title, url = await search_song(query)
    if not title:
        await interaction.followup.send("Не можах да намеря тази песен.")
        return

    state = get_state(interaction.guild.id)

    # Ако нищо не свири, пускаме веднага
    if not voice_client.is_playing() and not voice_client.is_paused():
        state.current = (title, url)
        source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)
        voice_client.play(source, after=lambda e: check_queue_loop(interaction, voice_client))
        await interaction.followup.send(f"🎶 Пускам: **{title}**")
    else:
        # Добавяме в края на опашката
        state.queue.append((title, url))
        pos = len(state.queue) # Тъй като 0 е текущата, позицията в чакащите е реалната позиция
        await interaction.followup.send(f"✅ Добавена на позиция #{pos}: **{title}**")

@bot.tree.command(name="pause", description="Пауза")
async def pause(interaction: discord.Interaction):
    vc = discord.utils.get(bot.voice_clients, guild=interaction.guild)
    if vc and vc.is_playing():
        vc.pause()
        await interaction.response.send_message("⏸️ Паузирано.")
    else:
        await interaction.response.send_message("Нищо не свири.")

@bot.tree.command(name="unpause", description="Продължава свиренето")
async def unpause(interaction: discord.Interaction):
    vc = discord.utils.get(bot.voice_clients, guild=interaction.guild)
    if vc and vc.is_paused():
        vc.resume()
        await interaction.response.send_message("▶️ Продължаваме.")
    else:
        await interaction.response.send_message("Не е на пауза.")

@bot.tree.command(name="skip", description="Скипва текущата песен")
async def skip(interaction: discord.Interaction):
    vc = discord.utils.get(bot.voice_clients, guild=interaction.guild)
    if vc and (vc.is_playing() or vc.is_paused()):
        vc.stop() # Това автоматично вика play_next
        await interaction.response.send_message("⏭️ Скип!")
    else:
        await interaction.response.send_message("Няма какво да скипвам.")

@bot.tree.command(name="next", description="Скипва (същото като /skip)")
async def next_song(interaction: discord.Interaction):
    await skip(interaction)

@bot.tree.command(name="previous", description="Връща предишната песен")
async def previous(interaction: discord.Interaction):
    vc = discord.utils.get(bot.voice_clients, guild=interaction.guild)
    state = get_state(interaction.guild.id)
    
    if not state.history:
        await interaction.response.send_message("Няма предишни песни в историята.")
        return

    # Логика за връщане:
    # 1. Взимаме последната песен от историята
    prev_title, prev_url = state.history.pop()
    
    # 2. Ако в момента свири песен, я връщаме най-отпред в опашката (да не я губим)
    if state.current:
        state.queue.insert(0, state.current)
    
    # 3. Слагаме "старата" песен като текуща (фактически я "инжектираме" за пускане)
    # За да сработи, я слагаме най-отпред в опашката и спираме плеъра.
    # play_next ще я вземе веднага.
    state.queue.insert(0, (prev_title, prev_url))
    
    # Тъй като play_next взима от history, трябва да внимаваме да не я дублираме в историята
    # Но play_next ще я сложи пак в history. Засега е ОК.

    if vc:
        vc.stop()
        await interaction.response.send_message(f"⏮️ Връщам назад: **{prev_title}**")
    else:
        await interaction.response.send_message("Грешка с плейъра.")

# --- QUEUE ГРУПА ОТ КОМАНДИ ---

# Създаваме група /queue
queue_group = app_commands.Group(name="queue", description="Управление на опашката")

@queue_group.command(name="show", description="Показва списъка с песни")
async def queue_show(interaction: discord.Interaction):
    state = get_state(interaction.guild.id)
    msg = ""
    
    if state.current:
        msg += f"🔥 **#0 (Сега): {state.current[0]}**\n\n"
    else:
        msg += "Нищо не свири в момента.\n"
        
    if state.queue:
        for i, (title, url) in enumerate(state.queue):
            msg += f"**#{i+1}** - {title}\n"
    else:
        msg += "\n*Няма други песни в опашката.*"
        
    await interaction.response.send_message(msg)

@queue_group.command(name="remove", description="Маха песен по номер (напр. 5)")
@app_commands.describe(position="Номер на песента от /queue show")
async def queue_remove(interaction: discord.Interaction, position: int):
    state = get_state(interaction.guild.id)
    
    if position <= 0:
        await interaction.response.send_message("Не можеш да махнеш песен #0 (текущата) с тази команда. Използвай /skip.")
        return
        
    # Коригираме индекса (потребителят вижда 1, но в Python списъка е 0)
    real_index = position - 1
    
    if 0 <= real_index < len(state.queue):
        removed_song = state.queue.pop(real_index)
        await interaction.response.send_message(f"🗑️ Махнах песен #{position}: **{removed_song[0]}**")
    else:
        await interaction.response.send_message(f"❌ Няма песен с номер #{position}.")

@queue_group.command(name="add", description="Вмъква песен на конкретна позиция")
@app_commands.describe(position="На коя позиция да застане", query="Линк или име")
async def queue_add(interaction: discord.Interaction, position: int, query: str):
    await interaction.response.defer()
    state = get_state(interaction.guild.id)
    
    if position <= 0:
        await interaction.followup.send("Позицията трябва да е 1 или повече.")
        return
        
    title, url = await search_song(query)
    if not title:
        await interaction.followup.send("Не намерих песента.")
        return
        
    # Коригираме индекса. Ако иска да е #1 (следващата), insert index е 0.
    insert_index = position - 1
    
    # Ако индексът е по-голям от дължината, просто добавяме накрая
    if insert_index > len(state.queue):
        state.queue.append((title, url))
        await interaction.followup.send(f"📥 Опашката е по-къса, затова я сложих най-накрая: **{title}**")
    else:
        state.queue.insert(insert_index, (title, url))
        await interaction.followup.send(f"📥 Вмъкнах **{title}** на позиция **#{position}**.")

# Добавяме групата към бота
bot.tree.add_command(queue_group)

bot.run(TOKEN)
