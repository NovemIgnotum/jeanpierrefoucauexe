import discord
from discord.ext import commands
from gtts import gTTS  # Remplacement de pyttsx3
import os
import io
from pydub import AudioSegment
from dotenv import load_dotenv

load_dotenv()

text_channel_id = int(os.getenv("TEXT_CHANNEL_ID"))  # Conversion en int
discord_token = os.getenv("DISCORD_TOKEN")
TTS_volume = float(os.getenv("TTS_VOLUME", 1.0))

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix='!', intents=intents)

def text_to_speech(text):
    """Version modifiée utilisant gTTS"""
    try:
        # Création du fichier audio en mémoire
        tts = gTTS(text=text, lang='fr', slow=False)
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        
        # Conversion en AudioSegment
        audio = AudioSegment.from_file(mp3_fp, format="mp3")
        return audio
        
    except Exception as e:
        print(f"Erreur gTTS: {e}")
        raise

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
        
        # Utilisation d'un fichier temporaire en mémoire
        with io.BytesIO() as temp_output:
            audio.export(temp_output, format="mp3")
            temp_output.seek(0)
            voice_client.play(discord.FFmpegPCMAudio(temp_output))
            
            voice_client.source = discord.PCMVolumeTransformer(voice_client.source)
            voice_client.source.volume = TTS_volume

    except Exception as e:
        print(f"Erreur: {e}")
        await message.channel.send("Une erreur est survenue lors de la lecture du message")

    await bot.process_commands(message)

# [...] (Les commandes setup, join, leave restent identiques)

bot.run(discord_token)