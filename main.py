import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio


# Load environment variables from the .env file
load_dotenv()

# Define the necessary intents
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True  # Enable to receive message content

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

# Create new puzzles
puzzle1 = Puzzle('I am a sequence of digits, but I only know 0s and 1s. When you add my values together, you get a perfect square. What am I?', '10000', 'Think about numbers that computers love to talk in!')
puzzle2 = Puzzle('I am a 7-bit binary number. When my digits are interpreted as a decimal number, they represent a prime number. When converted to ASCII, I am a character used in many programming languages to represent a newline. What am I?', '0000100', 'Look for a binary sequence that translates to a symbol commonly used to start a new line.')
puzzle3 = Puzzle('I am a binary number that is 8 bits long. When you convert me to decimal, I give you the total number of days in a non-leap year. My binary representation starts with 0001. What am I?', '00100111', 'Consider how many days are in a standard year and how that might be represented in binary.')

# Create new room
room1 = Room('Cipher Chamber', 'Solve puzzles related to binary', [puzzle1, puzzle2, puzzle3])

rooms = [room1]

# Variables to track game state
current_room = None
current_puzzle_index = 0
TIME_LIMIT = 60

# Create a bot command to start the game
@bot.command()
async def enter(ctx, *, room_name: str):
    print(f"enter command received with room_name: '{room_name}'")  # Debug output
    global current_room, current_puzzle_index
    current_room = None
    current_puzzle_index = 0
    room_name = room_name.strip().lower()  # Normalize and strip whitespace
    print(f"Normalized room_name: '{room_name}'")  # Debug output
    for r in rooms:
        print(f"Checking room: '{r.name.lower()}'")  # Debug output
        if r.name.lower() == room_name:  # Compare in lowercase
            current_room = r
            await ctx.send(f'Welcome to {r.name}!')
            await ctx.send(r.description)
            # Send the first puzzle
            await ctx.send(r.puzzles[current_puzzle_index].question)
        try:
            await asyncio.sleep(TIME_LIMIT)
            await ctx.send(f"Time's up! The answer to {r.puzzles[current_puzzle_index].question} was {r.puzzles[current_puzzle_index].answer}.")
        except asyncio.CancelledError:
            pass

            break
    else:
        await ctx.send('Room not found.')

# Create a bot command to submit an answer
@bot.command()
async def answer(ctx, *, user_answer: str):
    global current_room, current_puzzle_index
    if current_room is None:
        await ctx.send('You need to start a room first using !start [room_name]')
        return

    # Get the current puzzle
    current_puzzle = current_room.puzzles[current_puzzle_index]

    if user_answer.lower() == current_puzzle.answer.lower():
        await ctx.send('Correct!')
        current_puzzle_index += 1  # Move to the next puzzle

        # Check if there are more puzzles
        if current_puzzle_index < len(current_room.puzzles):
            # Send the next puzzle
            await ctx.send(current_room.puzzles[current_puzzle_index].question)
        else:
            await ctx.send('Congratulations! You have solved all the puzzles!')
            current_room = None  # Reset the game
            current_puzzle_index = 0
    else:
        await ctx.send('Incorrect. Try again!')
        await ctx.send("If you need help, type `!clue` for a hint!")

# Create a bot command to request a clue
@bot.command()
async def clue(ctx):
    global current_room, current_puzzle_index
    if current_room is None:
        await ctx.send('You need to start a room first using !start [room_name]')
        return

    # Get the current puzzle
    current_puzzle = current_room.puzzles[current_puzzle_index]
    
    # Provide the clue for the current puzzle
    await ctx.send(f"Here’s a clue: {current_puzzle.clue}")

@bot.command()
async def  start(ctx):
    await ctx.send("WELCOME to Escape the Room! 🗝️ Get ready to unlock doors, solve puzzles, and test your wits. Will you escape or be trapped forever? The choice is yours!")
    await ctx.send("Here’s the list of mysterious rooms waiting for you to explore: choose wisely, adventurer!")
    for room in rooms:
        await ctx.send(room.name)
    await ctx.send("Ready for adventure? Use !enter [room_name] to step into the unknown and uncover hidden secrets!")


# Run the bot
bot.run(os.getenv('TOKEN'))
