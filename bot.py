import os
import discord
from discord.ext import commands
from pymongo import MongoClient
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the bot token from the environment variable
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
MONGODB_CONNECTION_URL = os.getenv('MONGODB_CONNECTION_URL')

# Connect to MongoDB
client = MongoClient(MONGODB_CONNECTION_URL)
db = client['discord_bot']
collection = db['csn_data']

# Create a bot instance
intents = discord.Intents.default()
bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.slash_command(name='touroku', description='Register a CSN')
async def register_csn(ctx, csn: str, amount: int):
    # Check if the CSN already exists in the database
    existing_data = collection.find_one({'csn': csn})
    
    if existing_data:
        # Update the existing document with the new amount and registration date
        collection.update_one({'csn': csn}, {'$set': {'amount': amount, 'registration_date': datetime.now()}})
    else:
        # Create a new document for the CSN
        data = {
            'csn': csn,
            'registration_date': datetime.now(),
            'amount': amount
        }
        collection.insert_one(data)
    
    # Retrieve the updated data from the database
    updated_data = collection.find_one({'csn': csn})
    
    # Calculate the time difference
    registration_date = updated_data['registration_date']
    current_date = datetime.now()
    time_diff = current_date - registration_date
    
    # Check if the data is less than 24 hours old
    if time_diff < timedelta(hours=24):
        hours_passed = time_diff.total_seconds() // 3600
        
        # Create an embed with green color
        embed = discord.Embed(title=f"CSN {csn} Information", color=discord.Color.green())
        embed.add_field(name="Time since last registration", value=f"{hours_passed:.2f} hours", inline=False)
        embed.add_field(name="Registration Date", value=registration_date.strftime('%Y-%m-%d'), inline=False)
        embed.add_field(name="Amount", value=updated_data['amount'], inline=False)
        
        await ctx.respond(embed=embed)
    else:
        hours_passed = time_diff.total_seconds() // 3600
        
        # Create an embed with red color
        embed = discord.Embed(title=f"CSN {csn} Information", color=discord.Color.red())
        embed.add_field(name="Time since last registration", value=f"{hours_passed:.2f} hours", inline=False)
        embed.add_field(name="Registration Date", value=registration_date.strftime('%Y-%m-%d'), inline=False)
        embed.add_field(name="Amount", value=updated_data['amount'], inline=False)
        
        await ctx.respond(embed=embed)

# Run the bot
bot.run(DISCORD_BOT_TOKEN)
