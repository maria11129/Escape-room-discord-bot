import discord
from discord.ext import commands
import random

bot = commands.Bot(command_prefix='!')

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
async def answer(ctx, answer):
    # Check if the answer is correct
    if answer == puzzle.answer:
        await ctx.send('Correct!')
    else:
        await ctx.send('Incorrect. Try again!')

bot.run('YOUR_BOT_TOKEN')