import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio
import sqlite3

# Load environment variables from the .env file
load_dotenv()

# Define the necessary intents
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True  # Enable to receive message content

# Create the bot instance with command prefix and intents
bot = commands.Bot(command_prefix='!', intents=intents)

# Step 6: Connect to SQLite Database
# SQLite will automatically create the 'game_data.db' file if it does not exist.
conn = sqlite3.connect('game_data.db')
c = conn.cursor()

# Step 7: Create 'players' table if it doesn't already exist
# This stores player ID, score, attempts, and whether they've solved the puzzle.
c.execute('''
    CREATE TABLE IF NOT EXISTS players (
        id TEXT PRIMARY KEY,
        score INTEGER,
        attempts INTEGER,
        solved BOOLEAN
    )
''')
conn.commit()

# Define a Room class
class Room:
    def __init__(self, name, description, puzzles):
        self.name = name
        self.description = description
        self.puzzles = puzzles

# Define a Puzzle class
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
TIME_LIMIT = 160

# Step 8: Store player data to database upon room entry
@bot.command()
async def enter(ctx, *, room_name: str):
    global current_room, current_puzzle_index
    player_id = str(ctx.author.id)  # Get player's Discord ID
    
    # Check if the player is already in the database
    player = c.execute('SELECT * FROM players WHERE id = ?', (player_id,)).fetchone()
    if player is None:
        # If player not in database, add with default score and attempts
        c.execute('INSERT INTO players (id, score, attempts, solved) VALUES (?, ?, ?, ?)', (player_id, 100, 0, False))
        conn.commit()
    
    current_room = None
    current_puzzle_index = 0
    room_name = room_name.strip().lower()  # Normalize and strip whitespace
    for r in rooms:
        if r.name.lower() == room_name:
            current_room = r
            await ctx.send(f'Welcome to {r.name}!')
            await ctx.send(r.description)

            # Send the first puzzle
            await ctx.send(r.puzzles[current_puzzle_index].question)
            await ctx.send(f"\nYou have {TIME_LIMIT} seconds to solve it!")

            # Start the countdown timer
            time_remaining = TIME_LIMIT
            message = await ctx.send(f"⏳ Time remaining: {time_remaining} seconds")
            while time_remaining > 0:
                await asyncio.sleep(1)
                time_remaining -= 1
                await message.edit(content=f"⏳ Time remaining: {time_remaining} seconds")
            await ctx.send(f"⏰ Time's up! The answer to {r.puzzles[current_puzzle_index].question} was {r.puzzles[current_puzzle_index].answer}.")
            break
    else:
        await ctx.send('Room not found.')

# Command to submit an answer
@bot.command()
async def answer(ctx, *, user_answer: str):
    global current_room, current_puzzle_index
    if current_room is None:
        await ctx.send('You need to start a room first using !start [room_name]')
        return

    # Get the current puzzle
    current_puzzle = current_room.puzzles[current_puzzle_index]
    player_id = str(ctx.author.id)

    if user_answer.lower() == current_puzzle.answer.lower():
        # Update player's progress in the database
        c.execute('UPDATE players SET solved = ? WHERE id = ?', (True, player_id))
        conn.commit()
        await ctx.send('Correct!')
        current_puzzle_index += 1  # Move to the next puzzle

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

# Command to request a clue
@bot.command()
async def clue(ctx):
    global current_room, current_puzzle_index
    if current_room is None:
        await ctx.send('You need to start a room first using !start [room_name]')
        return

    current_puzzle = current_room.puzzles[current_puzzle_index]
    await ctx.send(f"Here’s a clue: {current_puzzle.clue}")

# Game start command
@bot.command()
async def start(ctx):
    await ctx.send("WELCOME to Escape the Room! 🗝️ Get ready to unlock doors, solve puzzles, and test your wits. Will you escape or be trapped forever? The choice is yours!")
    await ctx.send("Here’s the list of mysterious rooms waiting for you to explore:")
    for room in rooms:
        await ctx.send(room.name)
    await ctx.send("Ready? Use !enter [room_name] to start!")

    
@bot.command()
async def rank(ctx):
    try:
        # Connect to the SQLite Database
        conn = sqlite3.connect('game_data.db')
        c = conn.cursor()

        # Query the players table and get all players sorted by score (descending)
        c.execute('SELECT id, score FROM players ORDER BY score DESC')
        rows = c.fetchall()

        # Close the database connection
        conn.close()

        if rows:
            # Create a leaderboard message
            leaderboard = "🏆 **Leaderboard** 🏆\n\n"
            for idx, row in enumerate(rows):
                player_id, score = row
                member = await bot.fetch_user(player_id)  # Fetch Discord user by ID
                leaderboard += f"**{idx + 1}. {member.name}** - {score} points\n"

            # Send the leaderboard
            await ctx.send(leaderboard)
        else:
            await ctx.send("No players found in the ranking.")
    except sqlite3.Error as e:
        await ctx.send(f"An error occurred while fetching the rankings: {e}")

# Run the bot
bot.run(os.getenv('TOKEN'))
