#======================================================================
# Tandrew-Bot
# The bot will use the first text channel in the server as its
# default channel for sending birthday notifications
#======================================================================
import environment # Module that contains several environment dependent constants
import discord
from discord.ext import commands
from collections import deque
from datetime import date
from Cogs import music_cog
from Cogs import rss
from os import environ
from os import system
from os import listdir
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

loop = asyncio.get_event_loop()
bot = commands.Bot(command_prefix=">")
bdays = {} # Store birthdays as list of linked lists
today = date.today()
channel = {} # Default channel for bot messages
changesMade = False
wedVideos = [] # List of video ID"s for Wednesday videos
wolfClient = wolframalpha.Client(environ.get("WOLFRAM_TOKEN"))
tunaFiles = listdir(environment.TUNA)
drawingPosted = False # Has a drawing already been posted today
tunaChannels = {}
weeklyDrawings = False # Flag to toggle weekly drawing posts

async def checkDate(): # Simple background process to continually check the date
    global today
    global bot
    today = date.today()
    while not bot.is_ready():
        await asyncio.sleep(30) # Wait for the bot to properly intialize
    for g in bot.guilds:
        for person in bdays[g.name][today.month - 1]: # Check everyone who has a birthday this month
            if int(person.day) == today.day:
                await channel[g.name].send("@everyone It\'s {}\'s birthday today!".format(person.name))
            elif int(person.day) - today.day <= 1 and int(person.day) > today.day:
                await channel[g.name].send("{}\'s birthday is coming up soon! ({}/{})".format(person.name, person.month, person.day))
    try: # Set status depending on if it is a Wednesday or not
        if today.weekday() == 2:
            if bot is not None: 
                await bot.change_presence(activity=discord.Game("It is Wednesday my dudes!"))
            # with open(environment.WED_FROG, "rb") as icon:
        #         if bot is not None: 
        #             await bot.user.edit(avatar=icon.read()) # Change profile picture for Wednesdays
        # else:
        #     with open(environment.PROFILE_IMG, "rb") as icon:
        #         if bot is not None: 
        #             await bot.user.edit(avatar=icon.read())
    except:
        print("Tried to change avatar too often.")
    while True:
        print("Checking the date...")
        if weeklyDrawings and not drawingPosted and today.weekday() == 3: # Post a drawing on Thursday
            filename = environment.TUNA + "/" + choice(tunaFiles)
            file = discord.File(filename)
            for g, ch in tunaChannels.items():
                await ch.send(file=file)
            drawingPosted = True
        elif today.weekday() != 3: # Reset drawingPosted if no longer Thursday
            drawingPosted = False
        try: # Check birthdays on date change
            if date.today().weekday() != today.weekday():
                print("Changing the date...")
                today = date.today()
                for g in bot.guilds:
                    for person in bdays[g.name][today.month - 1]: # Check everyone who has a birthday this month
                        if int(person.day) == today.day:
                            await channel[g.name].send("@everyone It\'s {}\'s birthday today!".format(person.name))
                        elif int(person.day) - today.day <= 1 and int(person.day) > today.day:
                            await channel[g.name].send("{}\'s birthday is coming up soon! ({}/{})".format(person.name, person.month, person.day))
                if today.weekday() == 2:
                    if bot is not None: 
                        await bot.change_presence(activity=discord.Game("It is Wednesday my dudes!"))
                    # with open(environment.WED_FROG, "rb") as icon:
                    #     if bot is not None: 
                    #         await bot.user.edit(avatar=icon.read()) # Change profile picture for Wednesdays
                else:
                    await bot.change_presence(activity=None)
                    # with open(environment.PROFILE_IMG, "rb") as icon:
                    #     if bot is not None: 
                    #         await bot.user.edit(avatar=icon.read())
        except:
            print("Tried to change avatar too often.")
        await asyncio.sleep(1800)

# Background process for RSS functionality
async def rssDaemon():
    while not bot.is_ready():
        await asyncio.sleep(30) # Wait for bot to initialize
    await rss.loadFiles(bot)
    while True:
        await rss.getFeed()
        await rss.postFeed()
        await asyncio.sleep(600) # Update feed every 10 mins

