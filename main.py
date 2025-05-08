import discord
from discord.ext import commands
import pyttsx3
import os
import io
from pydub import AudioSegment
from pydub.playback import play
from dotenv import load_dotenv

load_dotenv()

text_channel_id = os.getenv("TEXT_CHANNEL_ID")
discord_token = os.getenv("DISCORD_TOKEN")
TTS_rate = int(os.getenv("TTS_RATE", 150))
TTS_volume = float(os.getenv("TTS_VOLUME", 1.0))

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix='!', intents=intents)

engine = pyttsx3.init()
engine.setProperty('rate', TTS_rate)
engine.setProperty('volume', TTS_volume)
engine.setProperty('voice', 'french')

def text_to_speech(text):
    temp_file = "temp.wav"
    engine.save_to_file(text, temp_file)
    engine.runAndWait()

    audio = AudioSegment.from_wav(temp_file)
    os.remove(temp_file)
    return audio

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} - {bot.user.id}')
    print(f'Watching for messages in channel ID: {text_channel_id}')

@bot.event
async def on_message(message):
    if message.author == bot.user or message.channel.id != text_channel_id:
        return

    voice_state = message.author.voice
    if not voice_state:
        return await message.channel.send("Vous devez être dans un salon vocal pour utiliser cette fonctionnalité!")

    voice_channel = voice_state.channel
    voice_client = discord.utils.get(bot.voice_clients, guild=message.guild)

    try:
        # Gestion de la connexion vocale
        if voice_client and voice_client.channel != voice_channel:
            await voice_client.move_to(voice_channel)
        elif not voice_client:
            voice_client = await voice_channel.connect()

        # Conversion et lecture du message
        audio = text_to_speech(f"{message.author.display_name} dit: {message.content}")
        temp_output = "temp_output.mp3"
        audio.export(temp_output, format="mp3")
        
        voice_client.play(discord.FFmpegPCMAudio(temp_output))
        voice_client.source = discord.PCMVolumeTransformer(voice_client.source)
        voice_client.source.volume = TTS_volume
        
        def after_playing(error):
            if os.path.exists(temp_output):
                os.remove(temp_output)
        voice_client.after = after_playing

    except Exception as e:
        print(f"Erreur: {e}")
        await message.channel.send("Une erreur est survenue lors de la lecture du message")

    await bot.process_commands(message)

@bot.command()
async def setup(ctx, channel: discord.TextChannel = None):
    """Configure le salon textuel à surveiller"""
    if not channel:
        return await ctx.send("Veuillez spécifier un salon textuel: `!setup #nom-du-salon`")
    
    global TEXT_CHANNEL_ID
    TEXT_CHANNEL_ID = channel.id
    await ctx.send(f"Salon textuel configuré sur: {channel.mention}")

@bot.command()
async def join(ctx):
    """Rejoint votre salon vocal"""
    if not ctx.author.voice:
        return await ctx.send("Vous n'êtes pas dans un salon vocal!")
    
    channel = ctx.author.voice.channel
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    
    if voice_client and voice_client.channel == channel:
        return await ctx.send("Je suis déjà dans votre salon!")
    
    if voice_client:
        await voice_client.move_to(channel)
    else:
        await channel.connect()
    
    await ctx.send(f"Connecté à {channel.name}")

@bot.command()
async def leave(ctx):
    """Quitte le salon vocal"""
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client and voice_client.is_connected():
        await voice_client.disconnect()
        await ctx.send("Déconnecté du salon vocal")
    else:
        await ctx.send("Je ne suis pas dans un salon vocal")

bot.run(discord_token)