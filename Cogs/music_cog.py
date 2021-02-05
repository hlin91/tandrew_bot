#======================================================================
# Music playback cog for Tandrew-bot
# The code is messy but its python so whatevs
# TODO: Adjust representation of voice channels to support simultaneous
# playback in multiple servers
#======================================================================
import discord
from discord.ext import commands
from collections import deque
import os
from random import shuffle
import asyncio
from youtube_dl import YoutubeDL

class song: # Simple struct to hold metadata about songs
    name = None
    vol = None
    def __init__(self, n, v: int = 0.5):
        self.name = n
        self.vol = v
#======================================================================
# Global Data
#======================================================================
vChannelID = {} # The voice channel ID's of each server hashed by guild name
voice = None # The voice client
volume = 0.5 # Default volume level
sourcePath = "./Cache" # Default source directory
sourceFile = None # Source audio file
songList = os.listdir(sourcePath) # List of cached songs
for index, item in enumerate(songList): # Remove README file from song list
    if item == "README.md":
        del songList[index]
songQueue = None # Queue of songs to play
currentSong = None # Current song playing
nextSong = None # Song explicitly queued up to play next by user
infoDict = {} # Dictionary of song metadata hashed to the filename
changesMade = False # Are there changes that need to be serialized

downloaded = False # Did youtube-dl successfully download a file
def myHook(d): # Progress hook for youtube-dl
    global infoDict
    global changesMade
    global nextSong
    global downloaded
    if d["status"] == "finished":
        if d["filename"] not in infoDict:
            changesMade = True
            downloaded = True
            name = d["filename"][:-17]
            nextSong = d["filename"]
            infoDict[nextSong] = song(name, volume)
            
            
youtubeOpts ={ # Options for youtube-dl
    "default_search": "ytsearch1",
    "format": "bestaudio/best",
#    "postprocessors": [{
#            "key": "FFmpegExtractAudio",
#            "preferredcodec": "mp3",
#            "preferredquality": "192",
#        }],
    "fixup": "detect_or_warn",
    "prefer_ffmpeg": True,
    "progress_hooks": [myHook],
    "download_archive": "./yt_archive.txt"
}
ydl = YoutubeDL(youtubeOpts) # The youtube_dl downloader class

#======================================================================
# Helper Functions
#======================================================================
def fetch(query): # Helper function to download from youtube
    global ydl
    global downloaded
    ydl.download([query])
    if downloaded:
        os.rename("{}".format(nextSong), "{}/{}".format(sourcePath, nextSong)) # Move to Cache folder
        songList.append(nextSong)
    downloaded = False

def clearStatus(error): # Clear bot status and current song
    global bot
    global sourceFile
    global currentSong
    sourceFile = None
    currentSong = None
    coro = bot.change_presence(activity=None)
    fut = asyncio.run_coroutine_threadsafe(coro, bot.loop)
    fut.result()
    
def setStatus(status): # Sets bot status to the input string
    global bot
    coro = bot.change_presence(activity=discord.Game(status))
    fut = asyncio.run_coroutine_threadsafe(coro, bot.loop)
    fut.result()

def playNext(error): # Recursively play through the song queue
        global songQueue
        global infoDict
        global currentSong
        global voice
        global sourceFile
        global changesMade
        if songQueue:
            currentSong = songQueue.popleft()
            if currentSong not in infoDict:
                changesMade = True
                infoDict[currentSong] = song(currentSong, volume)
            i = infoDict[currentSong]
            setStatus(i.name)
            sourceFile = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(sourcePath + "/" + currentSong), i.vol)
            voice.play(sourceFile, after=playNext)
        else: # Queue is exhausted
            print("Queue is empty")
            clearStatus(None)

def repeat(error): # Continuously repeat the current song (currently only intended to be used with Last Christmas)
    global voice
    global sourceFile
    if currentSong is not None:
        sourceFile = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(currentSong), volume)
        voice.play(sourceFile, after=repeat)
        
def saveChanges():
    global changesMade
    if changesMade:
        with open("./playlist.txt", "w") as f:
            for name in songList:
                if name in infoDict:
                    i = infoDict[name]
                    f.write("{}/{}/{}\n".format(name, i.name, i.vol))
    changesMade = False
        
async def logoutMusic(): # Save changes made when shutting down the music cog
    global songList
    global sourcePath
    global infoDict
    global changesMade
    if changesMade:
        saveChanges()