@bot.event
async def on_ready():
    global channel
    for g in bot.guilds:
        if g.text_channels:
            channel[g.name] = g.text_channels[0]
    print("We have logged in as {0.user}".format(bot))
    print("Today\'s date: {}/{}".format(today.month, today.day))
    with open("./bdays.txt", "r") as bdaysFile:
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
    with open("./tunachannels.txt", "r") as f:
        for line in f:
            line.strip("\n")
            tokens = line.split("/")
            guild = None
            for g in bot.guilds:
                if tokens[0] == g.name:
                    guild = g
                    break
            if guild is None:
                print("Warning: no guild of name {}\n".format(tokens[0]))
            elif len(tokens) < 2:
                print("Warning: no channel given for guild {}\n".format(tokens[0]))
            elif guild and int(tokens[1]) >= 0 and int(tokens[1]) < len(guild.text_channels):
                tunaChannels[guild.name] = guild.text_channels[int(tokens[1])]
            else:
                print("Warning: invalid rss channel index for {}\n".format(tokens[0]))
    print("Tuna channels loaded")
    print("Ready")

@bot.command(name="tunatest") # For debugging
async def _tunatest(ctx):
    filename = environment.TUNA + "/" + choice(tunaFiles)
    file = discord.File(filename)
    await ctx.send( file=file)

@bot.command(name="toggletuna")
async def _toggletuna(ctx):
    global weeklyDrawings
    weeklyDrawings = not weeklyDrawings
    if weeklyDrawings:
        await ctx.send("Weekly drawings are now **Enabled**")
    else:
        await ctx.send("Weekly drawings are now **Disabled**")

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
        with open("./bdays.txt", "w") as outFile:
            outFile.write("")
            for g in bot.guilds:
                for queue in bdays[g.name]:
                    for b in queue:
                        outFile.write("{}/{}/{}/{}\n".format(b.name, b.month, b.day, g.name))
        print("Success")
    await music_cog.logoutMusic()
    await rss.saveChanges()
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
async def _commands(ctx, cog=""):
    result = "```\n"
    if cog.lower() == "default": # Default birthday bot commands
        result += "echo <string>: Prints the string into chat\n"
        result += "quickmafs <expression>: Evaluate and print the expression (just a wrapper for qalc)\n"
        result += "addbday <name> <month> <day>: Adds the specified birthday into the birthday list\n"
        result += "removebday <name> <month> <day>: Removes the specified birthday from the list\n"
        result += "initbdays: Resets the birthday list for this server\n"
        result += "listbdays: Prints all birthdays into chat\n"
        result += "qingwen <string>: Send Wolfram query\n"
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
    elif cog.lower() == "rss": # RSS cog commands
        result += "addrss <link>: Add a new url to the RSS listener\n"
        result += "setrsschan <index>: Set the channel RSS feeds are posted to\n"
        result += "listrss: List the current RSS feed links\n"
        result += "saverss: Serialize any changes\n"
    else: # Invalid cog name
        result += "Available cogs:\n"
        result += "default\n"
        result += "music\n"
        result += "rss\n"
        result += "\nUse >commands <cog_name> to view the commands associated with the cog\n"
    result += "```"
    await ctx.send(result)
    
@bot.command(name="hongkong")
async def _hongkong(ctx):
    await ctx.send("Fuck Hong Kong\nhttps://www.scmp.com/comment/opinion/article/3032041/hong-kongs-hatred-mainlanders-feeds-xenophobic-undercurrents-its")

@bot.command(name="qingwen") # Interact with the chatbot neural network
async def _qingwen(ctx, *, args):
    if "japan" in args.lower():
        await ctx.send("Never forget national humiliation.")
    else:
            result = wolfClient.query(args)
            for pod in result.pods:
                try:
                    await ctx.send(pod.text)
                    await ctx.send("---")
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
    if not message.author.bot: # Don't reply to other bots including self
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

def main():
    global bot
    global wedVideos
    global loop
    print("Loading Wednesday links...")
    with open("./wednesday.txt") as f: # Load videos used for Wednesday bot functionality
        wedVideos = f.readlines()
    print("Done")
    bot.add_cog(music_cog.music(bot)) # Load music playback features
    bot.add_cog(rss.rss(bot)) # Load RSS features
    # Run the bot in parallel with background processes
    group = asyncio.gather(bot.start(environ.get("BOT_TOKEN")), checkDate(), rssDaemon())
    loop.run_forever()

if __name__ == "__main__":
    main()
