#======================================================================
# Tandrew-Bot v1.1
# The bot will use the last text channel in the server as its
# default channel for sending birthday notifications
# Now uses Wolfram-API
#======================================================================
import discord
from discord.ext import commands
from collections import deque
from datetime import date
from Cogs import music_cog
from os import system
from random import choice
from time import sleep
from subprocess import check_output
import asyncio
import wolframalpha

class birthday:
    def __init__(self, n, m, d):
        self.name = n
        self.month = m
        self.day = d

bot = commands.Bot(command_prefix=">")
bot.add_cog(music_cog.music(bot))

bdays: dict = {} # Store birthdays as list of linked lists
today = date.today()
channel: dict = {} # Default channel for bot messages
changesMade = False
wedVideos = [] # List of video ID"s for Wednesday videos
with open("wednesday.txt") as f:
    wedVideos = f.readlines()
wolfClient = wolframalpha.Client("<WOLFRAM_API_TOKEN>")

async def checkDate(): # Simple background process to continually check the date
    global today
    global bot
    today = date.today()
    await asyncio.sleep(10) # Wait for the bot to properly intialize
    for g in bot.guilds:
        for person in bdays[g.name][today.month - 1]: # Check everyone who has a birthday this month
            if int(person.day) == today.day:
                await channel[g.name].send("@everyone It\'s {}\'s birthday today!".format(person.name))
            elif int(person.day) - today.day <= 7 and int(person.day) > today.day:
                await channel[g.name].send("{}\'s birthday is coming up soon! ({}/{})".format(person.name, person.month, person.day))
    try:
        if today.weekday() == 2:
            if bot is not None: 
                await bot.change_presence(activity=discord.Game("It is Wednesday my dudes!"))
            with open("wedFrog.jpg", "rb") as icon:
                if bot is not None: 
                    await bot.user.edit(avatar=icon.read()) # Change profile picture for Wednesdays
        else:
            with open("mao.png", "rb") as icon:
                if bot is not None: 
                    await bot.user.edit(avatar=icon.read())
    except:
        print("Tried to change avatar too often.")
    while True:
        print("Checking the date...")
        try:
            if date.today().weekday() != today.weekday():
                print("Changing the date...")
                today = date.today()
                for g in bot.guilds:
                    for person in bdays[g.name][today.month - 1]: # Check everyone who has a birthday this month
                        if int(person.day) == today.day:
                            await channel[g.name].send("@everyone It\'s {}\'s birthday today!".format(person.name))
                        elif int(person.day) - today.day <= 7 and int(person.day) > today.day:
                            await channel[g.name].send("{}\'s birthday is coming up soon! ({}/{})".format(person.name, person.month, person.day))
                if today.weekday() == 2:
                    if bot is not None: 
                        await bot.change_presence(activity=discord.Game("It is Wednesday my dudes!"))
                    with open("wedFrog.jpg", "rb") as icon:
                        if bot is not None: 
                            await bot.user.edit(avatar=icon.read()) # Change profile picture for Wednesdays
                else:
                    await bot.change_presence(activity=None)
                    with open("mao.png", "rb") as icon:
                        if bot is not None: 
                            await bot.user.edit(avatar=icon.read())
        except:
            print("Tried to change avatar too often.")
        await asyncio.sleep(1800)

@bot.event
async def on_ready():
    global channel
    for g in bot.guilds:
        channel[g.name] = g.text_channels[-1]
    print("We have logged in as {0.user}".format(bot))
    print("Today\'s date: {}/{}".format(today.month, today.day))
    with open("bdays.txt", "r") as bdaysFile:
        for g in bot.guilds:
            bdays[g.name] = []
            for i in range (0, 12):
                bdays[g.name].append(deque())
        for line in bdaysFile:
            line = line.strip("\n")
            tokens = line.split("/")
            b = birthday(tokens[0], tokens[1], tokens[2])
            if tokens[3] in bdays:
                bdays[tokens[3]][int(tokens[1], 10) - 1].append(b)
        print("Birthdays successfully loaded")
    print("Ready")

@bot.command(name="hello")
async def _hello(ctx):
    await ctx.send("Da jia hao! Wo shi Tandrew. Hen gao xing ren shi nin.")
        
@bot.command(name="echo") # Simple echo command
async def _echo(ctx, *, arg):
    await ctx.send(arg)

@bot.command(name="logout")
async def _logout(ctx):
    global changesMade
    global bot
    global loop
    await ctx.send("Arrivederci.")
    if changesMade:
        print("Saving birthdays...")
        with open("bdays.txt", "w") as outFile:
            outFile.write("")
            for g in bot.guilds:
                for queue in bdays[g.name]:
                    for b in queue:
                        outFile.write("{}/{}/{}/{}\n".format(b.name, b.month, b.day, g.name))
        print("Success")
    await music_cog.logoutMusic()
    await bot.logout()
    loop.stop()
    print("Done")

