import discord
from discord.ext import commands, tasks
import aiohttp
import asyncio
import random
import os
from datetime import datetime
import json

# Bot Setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Configuration
CHANNEL_ID = 1199441887392706680
TWITCH_CLIENT_ID = os.getenv('TWITCH_CLIENT_ID')
TWITCH_CLIENT_SECRET = os.getenv('TWITCH_CLIENT_SECRET')
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# Streamer Configuration
STREAMERS = {
    'heidelberr_muffin': {
        'platform': 'twitch',
        'url': 'https://www.twitch.tv/heidelberr_muffin',
        'username': 'heidelberr_muffin'
    },
    'block_b_boy': {
        'platform': 'twitch',
        'url': 'https://www.twitch.tv/block_b_boy',
        'username': 'block_b_boy'
    },
    'jasyygirl': {
        'platform': 'twitch',
        'url': 'https://www.twitch.tv/jasyygirl',
        'username': 'jasyygirl'
    },
    'witschgal': {
        'platform': 'twitch',
        'url': 'https://www.twitch.tv/witschgal',
        'username': 'witschgal'
    }
}

# Status tracking
streamer_status = {name: False for name in STREAMERS.keys()}
twitch_access_token = None

# Lustige Chaosquartier Ankündigungen
ANNOUNCEMENTS = [
    "🎉 ALARM IM CHAOSQUARTIER! {streamer} ist live und bringt das totale Chaos! {url} 🎮",
    "⚡ ACHTUNG ACHTUNG! {streamer} hat den Stream-Button gefunden und ist jetzt live! Das wird chaotisch! {url} 🔥",
    "🚨 BREAKING NEWS: {streamer} ist online und das Chaosquartier bebt vor Aufregung! {url} 💥",
    "🎪 Manege frei für {streamer}! Das Chaos-Spektakel beginnt JETZT! {url} 🎭",
    "🌪️ Ein wilder {streamer} ist erschienen! Das Chaosquartier ist nicht mehr sicher! {url} ⚡",
    "🎸 ROCK'N'ROLL! {streamer} rockt jetzt live das Chaosquartier! {url} 🤘",
    "🎲 Würfel sind gefallen! {streamer} ist live und bringt Glück ins Chaosquartier! {url} 🍀",
    "🎊 PARTY TIME! {streamer} macht Party und ihr seid alle eingeladen! {url} 🥳",
    "🔮 Die Kristallkugel sagt: {streamer} ist LIVE! Das Chaosquartier flippt aus! {url} ✨",
    "🎯 VOLLTREFFER! {streamer} hat ins Schwarze getroffen und ist jetzt live! {url} 🏹",
    "🎨 Kreativitäts-Alarm! {streamer} malt das Chaosquartier bunt - und das LIVE! {url} 🌈",
    "🎪 Ladies and Gentlemen! In der linken Ecke: {streamer} - LIVE im Chaosquartier! {url} 👑",
    "🚀 RAKETEN-START! {streamer} hebt ab und nimmt euch mit ins Live-Abenteuer! {url} 🌙",
    "🎭 Vorhang auf für {streamer}! Die Show im Chaosquartier beginnt! {url} 🎬",
    "⚗️ EXPERIMENTE IM LABOR! {streamer} ist live und mischt das Chaosquartier auf! {url} 🧪",
    "🎪 Zirkus Chaosquartier präsentiert: {streamer} - LIVE und in Farbe! {url} 🎠",
    "🌟 SUPERSTAR ALERT! {streamer} erleuchtet das Chaosquartier mit einem Live-Stream! {url} ⭐",
    "🎮 GAME ON! {streamer} startet das Spiel des Lebens - live im Chaosquartier! {url} 🕹️",
    "🎵 Die Musik spielt auf! {streamer} dirigiert das Chaos-Orchester - LIVE! {url} 🎼",
    "🎪 Hereinspaziert! {streamer} öffnet die Türen zum chaotischsten Stream ever! {url} 🎈",
    "⚡ BLITZ UND DONNER! {streamer} bringt das Gewitter ins Chaosquartier! {url} 🌩️",
    "🎯 Mission possible! Agent {streamer} ist live und das Chaosquartier ist das Ziel! {url} 🕵️",
    "🎪 Applaus, Applaus! {streamer} betritt die Bühne des Chaosquartiers! {url} 👏",
    "🚁 HUBSCHRAUBER-LANDUNG! {streamer} ist gelandet und streamt live! {url} 🚁",
    "🎨 Kunstwerk in Progress! {streamer} erschafft live ein Meisterwerk im Chaosquartier! {url} 🖼️",
    "🎪 Zauberstunde! {streamer} zaubert einen Live-Stream aus dem Hut! {url} 🎩",
    "⚡ ENERGIE-BOOST! {streamer} lädt das Chaosquartier mit Live-Power auf! {url} 🔋",
    "🎭 Shakespeare wäre neidisch! {streamer} schreibt Geschichte - live im Chaosquartier! {url} 📜",
    "🚀 3, 2, 1... LIVE! {streamer} startet durch ins Chaosquartier-Universum! {url} 🌌",
    "🎪 Das Unmögliche wird möglich! {streamer} ist LIVE und das Chaosquartier dreht durch! {url} 🎡"
]

