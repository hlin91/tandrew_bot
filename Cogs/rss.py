#======================================================================
# RSS cog
# Adds basic RSS functionality to Tandrew-bot
#======================================================================
import discord
from discord.ext import commands
import feedparser
import os

class rss(commands.Cog):
    channelChanges = false
    urlChanges = false
    urls = [] # List of urls for RSS feeds
    rssChannel = {} # Channel used for posting RSS updates hashed to the server name
    channelIndex = {} # Corresponding indexes for the text channels
    feeds = {} # RSS feed content mapped to each url
    lastPost = {} # ID of last RSS post mapped to each url
    
    def __init__(self, b):
        global rssChannel
        global urls
        global channelIndex
        # Load RSS feed urls from text file
        print("Loading RSS feeds...")
        with open("rssfeeds.txt", "r") as f:
            for line in f:
                line.strip("\n")
                urls.append(line)
        # Load RSS channels from text file
        print("Loading RSS channels...")
        with open("rsschannels.txt", "r") as f:
            for line in f:
                line.strip("\n")
                tokens = line.split("/")
                if tokens[1].isnumeric():
                    channelIndex[tokens[0]] = int(tokens[1])
                    guild = [g for g in b.guilds if tokens[0] == g.name]
                    if guild and int(tokens[1]) >= 0 and int(tokens[1]) < len(g.text_channels):
                        rssChannel[guild[0].name] = guild[0].text_channels[int(tokens[1])]
                    else:
                        print("Warning: invalid rss channel index for {}\n".format(tokens[0]))
                else:
                    print("Warning: ignoring non-numeric rss channel index for {}\n".format(tokens[0]))

    # Serialize any changes
    def saveChanges():
        global channelChanges
        global urlChanges
        if channelChanges:
            print("Saving RSS channels...")
            with open("rsschannels.txt", "w") as f:
                for guild, channel in channelIndex:
                    f.write("{}/{}\n".format(guild, channel))
            channelChanges = false
        if urlChanges:
            with open("rssfeeds.txt", "w") as f:
                for s in urls:
                    f.write(s)
            urlChanges = false
            
    # Get the latest RSS feed
    def getFeed():
        global feeds
        global lastPost
        for s in urls:
            if feeds[s] is not None:
                lastPost[s] = feeds[s][0].id
            feeds[s] = feedparser.parse(s)[0]

    # Convert a post into a formatted message string
    def ptos(post):
        result.append("{}\n".format(post.published))
        result.append("By: {}\n".format(post.author))
        result.append("\n---\n")
        result.append("{}\n".format(post.summary))
        result.append("---\n\n")
        result.append(post.links)
        return result

    # Post the RSS feed to the text channels
    def postFeed():
        for url, post in feeds:
            if post.id != lastPost[url].id:
                for ch in rssChannel:
                    ch.send(ptos(post))
    
    @commands.command()
    # Add a new RSS feed to listen to
    async def addrss(self, ctx, s):
        global urlChanges
        if s not in feeds:
            feeds.append(s)
            urlChanges = true

    @commands.command()
    # Set the channel updates are posted to
    async def setrsschan(self, ctx, n):
        global channelChanges
        global channelIndex
        global rssChannel
        if n.isnumeric() and int(n) >= 0 and int(n) < len(ctx.guild.text_channels):
            channelIndex[ctx.guild.name] = int(n)
            rssChannel[ctx.guild.name] = ctx.guild.text_channels[int(n)]
            channelChanges = true
        else:
            ctx.send("Invalid channel number")
    
    @commands.command()
    # List the current rss feeds
    async def listfeeds(self, ctx):
        result = "```\n"
        for s in urls:
            result.append("{}\n".format(s))
        result.append("```")
        ctx.send(result)
