import os
import discord
from discord.ext import commands
from pymongo import MongoClient
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo  # Import ZoneInfo from zoneinfo module
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the bot token and MongoDB connection URL from the environment variable
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
MONGODB_CONNECTION_URL = os.getenv('MONGODB_CONNECTION_URL')

# Connect to MongoDB
client = MongoClient(MONGODB_CONNECTION_URL)
db = client['discord_bot']
collection = db['csn_data']

# Create a bot instance with all intents enabled
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.slash_command(name='touroku', description='CSNを登録・照会')
async def register_csn(ctx, csn: discord.Option(str, "CSNを入力"), amount: discord.Option(int, "包帯の個数")):
    # Check if the CSN already exists in the database
    existing_data = collection.find_one({'csn': csn})
    
    if existing_data:
        # Convert registration_date from ISO 8601 string to datetime object
        registration_date_str = existing_data['registration_date'].rstrip('Z')  # Remove the 'Z'
        registration_date = datetime.fromisoformat(registration_date_str)
        registration_date = registration_date.replace(tzinfo=timezone.utc)  # Assign UTC timezone
        
        # Convert UTC to JST
        jst_date = registration_date.astimezone(ZoneInfo("Asia/Tokyo"))
        
        current_date = datetime.now(ZoneInfo("Asia/Tokyo"))
        time_diff = current_date - jst_date
        hours_passed = time_diff.total_seconds() // 3600

        # Determine the embed color based on the time difference
        if time_diff < timedelta(hours=24):
            color = discord.Color.red()
            description = "この市民には包帯を渡せません"
        else:
            color = discord.Color.green()
            description = "この市民には包帯を渡せます"

        # Create an embed with the existing data
        embed = discord.Embed(title=f"🔍 {csn} の情報", description=description, color=color)
        embed.set_thumbnail(url="https://i.imgur.com/u6oDUNv.png" if color == discord.Color.red() else "https://i.imgur.com/qLnl40c.png")
        embed.add_field(name="📅最後に登録された時間", value=f"{hours_passed:.2f} 時間前", inline=False)
        embed.add_field(name="⏲️登録された日付と時間", value=jst_date.strftime('%Y-%m-%d %H:%M'), inline=False)
        embed.add_field(name="🩹包帯の個数", value=existing_data['amount'], inline=False)
        embed.set_footer(text="Powered By NickyBoy", icon_url="https://i.imgur.com/QfmDKS6.png")
        await ctx.respond(embed=embed)

        # Update the existing document with the new amount and registration date only after responding
        collection.update_one({'csn': csn}, {'$set': {'amount': amount, 'registration_date': datetime.now(ZoneInfo("Asia/Tokyo")).isoformat()}})
    else:
        # Get the current time in JST
        jst_now = datetime.now(ZoneInfo("Asia/Tokyo"))
        
        # Format the JST datetime in the desired format
        formatted_jst_now = jst_now.strftime('%Y-%m-%d %H:%M')
        
        # Create a new document with the formatted JST time
        data = {
            'csn': csn,
            'registration_date': formatted_jst_now,
            'amount': amount
        }
        collection.insert_one(data)
        
        # Create an embed to confirm the registration
        embed = discord.Embed(title=f"🔍 {csn} の情報", description="新しいデータを登録しました", color=discord.Color.blue())
        embed.add_field(name="📅登録された日付と時間", value=formatted_jst_now, inline=False)
        embed.add_field(name="🩹包帯の個数", value=amount, inline=False)
        embed.set_footer(text="Powered By NickyBoy", icon_url="https://i.imgur.com/QfmDKS6.png")
        await ctx.respond(embed=embed)

# Run the bot
bot.run(DISCORD_BOT_TOKEN)
