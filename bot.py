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
        # Update the existing document with the new amount and registration date
        collection.update_one({'csn': csn}, {'$set': {'amount': amount, 'registration_date': datetime.utcnow()}})
    else:
        # Create a new document for the CSN
        data = {
            'csn': csn,
            'registration_date': datetime.utcnow(),
            'amount': amount
        }
        collection.insert_one(data)
    
    # Retrieve the updated data from the database
    updated_data = collection.find_one({'csn': csn})
    
    # Calculate the time difference
    registration_date = updated_data['registration_date']
    current_date = datetime.utcnow()
    time_diff = current_date - registration_date
    
    # Check if the data is less than 24 hours old
    if time_diff < timedelta(hours=24):
        hours_passed = time_diff.total_seconds() // 3600
        
        # Create an embed with green color
        embed = discord.Embed(title=f"CSN {csn} Information", description="この市民には包帯を渡せます", color=discord.Color.green())
        embed.set_thumbnail(url="https://i.imgur.com/u6oDUNv.png")
        embed.add_field(name="最後にCSNが登録されたのは", value=f"{hours_passed:.2f} 時間前", inline=False)
        embed.add_field(name="登録された日付", value=registration_date.strftime('%Y-%m-%d'), inline=False)
        embed.add_field(name="包帯の個数", value=updated_data['amount'], inline=False)
        embed.set_footer(text="Powered By NickyBoy", icon_url="https://i.imgur.com/QfmDKS6.png")
    else:
        hours_passed = time_diff.total_seconds() // 3600
        
        # Create an embed with red color
        embed = discord.Embed(title=f"CSN {csn} Information", description="この市民には包帯を渡せません", color=discord.Color.red())
        embed.set_thumbnail(url="https://i.imgur.com/qLnl40c.png")
        embed.add_field(name="最後にCSNが登録されたのは", value=f"{hours_passed:.2f} hours", inline=False)
        embed.add_field(name="登録された日付", value=registration_date.strftime('%Y-%m-%d'), inline=False)
        embed.add_field(name="包帯の個数", value=updated_data['amount'], inline=False)
        embed.set_footer(text="Powered By NickyBoy", icon_url="https://i.imgur.com/QfmDKS6.png")
        
    await ctx.respond(embed=embed)

# Run the bot
bot.run(DISCORD_BOT_TOKEN)