@bot.command(name="initbdays") # Initialize birthday list
async def _initbdays(ctx):
    global changesMade
    await ctx.send("Initializing birthday list...")
    for i in range(0, 12):
        bdays[ctx.guild.name][i] = deque()
    changesMade = True
    await ctx.send("Success!")

@bot.command(name="addbday")
async def _addbday(ctx, name, month, day):
    global changesMade
    b = birthday(name, month, day)
    bdays[ctx.guild.name][int(b.month) - 1].append(b)
    changesMade = True
    await ctx.send("{} successfully added.".format(b.name))
    
@bot.command(name="removebday")
async def _removebday(ctx, name, month, day):
    global changesMade
    for b in bdays[ctx.guild.name][int(month) - 1]:
        if b.name == name and b.month == month and b.day == day:
            bdays[ctx.guild.name][int(month) - 1].remove(b)
            changesMade = True
            await ctx.send("{} successfully removed.".format(b.name))
            break
    
@bot.command(name="listbdays")
async def _listbdays(ctx):
    result = "```\n"
    for queue in bdays[ctx.guild.name]:
        for b in queue:
            result += "{} {}/{}\n".format(b.name, b.month, b.day)
    result += "```"
    await ctx.send(result)

@bot.command(name="commands")
async def _commands(ctx, cog="default"):
    result = "```\n"
    if cog.lower() == "default": # Default birthday bot commands
        result += "echo <string>: Prints the string into chat\n"
        result += "quickmafs <expression>: Evaluate and print the expression (just a wrapper for qalc)\n"
        result += "addbday <name> <month> <day>: Adds the specified birthday into the birthday list\n"
        result += "removebday <name> <month> <day>: Removes the specified birthday from the list\n"
        result += "initbdays: Resets the birthday list for this server\n"
        result += "listbdays: Prints all birthdays into chat\n"
        result += "qingwen <string>: Ask Tandrew-Bot questions\n"
    elif cog.lower() == "music": # Music cog commands
        result += "leave: Disconnects the bot from the voice channel\n"
        result += "listqueue: Prints the remaining song queue\n"
        result += "neverforgetti: Never forget National Humiliation\n"
        result += "christmas <option>: Last Christmas\n"
        result += "play <song>: Fetches and enqueues the song from youtube. If the song is the exact name of a locally cached file, it will directly enqueue that file.\n"
        result += "pause: Pauses playback\n"
        result += "start: Starts playback\n"
        result += "resume: Resumes playback\n"
        result += "skip: Skips to the next song in the queue\n"
        result += "playback <file>: Plays a cached file from name\n"
        result += "setvolume <level>: Sets the default volume level for the current song\n"
        result += "setname <name>: Sets the name for the current song\n"
        result += "shuffle: Shuffles the song list and refills the song queue\n"
        result += "summon: Connects the bot to the default voice channel\n"
        result += "volume [<level>]: Sets the default volume level for the session. Prints the current volume if no arguments are passed\n"
    else: # Invalid cog name
        result += "Available cogs:\n"
        result += "music\n"
    result += "```"
    await ctx.send(result)
    
@bot.command(name="hongkong")
async def _hongkong(ctx):
    await ctx.send("https://www.scmp.com/comment/opinion/article/3032041/hong-kongs-hatred-mainlanders-feeds-xenophobic-undercurrents-its")

@bot.command(name="qingwen") # Interact with the chatbot neural network
async def _qingwen(ctx, *, args):
    if "japan" in args.lower():
        await ctx.send("Never forget national humiliation.")
    else:
            result = wolfClient.query(args)
            for pod in result.pods:
                try:
                    await ctx.send(pod.text)
                    await ctx.send("=============================================================================")
                except:
                    pass

@bot.command(name="quickmafs")
async def _quickmafs(ctx, *, args): # Pass the arguments to qalc and print the result
    try:
        result = str(check_output(["qalc {}".format(args)], shell=True))[2:-3]
    except:
        result = "Invalid syntax."
    await ctx.send(result)
    
@bot.event
async def on_message(message): # Override the on_message event to account for Wednesday functionality
    if not message.author.bot: # Don"t reply to other bots including self
        m = message.content.lower()
        if "my dude" in m: # Being addressed
            if "wednesday" in m: # Asking if it is wednesday
                if today.weekday() == 2: # It is wednesday
                    await message.channel.send("{}, It is Wednesday my dude!\neeeeeeeAAAAAhhhhhahahHAHahAHHAhAHHAhHAhAhHAhHHAAAAAAAAAA\n\n https://www.youtube.com/watch?v={}".format(message.author.mention, choice(wedVideos)))
                else:
                    await message.channel.send("{}, It is NOT Wednesday my dude :(".format(message.author.mention))
            if "video" in m: # Asking for a video
                await message.channel.send("{}, https://www.youtube.com/watch?v={}".format(message.author.mention, choice(wedVideos)))
        else:
            await bot.process_commands(message)

# Run the bot in parallel with checkDate using asyncio
loop = asyncio.get_event_loop()
group = asyncio.gather(bot.start("<BOT_TOKEN_HERE>"), checkDate())
loop.run_forever()
