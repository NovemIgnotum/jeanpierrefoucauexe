import discord
from discord.ext import commands
from gtts import gTTS
import os
import io
from dotenv import load_dotenv

load_dotenv()

text_channel_id = int(os.getenv("TEXT_CHANNEL_ID"))
discord_token = os.getenv("DISCORD_TOKEN")
TTS_volume = float(os.getenv("TTS_VOLUME", 1.0))

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix='!', intents=intents)

def text_to_speech(text):
    """Convertit le texte en audio avec gTTS"""
    try:
        tts = gTTS(text=text, lang='fr', slow=False)
        audio_bytes = io.BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        return audio_bytes  # On conserve l'objet BytesIO qui a une méthode read()
    except Exception as e:
        print(f"Erreur gTTS: {e}")
        raise

@bot.event
async def on_ready():
    print(f'Bot connecté : {bot.user.name}')
    print(f'Surveille le salon : {text_channel_id}')

@bot.event
async def on_message(message):
    if message.author == bot.user or message.channel.id != text_channel_id:
        return

    if not message.author.voice:
        return await message.channel.send("Connectez-vous à un salon vocal d'abord !")

    voice_channel = message.author.voice.channel
    voice_client = discord.utils.get(bot.voice_clients, guild=message.guild)

    try:
        # Gestion connexion vocale
        if voice_client:
            if voice_client.channel != voice_channel:
                await voice_client.move_to(voice_channel)
        else:
            voice_client = await voice_channel.connect()

        # Génération et lecture audio
        audio_stream = text_to_speech(f'{message.content}')
        
        voice_client.play(
            discord.FFmpegPCMAudio(
                source=audio_stream,  # On passe directement l'objet BytesIO
                pipe=True
            ),
            after=lambda e: print(f"Lecture terminée : {e}" if e else "Succès")
        )
        voice_client.source = discord.PCMVolumeTransformer(voice_client.source)
        voice_client.source.volume = TTS_volume

    except Exception as e:
        print(f"Erreur: {e}")
        await message.channel.send("Problème de lecture audio")

    await bot.process_commands(message)

# [...] (Les commandes join et leave restent identiques)

bot.run(discord_token)