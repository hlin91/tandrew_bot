#======================================================================
# RSS cog
# Adds basic RSS functionality to Tandrew-bot
#======================================================================
import discord
from discord.ext import commands
import feedparser
import os
import dateutil.parser

channelChanges = False
urlChanges = False
urls = [] # List of urls for RSS feeds
rssChannel = {} # Channel used for posting RSS updates hashed to the server name
channelIndex = {} # Corresponding indexes for the text channels
feeds = {} # RSS feed content mapped to each url
lastPost = {} # ID of last RSS post mapped to each url

# Get the latest RSS feed
async def getFeed():
    global feeds
    global lastPost
    print("Getting RSS feed...")
    for s in urls:
        if s in feeds: # If this is not the first batch
            lastPost[s] = feeds[s] # Save it as the last batch
        if feedparser.parse(s).entries:
            feeds[s] = feedparser.parse(s).entries

# Convert a post into a formatted message string
def ptos(post):
    result = "<a:newspaper:793257230618460160> **| Hot off the press**\n\n"
    pic = None
    result += "**"
    try:
        result += "{}".format(post.title)
    except:
        pass
    result += "**\n"
    try:
        date = dateutil.parser.isoparse(post.date)
        result += "{}-{}-{}, {}:{}\n".format(date.month, date.day, date.year, format(date.hour, "02"), format(date.minute, "02"))
    except:
        pass
    try:
        result += "By: {}\n".format(post.author)
    except:
        pass
    result += "\n---\n"
    try:
        result += "{}\n".format(post.summary)
    except:
        pass
    result += "---\n\n"
    try:
        result += "{}\n".format(post.link)
    except:
        pass
    try:
        # Extract the first image from the <a> element
        tokens = post.content[0]["value"].split(" ")
        for t in tokens:
            temp = t.split("=")
            if temp[0] == "href" or temp[0] == "src":
                link = temp[1].strip('"')
                if link.endswith(".jpg") or link.endswith(".png"):
                    pic = link
                    break
    except:
        return result, None
    return result, pic

# Post the RSS feed to the text channels
async def postFeed():
    print("Posting RSS feed...")
    for url, posts in feeds.items():
        if url in lastPost: # If this is not the first batch of posts retrieved
            for post in posts:
                if post not in lastPost[url]:
                    for g, ch in rssChannel.items():
                        s, pic = ptos(post)
                        if pic is None:
                            await ch.send(s)
                        else:
                            try:
                                e = discord.Embed(url=pic)
                                e.set_image(url=pic)
                                await ch.send(content=s, embed=e)
                            except:
                                await ch.send(s)
                
# Serialize any changes
async def saveChanges():
    global channelChanges
    global urlChanges
    if channelChanges:
        print("Saving RSS channels...")
        with open("rsschannels.txt", "w") as f:
            for guild, channel in channelIndex.items():
                f.write("{}/{}\n".format(guild, channel))
        channelChanges = False
    if urlChanges:
        with open("rssfeeds.txt", "w") as f:
            for s in urls:
                f.write("{}\n".format(s))
        urlChanges = False

def loadFiles(b): # Call this once the bot has been fully initialized
    global rssChannel
    global urls
    global channelIndex
    # Load RSS feed urls from text file
    print("Loading RSS feeds...")
    with open("./rssfeeds.txt", "r") as f:
        for line in f:
            line.strip("\n")
            if line:
                urls.append(line)
    print("Done")
    # Load RSS channels from text file
    print("Loading RSS channels...")
    with open("./rsschannels.txt", "r") as f:
        for line in f:
            line.strip("\n")
            tokens = line.split("/")
            guild = None
            for g in b.guilds:
                if tokens[0] == g.name:
                    guild = g
                    break
            if guild is None:
                print("Warning: no guild of name {}\n".format(tokens[0]))
            elif guild and int(tokens[1]) >= 0 and int(tokens[1]) < len(guild.text_channels):
                channelIndex[tokens[0]] = int(tokens[1])
                rssChannel[guild.name] = guild.text_channels[int(tokens[1])]
            else:
                print("Warning: invalid rss channel index for {}\n".format(tokens[0]))
    print("Done")

class rss(commands.Cog):    
    def __init__(self, b):
        pass

    @commands.command()
    # Add a new RSS feed to listen to
    async def addrss(self, ctx, s):
        global urlChanges
        if s not in urls:
            urls.append(s)
            urlChanges = True

    @commands.command()
    # Set the channel updates are posted to
    async def setrsschan(self, ctx, n):
        global channelChanges
        global channelIndex
        global rssChannel
        if n.isnumeric() and int(n) >= 0 and int(n) < len(ctx.guild.text_channels):
            channelIndex[ctx.guild.name] = int(n)
            rssChannel[ctx.guild.name] = ctx.guild.text_channels[int(n)]
            channelChanges = True
        else:
            await ctx.send("Invalid channel number.")
    
    @commands.command()
    # List the current rss feeds
    async def listrss(self, ctx):
        result = "```\n"
        for s in urls:
            result += "{}\n".format(s)
        result += "```"
        await ctx.send(result)

    @commands.command()
    # For testing
    async def testfeed(self, ctx):
        await getFeed()
        for key, val in feeds.items():
            await ctx.send(ptos(val))

    @commands.command()
    async def saverss(self, ctx):
        await saveChanges()
        await ctx.send("Done.")
