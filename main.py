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
intents.message_content = True

# Create the bot instance with command prefix and intents
bot = commands.Bot(command_prefix='!', intents=intents)

# Step 7: Create 'players' table if it doesn't already exist
def create_table():
    conn = sqlite3.connect('game_data.db')
    c = conn.cursor()
    # Add the 'inventory' column to the 'players' table
    c.execute('ALTER TABLE players ADD COLUMN inventory TEXT;')
    print("Column 'inventory' added successfully.")
    c.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id TEXT PRIMARY KEY,
            score INTEGER,
            attempts INTEGER,
            solved BOOLEAN,
            inventory TEXT
        )
    ''')
    conn.commit()
    conn.close()

create_table()

# Define a Room class
class Room:
    def __init__(self, name, description, puzzles, difficulty='medium'):
        self.name = name
        self.description = description
        self.puzzles = puzzles
        self.difficulty = difficulty

# Define a Puzzle class
class Puzzle:
    def __init__(self, question, answer, clue):
        self.question = question
        self.answer = answer
        self.clue = clue

# Create new puzzles
puzzle1 = Puzzle('I am a sequence of digits, but I only know 0s and 1s. When you add my values together, you get a perfect square. What am I?', '10000', 'Think about numbers that computers love to talk in!')
puzzle2 = Puzzle('I am a 7-bit binary number. When my digits are interpreted as a decimal number, they represent a prime number.', '0000100', 'Look for a binary sequence that translates to a symbol.')
puzzle3 = Puzzle('I am a binary number that is 8 bits long...', '00100111', 'Consider how many days are in a standard year and how that might be represented in binary.')

# Create new room
room1 = Room('Cipher Chamber', 'Solve puzzles related to binary', [puzzle1, puzzle2, puzzle3], difficulty='easy')

rooms = [room1]

# Variables to track game state
current_room = None
current_puzzle_index = 0
TIME_LIMIT = 160

# Step 8: Store player data to database upon room entry
@bot.command()
async def enter(ctx, *, room_name: str):
    global current_room, current_puzzle_index
    player_id = str(ctx.author.id)

    conn = sqlite3.connect('game_data.db')
    c = conn.cursor()

    # Check if the player is already in the database
    player = c.execute('SELECT * FROM players WHERE id = ?', (player_id,)).fetchone()
    if player is None:
        c.execute('INSERT INTO players (id, score, attempts, solved, inventory) VALUES (?, ?, ?, ?, ?)', (player_id, 100, 0, False, ""))
        conn.commit()

    current_room = None
    current_puzzle_index = 0
    room_name = room_name.strip().lower()

    for r in rooms:
        if r.name.lower() == room_name:
            current_room = r
            await ctx.send(f'Welcome to {r.name}! {r.difficulty.capitalize()} difficulty.')
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
            await ctx.send(f"⏰ Time's up! The answer was {r.puzzles[current_puzzle_index].answer}.")
            break
    else:
        await ctx.send('Room not found.')

    conn.close()

# Command to submit an answer
@bot.command()
async def answer(ctx, *, user_answer: str):
    global current_room, current_puzzle_index
    if current_room is None:
        await ctx.send('You need to start a room first using !enter [room_name]')
        return

    current_puzzle = current_room.puzzles[current_puzzle_index]
    player_id = str(ctx.author.id)

    conn = sqlite3.connect('game_data.db')
    c = conn.cursor()

    if user_answer.lower() == current_puzzle.answer.lower():
        c.execute('UPDATE players SET solved = ? WHERE id = ?', (True, player_id))
        conn.commit()

        # Update score
        c.execute('UPDATE players SET score = score + 10 WHERE id = ?', (player_id,))
        conn.commit()

        await ctx.send('Correct! 🎉')
        current_puzzle_index += 1

        if current_puzzle_index < len(current_room.puzzles):
            await ctx.send(current_room.puzzles[current_puzzle_index].question)
        else:
            await ctx.send('Congratulations! You solved all the puzzles! 🎉')
            current_room = None
            current_puzzle_index = 0
    else:
        await ctx.send('Incorrect. Try again! 💡')
        await ctx.send("If you need help, type `!clue` for a hint!")

    conn.close()

# Command to request a clue
@bot.command()
async def clue(ctx):
    global current_room, current_puzzle_index
    if current_room is None:
        await ctx.send('You need to start a room first using !enter [room_name]')
        return

    current_puzzle = current_room.puzzles[current_puzzle_index]
    await ctx.send(f"Here’s a clue: {current_puzzle.clue}")

# Command to check inventory
@bot.command()
async def inventory(ctx):
    player_id = str(ctx.author.id)
    
    conn = sqlite3.connect('game_data.db')
    c = conn.cursor()

    player = c.execute('SELECT inventory FROM players WHERE id = ?', (player_id,)).fetchone()
    if player and player[0]:
        await ctx.send(f"Your inventory: {player[0]}")
    else:
        await ctx.send("Your inventory is empty.")

    conn.close()

# Game start command
@bot.command()
async def start(ctx):
    await ctx.send("WELCOME to Escape the Room! 🗝️ Unlock doors, solve puzzles, and test your wits.")
    await ctx.send("Here’s the list of rooms you can explore:")
    for room in rooms:
        await ctx.send(f"{room.name} (Difficulty: {room.difficulty})")
    await ctx.send("Ready? Use !enter [room_name] to start!")

# Rank command with leaderboard
@bot.command()
async def rank(ctx):
    try:
        conn = sqlite3.connect('game_data.db')
        c = conn.cursor()

        c.execute('SELECT id, score FROM players ORDER BY score DESC')
        rows = c.fetchall()

        conn.close()

        if rows:
            leaderboard = "🏆 **Leaderboard** 🏆\n\n"
            for idx, row in enumerate(rows):
                player_id, score = row
                member = await bot.fetch_user(player_id)
                leaderboard += f"**{idx + 1}. {member.name}** - {score} points\n"
            await ctx.send(leaderboard)
        else:
            await ctx.send("No players found in the ranking.")
    except sqlite3.Error as e:
        await ctx.send(f"An error occurred: {e}")

# Custom help command
bot.remove_command('help')

@bot.command()
async def help(ctx):
    help_message = """
    **Escape the Room - Command List** 🗝️

    **!start** - Start the game and see available rooms.
    **!enter [room_name]** - Enter a specific room by its name.
    **!answer [your_answer]** - Submit an answer to the current puzzle.
    **!clue** - Get a clue for the current puzzle (if you're stuck).
    **!inventory** - Check your current inventory.
    **!rank** - See the player leaderboard (ranked by score).
    **!help** - Show this help message.

    Example usage:
    - `!enter Cipher Chamber`
    - `!answer 10000`
    - `!clue`
    
    Good luck! 🧠💡
    """
    await ctx.send(help_message)

# Run the bot
bot.run(os.getenv('TOKEN'))
