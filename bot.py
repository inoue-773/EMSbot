import os
import discord
from discord.ext import commands
from pymongo import MongoClient
from datetime import datetime, timedelta
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
        # Calculate the time difference
        registration_date = existing_data['registration_date']
        current_date = datetime.utcnow()
        time_diff = current_date - registration_date
        hours_passed = time_diff.total_seconds() // 3600

        # Determine the embed color based on the time difference
        if time_diff < timedelta(hours=24):
            color1 = discord.Color.red()
            description1 = "この市民には包帯を渡せません"
            url1 = "https://i.imgur.com/u6oDUNv.png"
        else:
            color1 = discord.Color.green()
            description1 = "この市民には包帯を渡せます"
            url1 = "https://i.imgur.com/qLnl40c.png"

        # Create an embed with the existing data
        embed = discord.Embed(title=f"🔍 {csn} の情報", description=description1, color=color1)
        embed.set_thumbnail(url=url1)
        embed.add_field(name="📅最後に登録された時間", value=f"{hours_passed:.2f} 時間前", inline=False)
        embed.add_field(name="⏲️登録された日付と時間", value=registration_date.strftime('%Y-%m-%d %H:%M'), inline=False)
        embed.add_field(name="🩹包帯の個数", value=existing_data['amount'], inline=False)
        embed.set_footer(text="Powered By NickyBoy", icon_url="https://i.imgur.com/QfmDKS6.png")
        await ctx.respond(embed=embed)

        # Update the existing document with the new amount and registration date only after responding
        collection.update_one({'csn': csn}, {'$set': {'amount': amount, 'registration_date': datetime.utcnow()}})
    else:
        # Create a new document for the CSN
        data = {
            'csn': csn,
            'registration_date': datetime.utcnow(),
            'amount': amount
        }
        collection.insert_one(data)
        embed = discord.Embed(title=f"🔍 {csn} の情報", description="新しいデータを登録しました", color=discord.Color.blue())
        embed.add_field(name="📅登録された日付と時間", value=data['registration_date'].strftime('%Y-%m-%d %H:%M'), inline=False)
        embed.add_field(name="🩹包帯の個数", value=amount, inline=False)
        embed.set_footer(text="Powered By NickyBoy", icon_url="https://i.imgur.com/QfmDKS6.png")
        await ctx.respond(embed=embed)

# Run the bot
bot.run(DISCORD_BOT_TOKEN)
