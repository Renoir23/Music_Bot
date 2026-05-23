import os
import discord
from discord.ext import commands
import asyncio
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import yt_dlp
import static_ffmpeg
static_ffmpeg.add_paths()  # ဒါက ffmpeg ကို system path ထဲ အလိုအလျောက် ထည့်ပေးသွားမှာပါ

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True # Voice Channel ထဲ ဝင်ဖို့အတွက် လိုအပ်ပါတယ်
bot = commands.Bot(command_prefix="!", intents=intents)

# yt-dlp နဲ့ FFmpeg ရဲ့ သီချင်းဆွဲမယ့် အပြင်အဆင်များ
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'default_search': 'auto'
}
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}
ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

@bot.event
async def on_ready():
    print(f"🎵 {bot.user.name} Music Bot အဆင်သင့်ဖြစ်ပါပြီ!")

@bot.command()
async def play(ctx, *, search: str):
    """သီချင်းဖွင့်ရန် Command (ဥပမာ - !play မုန်းရင်လည်းမုန်း)"""
    
    # ဖွင့်ခိုင်းတဲ့သူ Voice Channel ထဲ ရှိမရှိ စစ်ဆေးခြင်း
    if not ctx.author.voice:
        return await ctx.send("❌ သီချင်းဖွင့်ဖို့ အရင်ဦးစွာ Voice Channel တစ်ခုထဲ ဝင်ပေးပါဦးဗျာ။")
    
    voice_channel = ctx.author.voice.channel
    
    # Bot ကို Voice Channel ထဲ ဝင်ခိုင်းခြင်း
    if ctx.voice_client is None:
        await voice_channel.connect()
    else:
        await ctx.voice_client.move_to(voice_channel)
        
    await ctx.send(f"🔍 **'{search}'** ကို ရှာဖွေနေပါတယ်...")
    
    loop = asyncio.get_event_loop()
    try:
        # YouTube ကနေ သီချင်းဒေတာ ရှာဖွေဆွဲယူခြင်း
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(f"ytsearch:{search}", download=False))
        if 'entries' in data and len(data['entries']) > 0:
            song_info = data['entries'][0]
        else:
            return await ctx.send("❌ သီချင်း ရှာမတွေ့ပါဘူးခင်ဗျာ။")
            
        url = song_info['url']
        title = song_info['title']
        duration = song_info.get('duration', 0)
        minutes, seconds = divmod(duration, 60)
        
        # လက်ရှိ သီချင်းဖွင့်နေရင် ရပ်လိုက်ခြင်း
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            
        # သီချင်းစတင်ဖွင့်ခြင်း
        source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)
        ctx.voice_client.play(source)
        
        # --------------------------------------------------
        # 🌟 VIRTUAL MUSIC CARD (EMBED DESIGN)
        # --------------------------------------------------
        embed = discord.Embed(
            title="🎵 NOW PLAYING • VIRTUAL PLAYER",
            description=f"**[{title}]({song_info['webpage_url']})**",
            color=discord.Color.from_rgb(127, 0, 255) # ခရမ်းရောင် Card ဒီဇိုင်း
        )
        
        # Card ထဲက အချက်အလက်များ
        embed.add_field(name="🎤 Artist", value=song_info.get('uploader', 'Unknown Artist'), inline=True)
        embed.add_field(name="🕒 Duration", value=f"{minutes:02d}:{seconds:02d}", inline=True)
        
        # Progress Bar အလှပြလိုင်း (Virtual Card ပုံစံဖြစ်အောင် စာသားဖြင့် ဖန်တီးထားခြင်း)
        embed.add_field(name="⏮️  ▶️  ⏭️  ━━━🔘────────", value="⚡ **PREMIUM AUDIO STREAM**", inline=False)
        
        # ညာဘက်ထောင့်က Album Art ပုံစံ Icon အဝိုင်းလေး
        embed.set_thumbnail(url="https://i.imgur.com/8Q8WpXF.png") 
        embed.set_footer(text=f"Requested by {ctx.author.name} • VISA MUSIC ONLY")
        
        # ဆောက်ထားတဲ့ Virtual Card ကို ပို့ပေးခြင်း
        await ctx.send(embed=embed)
        
    except Exception as e:
        print(e)
        await ctx.send("❌ သီချင်းဖွင့်ရတာ အဆင်မပြေဖြစ်သွားပါတယ်။")

@bot.command()
async def stop(ctx):
    """သီချင်းရပ်ပြီး Channel ထဲက ထွက်ရန်"""
    if ctx.voice_client:
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
        await ctx.voice_client.disconnect()
        await ctx.send("🛑 သီချင်းဖွင့်ခြင်းကို ရပ်ဆိုင်းပြီး Voice Channel ထဲက ထွက်လိုက်ပါပြီ။")
    else:
        await ctx.send("❌ Bot က Voice Channel ထဲမှာ ရှိမနေပါဘူး။")
# Render Web Server (Port Scan ကျော်ရန်)
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Music Bot is running perfectly!")

def run_health_check():
    port = int(os.getenv("PORT", 8000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=run_health_check, daemon=True).start()
    
    TOKEN = os.getenv("DISCORD_TOKEN")
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("Error: DISCORD_TOKEN မတွေ့ရှိပါ။")