class StreamBot:
    def __init__(self):
        self.session = None
    
    async def get_twitch_token(self):
        """Holt einen neuen Twitch Access Token"""
        global twitch_access_token
        
        if not TWITCH_CLIENT_ID or not TWITCH_CLIENT_SECRET:
            print("❌ Twitch API Credentials fehlen!")
            return None
            
        url = "https://id.twitch.tv/oauth2/token"
        params = {
            'client_id': TWITCH_CLIENT_ID,
            'client_secret': TWITCH_CLIENT_SECRET,
            'grant_type': 'client_credentials'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        twitch_access_token = data['access_token']
                        print("✅ Twitch Token erhalten!")
                        return twitch_access_token
                    else:
                        print(f"❌ Fehler beim Token-Abruf: {response.status}")
                        return None
        except Exception as e:
            print(f"❌ Fehler beim Token-Abruf: {e}")
            return None
    
    async def check_twitch_stream(self, username):
        """Überprüft ob ein Twitch Stream live ist"""
        if not twitch_access_token:
            await self.get_twitch_token()
            
        if not twitch_access_token:
            return False
            
        url = f"https://api.twitch.tv/helix/streams?user_login={username}"
        headers = {
            'Client-ID': TWITCH_CLIENT_ID,
            'Authorization': f'Bearer {twitch_access_token}'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 401:  # Token expired
                        await self.get_twitch_token()
                        headers['Authorization'] = f'Bearer {twitch_access_token}'
                        async with session.get(url, headers=headers) as retry_response:
                            if retry_response.status == 200:
                                data = await retry_response.json()
                                return len(data['data']) > 0
                    elif response.status == 200:
                        data = await response.json()
                        return len(data['data']) > 0
                    else:
                        print(f"❌ Twitch API Fehler für {username}: {response.status}")
                        return False
        except Exception as e:
            print(f"❌ Fehler bei Twitch Check für {username}: {e}")
            return False
    
    async def check_tiktok_live(self, username):
        """Überprüft TikTok Live Status (vereinfacht)"""
        # TikTok hat keine offizielle API für Live-Status
        # Hier könntest du Web Scraping implementieren oder eine alternative Lösung nutzen
        # Für jetzt returnieren wir False, da TikTok Live-Detection komplex ist
        return False

stream_bot = StreamBot()

# HTTP Server für UptimeRobot
from aiohttp import web

async def health_check(request):
    return web.Response(text="Bot läuft! Chaosquartier ist bereit! 🎪", status=200)

async def start_web_server():
    """Startet den HTTP Server für UptimeRobot"""
    app = web.Application()
    app.router.add_get('/', health_check)
    app.router.add_get('/health', health_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get('PORT', 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"🌐 Web Server läuft auf Port {port}")

@bot.event
async def on_ready():
    print(f'✅ {bot.user} ist bereit für das Chaosquartier!')
    print(f'📺 Überwache {len(STREAMERS)} Streamer')
    
    # Starte die Stream-Überwachung
    if not check_streams.is_running():
        check_streams.start()
    
    # Starte den Ping-Server für UptimeRobot
    if not ping_server.is_running():
        ping_server.start()

@tasks.loop(minutes=2)  # Alle 2 Minuten checken
async def check_streams():
    """Überprüft alle Streamer auf Live-Status"""
    global streamer_status
    
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print(f"❌ Channel {CHANNEL_ID} nicht gefunden!")
        return
    
    for streamer_name, config in STREAMERS.items():
        try:
            is_live = False
            
            if config['platform'] == 'twitch':
                is_live = await stream_bot.check_twitch_stream(config['username'])
            elif config['platform'] == 'tiktok':
                is_live = await stream_bot.check_tiktok_live(config['username'])
            
            # Wenn Streamer online gegangen ist (war offline, ist jetzt online)
            if is_live and not streamer_status[streamer_name]:
                # Wähle eine zufällige Ankündigung
                announcement = random.choice(ANNOUNCEMENTS)
                message = announcement.format(
                    streamer=config['username'],
                    url=config['url']
                )
                
                # Sende Ankündigung
                await channel.send(message)
                print(f"🎉 {streamer_name} ist live gegangen!")
            
            # Status aktualisieren
            streamer_status[streamer_name] = is_live
            
        except Exception as e:
            print(f"❌ Fehler beim Checken von {streamer_name}: {e}")
    
    print(f"🔄 Stream-Check abgeschlossen: {datetime.now().strftime('%H:%M:%S')}")

@tasks.loop(minutes=5)  # Alle 5 Minuten für UptimeRobot
async def ping_server():
    """Hält den Bot für UptimeRobot am Leben"""
    print(f"🏓 Ping! Bot läuft... {datetime.now().strftime('%H:%M:%S')}")

@bot.command(name='status')
async def stream_status(ctx):
    """Zeigt den aktuellen Status aller Streamer"""
    if ctx.channel.id != CHANNEL_ID:
        return
    
    embed = discord.Embed(
        title="🎪 Chaosquartier Stream Status",
        color=0xFF6B6B,
        timestamp=datetime.now()
    )
    
    for streamer_name, config in STREAMERS.items():
        status_emoji = "🔴 LIVE" if streamer_status[streamer_name] else "⚫ Offline"
        platform_emoji = "📺" if config['platform'] == 'twitch' else "📱"
        
        embed.add_field(
            name=f"{platform_emoji} {config['username']}",
            value=f"{status_emoji}",
            inline=True
        )
    
    embed.set_footer(text="Chaosquartier Stream Bot")
    await ctx.send(embed=embed)

@bot.command(name='test')
async def test_announcement(ctx, *, streamer_name=None):
    """Testet eine Ankündigung für einen Streamer"""
    if ctx.channel.id != CHANNEL_ID:
        return
    
    if not streamer_name or streamer_name not in STREAMERS:
        available = ", ".join(STREAMERS.keys())
        await ctx.send(f"❌ Bitte gib einen gültigen Streamer an: {available}")
        return
    
    config = STREAMERS[streamer_name]
    announcement = random.choice(ANNOUNCEMENTS)
    message = announcement.format(
        streamer=config['username'],
        url=config['url']
    )
    
    await ctx.send(f"🧪 **Test-Ankündigung:**\n{message}")

@bot.event
async def on_error(event, *args, **kwargs):
    print(f"❌ Bot Fehler in {event}: {args}")

# Bot starten
async def main():
    """Startet Bot und Web Server parallel"""
    # Starte Web Server
    await start_web_server()
    
    # Starte Bot
    try:
        await bot.start(DISCORD_TOKEN)
    except Exception as e:
        print(f"❌ Bot konnte nicht gestartet werden: {e}")
        print("💡 Stelle sicher, dass DISCORD_TOKEN gesetzt ist!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Bot gestoppt!")
    except Exception as e:
        print(f"❌ Fehler beim Starten: {e}")
