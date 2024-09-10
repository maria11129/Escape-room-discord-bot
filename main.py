import discord
from discord.ext import commands
import os 
from dotenv import load_dotenv


# Load environment variables from the .env file
load_dotenv()

# Define the necessary intents
intents = discord.Intents.default()
intents.messages = True  # Enable the intent to receive message events

# Create the bot instance with command prefix and intents
bot = commands.Bot(command_prefix='!', intents=intents)

# Define a room class
class Room:
    def __init__(self, name, description, puzzles):
        self.name = name
        self.description = description
        self.puzzles = puzzles

# Define a puzzle class
class Puzzle:
    def __init__(self, question, answer, clue):
        self.question = question
        self.answer = answer
        self.clue = clue

# Create a room
room = Room('Detective\'s Office', 'Solve the mystery!', [
    Puzzle('What is the combination to the safe?', '1234', 'Check the bookshelf'),
    Puzzle('Who is the suspect?', 'John Doe', 'Look at the security footage')
])

# Create a bot command to start the game
@bot.command()
async def start(ctx):
    await ctx.send(f'Welcome to {room.name}!')
    await ctx.send(room.description)
    for puzzle in room.puzzles:
        await ctx.send(puzzle.question)

# Create a bot command to submit an answer
@bot.command()
async def answer(ctx, *, answer: str):  # Use * to capture the whole answer as a single string
    # Check if the answer is correct
    for puzzle in room.puzzles:
        if answer.lower() == puzzle.answer.lower():  # Ignore case for answer comparison
            await ctx.send('Correct!')
            break
    else:
        await ctx.send('Incorrect. Try again!')

# Run the bot
bot.run(os.getenv('TOKEN'))