#======================================================================
# Music Cog
#======================================================================
class music(commands.Cog):
    vChannel = None # The voice channel
    
    def __init__(self, b):
        global songList
        global songQueue
        global infoDict
        global bot
        self.bot = b
        bot = b
        self.last_member = None
        print("Initializing playlist...")
        for index, s in  enumerate(songList):
            if s.startswith("."): # Remove mac system files
                del songList[index]
        shuffle(songList)
        print("Done")
        songQueue = deque(songList)
        print("Loading playlist file...")
        with open("./playlist.txt", "r") as f:
            for line in f:
                tokens = line.split("/")
                if len(tokens) == 3:
                    infoDict[tokens[0]] = song(tokens[1], float(tokens[2]))
        print("Done")

    async def playHelp(self): # Helper to start playback of song queue within class member functions
        global voice
        global songQueue
        global infoDict
        global changesMade
        global currentSong
        global sourceFile
        if songQueue:
            fileName = songQueue.popleft()
            if fileName in infoDict:
                sourceFile = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(sourcePath + "/" + fileName), infoDict[fileName].vol)
            else:
                sourceFile = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(sourcePath + "/" + fileName), volume)
            currentSong = fileName
            if fileName not in infoDict:
                changesMade = True
                infoDict[fileName] = song(fileName, volume)
            await self.bot.change_presence(activity=discord.Game(infoDict[fileName].name))
            voice.play(sourceFile, after=playNext)
    
    @commands.command()
    async def summon(self, ctx, arg: int=0): # Connect the bot to the specified voice channel
        global voice
        global vChannelID
        if not vChannelID: # Get the voice channel ID's if necessary
                print("Getting voice channels...")
                for g in bot.guilds:
                    vChannelID[g.name] = []
                    for c in g.voice_channels:
                        vChannelID[g.name].append(c.id)
        if arg < 0 or arg > (len(vChannelID[ctx.guild.name])) - 1:
            await ctx.send("Invalid argument.")
        elif voice is None:
            self.vChannel = self.bot.get_channel(vChannelID[ctx.guild.name][arg])
            voice = await self.vChannel.connect()
            # if len(self.vChannel.members) > 1: # Start playing if users are in the voice channel upon summoning
            #     await self.playHelp()
        else:
            await ctx.send("Already in a voice channel.")
    
    @commands.command()
    async def leave(self, ctx): # Disconnect the bot from the voice channel
        global voice
        if voice is None:
            await ctx.send("Currently not in a voice channel.")
        else: 
            await voice.disconnect()
            voice = None
    
    @commands.command()
    async def playback(self, ctx, fileName): # Play a cached file by file name (mainly for testing)
        global voice
        if voice is None:
            await ctx.send("Currently not in a voice channel.")
        else:
            try:
                global volume
                global infoDict
                global currentSong
                global changesMade
                global sourcePath
                global sourceFile
                if fileName in infoDict:
                    sourceFile = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(sourcePath + "/" + fileName), infoDict[fileName].vol)
                else:
                    sourceFile = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(sourcePath + "/" + fileName), volume)
            except:
                await ctx.send("Could not open file")
                return
            currentSong = fileName
            if fileName not in infoDict:
                changesMade = True
                infoDict[fileName] = song(fileName, volume)
            await self.bot.change_presence(activity=discord.Game(infoDict[fileName].name))
            voice.play(sourceFile, after=clearStatus)
            
    @commands.command()
    async def neverforgetti(self, ctx): # Never forget national humiliation
        global voice
        if voice is None:
            await ctx.send("Currently not in a voice channel.")
        else:
            try:
                global currentSong
                global sourceFile
                sourceFile = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio("./anthem.mp3"), volume)
                if voice.is_playing() or voice.is_paused():
                    voice.stop()
                currentSong = "anthem.mp3"
                await self.bot.change_presence(activity=discord.Game("March of the Volunteers"))
                voice.play(sourceFile, after=clearStatus)
            except:
                await ctx.send("Could not open file.")

    @commands.command()
    async def christmas(self, ctx, arg:str=""): # Last Christmas
        global voice
        if voice is None:
            await ctx.send("Currently not in a voice channel.")
        elif voice.is_playing() or voice.is_paused():
            await ctx.send("Player is already playing something else.")
        else:
            try:
                global currentSong
                global sourceFile
                if arg.lower() == "chink":
                    sourceFile = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio("./christmas3.mp3"), volume)
                    currentSong = "christmas3.mp3"
                elif arg.lower() == "jap":
                    sourceFile = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio("./christmas2.mp3"), volume)
                    currentSong = "christmas2.mp3"
                else:
                    sourceFile = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio("./christmas.mp3"), volume)
                    currentSong = "christmas.mp3"
                await self.bot.change_presence(activity=discord.Game("Last Christmas"))
                voice.play(sourceFile, after=repeat)
            except:
                await ctx.send("Could not open file.")
    
    @commands.command()
    async def pause(self, ctx):
        global voice
        if voice is not None and voice.is_playing():
            voice.pause()
    
    @commands.command()
    async def resume(self, ctx):
        global voice
        if voice is not None and voice.is_paused():
            voice.resume()
            
    @commands.command()
    async def volume(self, ctx, v: int = None): # Changes the global volume and current song volume. Prints the current volume if no arguments are passed
        global sourceFile
        global voice
        if v is None and sourceFile is not None:
            await ctx.send("Current volume: {}".format(sourceFile.volume * 100))
        elif v < 0 or v > 100:
            await ctx.send("Volume is in the range [0, 100].")
        else:
            global volume
            volume = v / 100.0
            if voice.is_playing():
                voice.source.volume = v / 100.0
            await ctx.send("Default volume for the session set to {}.".format(v))
            
    @commands.command()
    async def setvolume(self, ctx, v: float): # Changes the default volume of the current song
        global currentSong
        global sourceFile
        global infoDict
        global changesMade
        if v < 0 or v > 100:
            await ctx.send("Volume is in the range [0, 100].")
        elif currentSong is None:
            await ctx.send("No song is currently playing.")
        else:
            infoDict[currentSong].vol = v / 100.0
            changesMade = True
            if voice.is_playing():
                voice.source.volume = v / 100.0
            await ctx.send("Volume for {} successfully set to {}.".format(infoDict[currentSong].name, infoDict[currentSong].vol * 100))
            
    @commands.command()
    async def setname(self, ctx, n): # Set the name of the current song
        global currentSong
        global infoDict
        global changesMade
        if currentSong is not None and currentSong != "anthem.mp3":
            infoDict[currentSong].name = n
            await self.bot.change_presence(activity=discord.Game(n))
            changesMade = True
            await ctx.send("Name successfully changed to {}.".format(n))
        else:
            await ctx.send("Cannot do that right now.")
    
    @commands.command(name="shuffle")
    async def _shuffle(self, ctx): # Shuffle and refill the current song queue
        global songList
        global songQueue
        songList = os.listdir(sourcePath)
        for index, s in  enumerate(songList):
            if s.startswith("._"):
                del songList[index]
        shuffle(songList)
        songQueue = deque(songList)
        for s in songQueue:
            if s not in infoDict:
                infoDict[s] = song(s, volume)
        await ctx.send("Done.")
        
    @commands.command()
    async def listqueue(self, ctx):
        result = "```\n"
        try:
            result += "Now playing: {}\n\n".format(infoDict[currentSong].name)
        except:
            result += "Now playing: {}\n\n".format(currentSong)
        for song in songQueue:
            result += "{}\n".format(infoDict[song].name)
        result += "```"
        await ctx.send(result)
        
    @commands.command()
    async def skip(self, ctx): # Stops playback and plays the next song in the queue if possible
        global voice
        global currentSong
        global songQueue
        if voice is not None and (voice.is_playing() or voice.is_paused()):
            voice.stop()
            
    @commands.command()
    async def start(self, ctx): # Starts queue playback
        global voice
        global songQueue
        if not (voice.is_playing() or voice.is_paused()):
            if not songQueue:
                await ctx.send("The queue is empty.")
            else:
                await self.playHelp()
        else:
            await ctx.send("The player is already playing.")
                
    @commands.command() # Downloads requested song if necessary and emplaces it at the front of the song queue
    async def play(self, ctx, *, args):
        global songQueue
        global voice
        global nextSong
        if not args:
            await ctx.send("Usage: play <song>")
        else:
            q = "".join(args)
            if q in songList: # Query is exactly the name of a local file
                nextSong = q
                songQueue.appendleft(q)
            else: # Fetch and enqueue query from youtube
                fetch(q)
                songQueue.appendleft(nextSong)
            if nextSong is not None:
                await ctx.send("Added `{}` to queue.".format(infoDict[nextSong].name))
            if not (voice.is_playing() or voice.is_paused()):
                await self.playHelp()
                
    @commands.command()
    async def saveChanges(self, ctx):
        if changesMade:
            saveChanges()
            await ctx.send("Changes successfully saved.")
        else:
            await ctx.send("There are no changes to save.")
