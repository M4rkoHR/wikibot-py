import re
import sys
import time
import praw
import json
import TopGG
import signal
import random
import asyncio
import discord
import settings
import eightball
import wikipedia
import threading
import wolframalpha
from time import sleep
import urbandictionary as ud
from datetime import datetime
from discord.ext import commands
from youtube_api import YoutubeDataApi
from db_interface import backup, restore

with open('languages.json', encoding='utf8') as languages_file:
    languages = json.load(languages_file)
token = settings.discordBotToken
reddit = praw.Reddit(client_id=settings.prawClientID,
                     client_secret=settings.prawClientSecret,
                     user_agent=settings.prawUserAgent)
wolfram = wolframalpha.Client(settings.wolframApiKey)
autor = settings.ownerName
banned_subs = settings.bannedSubs
ownerid = settings.ownerID
use_postgres = settings.usePostgres
ytid = settings.youtubeApiKey
use_topgg = settings.useTopGG
if use_topgg:
    topggtoken = settings.TopGGtoken
if use_postgres: restore()
with open('responses.json') as responses_file:
    responses = json.load(responses_file)
ownerdm = None # gets initialized to send messages to the bot owner later
default_lang = "en"
wikipedia_language = {}
message_history = {}
answered = {}
subsettings = {}
userwarns = {}
guild_language = {} #guild language for every server, currently "hr" or "en"
misc={}
intents = discord.Intents(messages=True, guilds=True, members=True)
client = commands.Bot(command_prefix = '?', intents=intents, help_command=None, case_insensitive=True)
default_subreddits = ["dankmemes", "memes", "me_irl", "historymemes", "okbuddyretard", "dogelore", "dankchristianmemes"]
language_not_supported = "That language is not supported yet, you can help translate WikiBot to your language by translating a small number of responses over on https://github.com/M4rkoHR/wikibot-py/blob/main/languages.json"
started=False

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    await client.change_presence(activity=discord.Game(name='wikibot.tech | ?help'))
    global ownerdm
    ownerdm = client.get_user(ownerid)
    try:
        global guild_language
        with open('guild_language.json') as json_file:
            guild_language = json.load(json_file)
        print(guild_language)
        await ownerdm.send('guild_language.json loaded')
        try:
            await ownerdm.send(f'guild_language:\n```{guild_language}```')
        except:
            await ownerdm.send(f'guild_language:\n```file too large```')
    except:
        await ownerdm.send('Exception, generating new guild_language.json')
        for guild in client.guilds:
            if guild.id == 601663624175419412:
                guild_language.update({str(guild.id): "hr"})
            else:
                guild_language.update({str(guild.id): default_lang})
        with open('guild_language.json', 'w') as json_file:
            json.dump(guild_language, json_file)
    try:
        global wikipedia_language
        with open('wikipedia_language.json') as json_file:
            wikipedia_language = json.load(json_file)
        await ownerdm.send('wikipedia_language.json loaded')
        try:
            await ownerdm.send(f'wikipedia_language:\n```{wikipedia_language}```')
        except:
            await ownerdm.send(f'wikipedia_language:\n```file too large```')
    except:
        await ownerdm.send('wikipedia_language.json not found')
    try:
        global subsettings
        with open('subsettings.json') as json_file:
            subsettings = json.load(json_file)
        await ownerdm.send('subsettings.json loaded')
        try:
            await ownerdm.send(f'subsettings:\n```{subsettings}```')
        except:
            await ownerdm.send(f'subsettings:\n```file too large```')
    except:
        await ownerdm.send('subsettings.json not found')
    try:
        global userwarns
        with open('warns.json') as json_file:
            userwarns = json.load(json_file)
        await ownerdm.send('warns.json loaded')
    except:
        await ownerdm.send('warns.json not found')
    try:
        global misc
        with open('misc.json') as json_file:
            misc = json.load(json_file)
        try:
            await ownerdm.send(f'misc:\n```{misc}```')
        except:
            await ownerdm.send(f'misc:\n```file too large```')
    except:
        await ownerdm.send('misc.json not found')
    if use_topgg:
        TopGG.setup(client=client)
        await ownerdm.send('Setting up TopGG cog')
    await ownerdm.send('Done')
    if use_postgres: backup()
    global started
    started=True
    print("Done")


@client.command(brief='Help command')
async def help(ctx, *, command=None):
    embed=discord.Embed(colour=0x0000ff,
                        title="WikiBot Help",
                        description="To know more about each command, type ?help `command`",
                        url="https://wikibot.tech")
    embed.add_field(name="?yt `query`", value="YouTube search", inline=True)
    embed.add_field(name="?wiki `query`", value="Wikipedia search", inline=True)
    embed.add_field(name="?urban|ud `query`", value="Urban Dictionary search", inline=True)
    embed.add_field(name="?wikilang `language`", value="Set Wikipedia language (EN for English, DE for German etc.)", inline=True)
    embed.add_field(name="?8ball `question`", value="Ask Magic 8 Ball a question", inline=True)
    embed.add_field(name="?cp|copypasta `query`", value="Sends a copypasta from r/copypasta", inline=True)
    embed.add_field(name="?hot|meme|reddit `subreddit`", value="Sends an image from the subreddit", inline=True)
    embed.add_field(name="?warn `@user` `reason`", value="Warns user for a given reason", inline=True)
    embed.add_field(name="?warns `@user`", value="Check user's warns (your warns if no user is mentioned)", inline=True)
    embed.add_field(name="?changelang `language`", value="Change bot language to a supported language", inline=True)
    embed.add_field(name="?clearwarns `@user`", value="Clear user's warns", inline=True)
    embed.add_field(name="?lang", value="Check WikiBot language for current server", inline=True)
    embed.add_field(name="?subscribe | subreddit | `subreddit`", value="Add `subreddit` to a list of subscribed subreddits used for an empty `?reddit | hot | meme` command (with no arguments)", inline=True)
    embed.add_field(name="?archivepins|ap `#source-channel` `#target-channel`", value="Archives pins from `#source-channel` into `#target-channel`", inline=True)
    embed.add_field(name="?send `#target-channel` `message`", value="Sends `message` to `#target-channel`", inline=True)
    embed.add_field(name="?ars `keyword`;`response`", value="Bot responds with `response` if message is equal to `keyword` (case insensitive)", inline=True)
    embed.add_field(name="?ard `keyword`;`response`", value="Bot responds with `response` if message contains `keyword` (case insensitive)", inline=True)
    embed.add_field(name="?rrs|rrd `response`", value="Removes a response, ?rrs to remove a static response, ?rrd to remove dynamic one", inline=True)
    embed.add_field(name="?garand", value="Garand ping", inline=True)
    embed.add_field(name="?ping", value="Check latency", inline=True)
    embed.add_field(name="?whoasked", value="Who asked?", inline=True)
    embed.add_field(name="?toggle `feature`", value="Toggle features such as `dadbot`,`repeat` and `wolfram`/`what is`", inline=True)
    embed.set_footer(text="Web Dashboard: https://wikibot.tech")
    await ctx.send(embed=embed)

@client.command(brief='debug command')
async def d(ctx, *, string):
    if ctx.message.author.id != ownerid:
        await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["not_author"].format(author=autor))
        return
    if str(string).lower() == 'backup':
        await ownerdm.send(file=discord.File('guild_language.json'))
        await ownerdm.send(file=discord.File('wikipedia_language.json'))
        await ownerdm.send(file=discord.File('subsettings.json'))
        await ownerdm.send(file=discord.File('warns.json'))
        await ownerdm.send(file=discord.File('responses.json'))
        await ownerdm.send(file=discord.File('misc.json'))
        return
    command = f"{str(string)}"
    await ctx.send(f'{command}')


@client.command(aliases=['youtube'], brief='Searches YouTube for given query and returns link')
async def yt(ctx, *, query):
    yt = YoutubeDataApi(ytid)
    searches = yt.search(str(query), max_results=3)
    result=yt.get_video_metadata(searches[0]["video_id"], part=['id', 'snippet', 'contentDetails', 'statistics'])
    searches.clear()
    del yt
    url = 'https://www.youtube.com/watch?v=' + result["video_id"]
    desc=result["video_description"].split('\n')[0]
    if len(desc)>300:
        desc=desc[:300]+"..."
    embed=discord.Embed(colour=0xff0000,
                        title=result["video_title"],
                        description=desc,
                        url=url)
    embed.set_author(name=result["channel_title"])
    embed.set_thumbnail(url=result["video_thumbnail"])
    embed.add_field(name="Views", value=str(result["video_view_count"]), inline=True)
    embed.add_field(name="Comments", value=str(result["video_comment_count"]), inline=True)
    embed.add_field(name="Duration", value=str(result["duration"])[2:-1].replace("M", ":").replace("H", ":"), inline=True)
    embed.add_field(name="Likes", value=str(result["video_like_count"]), inline=True)
    embed.add_field(name="Dislikes", value=str(result["video_dislike_count"]), inline=True)
    embed.set_footer(text=datetime.utcfromtimestamp(int(result["video_publish_date"])).strftime('%Y-%m-%d %H:%M:%S'))
    await ctx.send(embed=embed)


@client.command(aliases=['wikipedia'], brief='Searches Wikipedia for given query in desired language(?wikilang)', description='Searches Wikipedia for given query in desired language(default english, changed with ?wikilang) and returns 3 sentences from summary')
async def wiki(ctx, *, query):
    global wikipedia_language
    try:
        wikipedia_language = restore(file="wikipedia_language.json")
    except Exception as e:
        await ownerdm.send("Unable to restore Wikipedia languages: \n{exception}".format(exception=e))
        restore()
        try:
            with open('wikipedia_language.json') as json_file:
                wikipedia_language = json.load(json_file)
            await ownerdm.send('wikipedia_language.json loaded')
            await ownerdm.send(f'wikipedia_language:\n```{wikipedia_language}```')
        except:
            await ownerdm.send('wikipedia_language.json not found')
    page=None
    wikipedia.set_lang(str(wikipedia_language.setdefault(str(ctx.message.author.id), guild_language.get(str(ctx.guild.id), "en"))))
    try:
        page=wikipedia.page(wikipedia.search(query)[0])
    except wikipedia.exceptions.DisambiguationError as e:
        counter=0
        while page==None:
            try:
                page=wikipedia.page(e.options[counter])
            except:
                counter+=1
    except IndexError as e:
        await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["wikipedia_page_error"])
        print(e)
        return
    summary=page.summary.split("\n")[0]
    if len(summary)>2048:
        summary=summary[:2045]+"..."
    embed=discord.Embed(colour=0xfefefe,
                        title=page.title,
                        description=summary,
                        url=page.url,)
    embed.set_author(name="Wikipedia",
                    icon_url="https://cdn.discordapp.com/attachments/601676952134221845/799319569025335406/wikipedia.png",
                    url="https://www.wikipedia.org/")
    if page.images:
        embed.set_thumbnail(url=page.images[0])
    await ctx.send(embed=embed)


@client.command(brief='Changes language for Wikipedia search PER USER')
async def wikilang(ctx, language=None):
    if language==None:
        deflang=str(wikipedia_language.setdefault(str(ctx.message.author.id), guild_language.get(str(ctx.guild.id), "en")))
        await ctx.send("Language is {short} - {long}".format(short=deflang, long=wikipedia.languages()[deflang]))
        return
    query=language.lower()
    if query in wikipedia.languages():
        wikipedia_language.update({str(ctx.message.author.id): str(query)})
        lg = wikipedia.languages()[query]
        await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["wikilang_success"].format(query=query, lg=lg))
    else:
        defaultlanguage = wikipedia_language.setdefault(str(ctx.message.author.id), guild_language.setdefault(str(ctx.guild.id), "en"))
        await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["wikilang_error"].format(defaultlang=defaultlanguage, defaultlg=wikipedia.languages()[defaultlanguage]))
    with open('wikipedia_language.json', 'w') as json_file:
        json.dump(wikipedia_language, json_file)
    if use_postgres: backup()


@client.command(aliases=['urbandefinition', 'urbandictionary', 'ud', 'urbanexample'], brief='Gives a definition for a given query from urban dictionary')
async def urban(ctx, *, query):
    urbandefinition = ud.define(query)
    ud_definition=urbandefinition[0].definition.replace('[', '').replace(']', '')
    ud_example=urbandefinition[0].example.replace('[', '').replace(']', '')
    if len(ud_definition)>1024:
        ud_definition=ud_definition[:1021]+"..."
    if len(ud_example)>1024:
        ud_example=ud_definition[:1021]+"..."
    embed=discord.Embed(colour=0xe86222,
                        title=urbandefinition[0].word,
                        url="https://www.urbandictionary.com/define.php?term={word}".format(word=urbandefinition[0].word.replace(" ", "%20")))
    embed.add_field(name="Definition", value=ud_definition, inline=False)
    embed.add_field(name="Example", value=ud_example, inline=False)
    embed.set_footer(text="{upvotes} 👍 {downvotes} 👎".format(upvotes=urbandefinition[0].upvotes, downvotes=urbandefinition[0].downvotes))
    embed.set_author(name="Urban Dictionary",
                    icon_url="https://cdn.discordapp.com/attachments/795406810844495944/799297576766799882/ud.png",
                    url="https://www.urbandictionary.com/")
    await ctx.send(embed=embed)


@client.command(aliases=['bebacekic'], brief='Warns user for their inappropriate behavior')
async def babyhammer(ctx, *, user):
    await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["babyhammer"].format(user=user))

@client.command(aliases=['8ball'], brief='Magic 8 Ball... also ?8ball')
async def magic8ball(ctx, *, question):
    query=question
    alreadyanswered = answered.setdefault(str(ctx.message.author.id), ["a", "b"])
    if query.lower() in alreadyanswered:
        await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["already_answered"])
    else:
        answer = random.choice(eightball.odgovori if guild_language.setdefault(str(ctx.guild.id), "en")=="hr" else eightball.answers)
        for i in range(10, 15):
            if answer == (eightball.odgovori if guild_language.setdefault(str(ctx.guild.id), "en")=="hr" else eightball.answers)[i]:
                await ctx.send(f'{answer}')
                return
        alreadyanswered.append(str(query).lower())
        answered.update({str(ctx.message.author.id): alreadyanswered})
        await ctx.send(f'{answer}')


@client.command(aliases=['cp', 'cropasta', 'pasta'], brief='Searches copy|cropasta for given query')
async def copypasta(ctx, *, query):
    maxlength=4000
    subreddit=None
    if ctx.message.content.startswith('?copypasta'):
        subreddit='copypasta'
        color=0xFF5700
    elif ctx.message.content.startswith('?cropasta'):
        subreddit='cropasta'
        color=0xFF0000
    else:
        subreddit=("cropasta" if guild_language.setdefault(str(ctx.guild.id), default_lang)=="hr" else "copypasta")
        color=(0xFF5700 if subreddit == "copypasta" else 0xFF0000)
    for submission in reddit.subreddit(subreddit).search(query):
        textpost=submission.selftext
        if len(textpost)>maxlength:
            textpost=textpost[maxlength-3:]+"..."
        embed=discord.Embed(colour=color,
                        title=submission.title,
                        description=textpost,
                        url=submission.url
                        )
        msg = await ctx.send(embed=embed)
        subreddit_instance=reddit.subreddit(subreddit)
        embed.set_author(name=subreddit_instance.display_name,
                        icon_url=subreddit_instance.community_icon,
                        url="https://www.reddit.com/{path}".format(path=subreddit_instance._path))
        await msg.edit(embed=embed)
        break


@client.command(aliases=['meme', 'reddit'], brief='Random post from given subreddit', description='Random post from subreddit <query> or if subreddit is left out it defaults to your desired setting in ?hotsource|memesource')
async def hot(ctx, *, subreddit=None):
    global subsettings
    msg = None
    try:
        subsettings = restore(file="subsettings.json")
    except Exception as e:
        await ownerdm.send("Unable to restore subsettings.json:\n{exception}".format(exception=e))
        restore()
        try:
            with open('subsettings.json') as json_file:
                subsettings = json.load(json_file)
            await ownerdm.send('subsettings.json loaded')
            await ownerdm.send(f'subsettings:\n```{subsettings}```')
        except:
            await ownerdm.send('subsettings.json not found')
    query=subreddit
    if query == None:
        try:
            sub = random.choice(subsettings[str(ctx.message.author.id)])
            print(f'{ctx.message.author.id}: {sub}')
            if reddit.subreddit(sub).over18 and not ctx.channel.is_nsfw():
                sublist=list(subsettings[str(ctx.message.author.id)])
                random.shuffle(sublist)
                for choice in sublist:
                    if not reddit.subreddit(choice).over18:
                        sub=choice
                        break
        except:
            sub=random.choice(default_subreddits)
            msg = await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["default_sub_not_set"])
    else:
        sub = query.replace(' ', '')
        if sub.startswith("r/"):
            sub=sub[2:]
    for banned in banned_subs:
        if banned in sub:
            await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["banned_sub"].format(banned=banned))
            return
    subreddit = reddit.subreddit(sub)
    if subreddit.over18:
        if not ctx.channel.is_nsfw():
            await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["nsfw_sub"])
            return
    for submission in subreddit.random_rising():
        if not submission.is_self:
            print(submission.url)
            if "v.redd.it" not in submission.url and "youtu" not in submission.url and "imgur" not in submission.url and "vimeo" not in submission.url and "twitter" not in submission.url and "dailymotion" not in submission.url and "tiktok" not in submission.url and "gfycat" not in submission.url: #check for video content not supported in embed
                embed=discord.Embed(colour=0xFF5700,
                                    title=submission.title,
                                    url=submission.url
                                    )
                embed.set_image(url=submission.url)
                embed.set_author(name=subreddit.display_name,
                                icon_url=subreddit.community_icon,
                                url="https://www.reddit.com/{path}".format(path=subreddit._path))
                if msg:
                    await msg.edit(content=None, embed=embed)
                else:
                    await ctx.send(embed=embed)
                return
    await ctx.send("Not found.")


@client.command(aliases=['hotsource', 'redditsource', 'subreddit', 'subscribe', 'sub'], brief='Changes source subreddit for an empty ?hot|meme comamnd')
async def memesource(ctx, *, subreddit):
    query=subreddit
    sub = query.replace(' ', '')
    if sub.startswith("r/"):
        sub=sub[2:]
    if sub.lower()=="none":
        try:
            subsettings.pop(str(ctx.message.author.id))
        except:
            pass
        await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["default_sub_removed"])
        with open('subsettings.json', 'w') as json_file:
            json.dump(subsettings, json_file)
        if use_postgres: backup()
        return
    try:
        if reddit.subreddit(sub).over18:
            pass
        if str(ctx.message.author.id) not in subsettings:
            subsettings[str(ctx.message.author.id)]=[]
        subsettings[str(ctx.message.author.id)].append(sub)
        await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["default_sub_success"].format(sub=sub))
    except:
        await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["default_sub_fail"])
    with open('subsettings.json', 'w') as json_file:
        json.dump(subsettings, json_file)
    if use_postgres: backup()

@client.command(aliases=['subreddits', 'mysubs'])
async def subs(ctx):
    try:
        subsettings = restore(file="subsettings.json")
    except Exception as e:
        await ownerdm.send("Unable to restore subsettings.json:\n{exception}".format(exception=e))
        restore()
        try:
            with open('subsettings.json') as json_file:
                subsettings = json.load(json_file)
            await ownerdm.send('subsettings.json loaded')
            await ownerdm.send(f'subsettings:\n```{subsettings}```')
        except:
            await ownerdm.send('subsettings.json not found')
    embed=discord.Embed(
        colour=0x7289da,
        title=("Your Subreddits" if guild_language.setdefault(str(ctx.guild.id), "en")=="en" else "Vaši Subredditi"),
        description="\n".join(subsettings[str(ctx.message.author.id)]) if str(ctx.message.author.id) in subsettings else ("You are subscribed to no subreddits" if guild_language.setdefault(str(ctx.guild.id), "en")=="en" else "Niste se pretplatili na nijedan subreddit")
    )
    embed.set_author(name=ctx.message.author.display_name, icon_url=ctx.message.author.avatar_url)
    await ctx.send(embed=embed)
        

@client.command(aliases=['unsub', 'removesub'])
async def unsubscribe(ctx, *, sub):
    sub=sub.replace(" ", "")
    if sub.startswith("r/"):
        sub=sub[2:]
    try:
        if reddit.subreddit(sub).over18:
            pass
        if str(ctx.message.author.id) not in subsettings:
            raise Exception
        subsettings[str(ctx.message.author.id)].remove(sub)
        await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["remove_sub_success"].format(sub=sub))
    except:
        await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["remove_sub_fail"])
    with open('subsettings.json', 'w') as json_file:
        json.dump(subsettings, json_file)
    if use_postgres: backup()

@client.command(aliases=['tkojepitao', 'tkojepito'], brief='Nobody asked')
async def whoasked(ctx):
    await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["who_asked"])


@client.command(aliases=['garand'], brief='It\'s a garand ping...')
async def m1garand(ctx):
    await ctx.send("**PING!**\nhttps://cdn.discordapp.com/attachments/601676952134221845/728732427815616672/PING.mp4")


@client.command(aliases=['changelanguage'], brief='Debug command')
async def changelang(ctx, language=None):
    global guild_language
    if ctx.message.author.id == ownerid or ctx.author.guild_permissions.manage_messages or ctx.author.guild_permissions.administrator:
        pass
    else:
        await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["permission_denied"])
        return
    if language == None:
        guild_language[str(ctx.guild.id)] = "hr"*(guild_language[str(ctx.guild.id)]=="en")+"en"*(guild_language[str(ctx.guild.id)]=="hr")
        await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["language_change"])
    if language in languages:
        guild_language[str(ctx.guild.id)] = str(language)
        await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["language_change"])
    else:
        await ctx.send(language_not_supported)
        return
    try:
        with open('guild_language.json', 'w') as json_file:
                json.dump(guild_language, json_file)
        await ownerdm.send('guild_language.json updated')
    except:
        await ownerdm.send('guild_language.json update error')
    if use_postgres: backup()


@client.command(aliases=['banaj', 'banuj'], brief='A definetly real warn command')
async def warn(ctx, *, args):
    warnovi = []
    kaomod=False
    try:
        person, reason = args.split('>', maxsplit=1)
        if reason == '':
            await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["specify_reason"])
            return
        while reason[0] == ' ':
            reason=reason[1:]
    except:
        await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["specify_user"])
        return
    for role in ctx.author.roles:
        if role.id == 694533853951295590:
            kaomod=True
    if not kaomod:
        if ctx.author.guild_permissions.manage_messages:
            kaomod=True
        if ctx.author.guild_permissions.administrator:
            kaomod=True
        if ctx.message.author.id == ownerid:
            kaomod=True
    if not kaomod:
        await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["permission_denied"])
        return
    try:
        ime = f'{ctx.message.mentions[0].name}#{ctx.message.mentions[0].discriminator}'
    except:
        await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["specify_user"])
        return
    userid=ctx.message.mentions[0].id
    try:
        warnovi = userwarns.pop(str(userid))
    except:
        warnovi = []
    finally:
        warnovi+=reason.split("\n")
        userwarns.update({str(userid): warnovi})
        await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["warn_success"].format(ime=ime, reason=reason))
        await client.get_user(userid).send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["warned"].format(guild_name=ctx.guild.name, reason=reason))
        with open('warns.json', 'w') as json_file:
            json.dump(userwarns, json_file)
        if use_postgres: backup()


@client.command(aliases=['warnovi'], brief='Lists warnings for given user')
async def warns(ctx, *, user=None):
    warnovi = ''
    try:
        userid=ctx.message.mentions[0].id
    except:
        if user == None or str(user).replace(' ', '') == '':
            userid=ctx.message.author.id
            try:
                for warn in userwarns[str(userid)]:
                    warnovi = warnovi+warn+'\n'
                if not warnovi == '':
                    await ctx.send(f'```{warnovi}```')
                else:
                    await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["no_warnings"])
                    return
            except:
                await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["no_warnings"])
                return
            return
    try:
        for warn in userwarns[str(userid)]:
            warnovi = warnovi+warn+'\n'
        if not warnovi == '':
            await ctx.send(f'```{warnovi}```')
        else:
            await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["no_warnings_or_user_not_mentioned"])
    except:
        await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["no_warnings_or_user_not_mentioned"])

@client.command(aliases=['deletewarns'], brief='Clears warnings for given user')
async def clearwarns(ctx, *, user):
    kaomod=False
    for role in ctx.author.roles:
        if role.id == 694533853951295590:
            kaomod=True
    if not kaomod:
        if ctx.author.guild_permissions.manage_messages:
            kaomod=True
        if ctx.author.guild_permissions.administrator:
            kaomod=True
        if ctx.message.author.id == ownerid:
            kaomod=True
    if not kaomod:
        await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["permission_denied"])
        return
    try:
        userid=ctx.message.mentions[0].id
        userwarns.pop(str(userid))
    except:
        await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["specify_user"])
        return
    warned_user = f'{ctx.message.mentions[0].name}#{ctx.message.mentions[0].discriminator}'
    await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["clearwarns_success"].format(user=warned_user))
    with open('warns.json', 'w') as json_file:
        json.dump(userwarns, json_file)
    if use_postgres: backup()

@client.command(aliases=['dobrodosao', 'willkommen'], brief='Welcomes the user')
async def welcome(ctx, *, user):
    try:
        userid=ctx.message.mentions[0].id
        await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["welcome"].format(userid=userid))
    except:
        await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["specify_user"])


@client.command(aliases=['message'], brief='Mod command')
async def send(ctx, channel, *, message):
    if ctx.message.author.id == ownerid or ctx.author.guild_permissions.manage_messages or ctx.author.guild_permissions.administrator:
        pass
    else:
        await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["permission_denied"])
        return
    try:
        target_channel = ctx.message.channel_mentions[0]
        await target_channel.send(f'{message}')
    except:
        await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["specify_channel"])

@client.command(aliases=['ap'], brief='Mod command')
async def archivepins(ctx, channel_1=None, channel_2=None):
    if ctx.message.author.id == ownerid or ctx.author.guild_permissions.manage_messages or ctx.author.guild_permissions.administrator:
        pass
    else:
        await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["permission_denied"])
        return
    if ctx.message.channel_mentions:
        channel1 = ctx.message.channel_mentions[0]
        channel2 = ctx.message.channel_mentions[1]
        pins = await channel1.pins()
        for pin in pins:
            text_message="> {message}".format(message=pin.content.replace("\n", "\n> "))
            if pin.attachments:
                await channel2.send("By <@!{userid}>\n{message}\n{attachment}".format(userid=pin.author.id, message=text_message, attachment=pin.attachments[0].url))
            elif not pin.embeds:
                await channel2.send("By <@!{userid}>\n{message}".format(userid=pin.author.id, message=text_message))
            else:
                await channel2.send("By <@!{userid}>\n{message}".format(userid=pin.author.id, message=text_message))
                await channel2.send(embed=pin.embeds[0])
                
    else:
        await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["specify_channel"])


@client.command(aliases=['checklang'], brief='Check current Discord server language')
async def lang(ctx):
    await ctx.send(f'Language is: {guild_language[str(ctx.guild.id)].upper()}') #return guild's language

@client.command(aliases=['latency'], brief='Check bot latency')
async def ping(ctx):
    embed = discord.Embed(title=f'{round(client.latency*1000, 1)}ms', colour=0xfefefe)
    embed.set_author(name='Pong!', icon_url='https://cdn.discordapp.com/attachments/601676952134221845/748535727389671444/toilet.gif') #spinning toilet
    await ctx.send(embed=embed)

@client.command(aliases=['ars'], brief='Add a static response')
async def addresponsestatic(ctx, *, response):
    kaomod=False
    for role in ctx.author.roles:
        if role.id == 694533853951295590:
            kaomod=True
    if not kaomod:
        if ctx.author.guild_permissions.manage_messages:
            kaomod=True
        if ctx.author.guild_permissions.administrator:
            kaomod=True
        if ctx.message.author.id == ownerid:
            kaomod=True
    if not kaomod:
        await ctx.send(languages[str(ctx.guild.id)])
        return
    key, value = response.split(';')
    while key[0] == ' ':
        key = key[1:]
    while value[0] == ' ':
        value = value[1:]
    if str(ctx.guild.id) not in responses:
        responses[str(ctx.guild.id)]={"static": {}, "dynamic": {}}
    responses[str(ctx.guild.id)]["static"].update({key.lower(): value})
    with open('responses.json', 'w') as json_file:
        json.dump(responses, json_file)
    await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["static_response_added"].format(value=value, key=key))
    if use_postgres: backup()

@client.command(aliases=['ard'], brief='Add a dynamic response')
async def addresponsedynamic(ctx, *, response):
    kaomod=False
    for role in ctx.author.roles:
        if role.id == 694533853951295590:
            kaomod=True
    if not kaomod:
        if ctx.author.guild_permissions.manage_messages:
            kaomod=True
        if ctx.author.guild_permissions.administrator:
            kaomod=True
        if ctx.message.author.id == ownerid:
            kaomod=True
    if not kaomod:
        await ctx.send(f'Nemate dozvolu!' if guild_language.setdefault(str(ctx.guild.id), False) else f'You don\'t have permissions')
        return
    key, value = response.split(';')
    while key[0] == ' ':
        key = key[1:]
    while value[0] == ' ':
        value = value[1:]
    if str(ctx.guild.id) not in responses:
        responses[str(ctx.guild.id)]={"static": {}, "dynamic": {}}
    responses[str(ctx.guild.id)]["dynamic"].update({key.lower(): value})
    with open('responses.json', 'w') as json_file:
        json.dump(responses, json_file)
    await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["dynamic_response_added"].format(value=value, key=key))
    if use_postgres: backup()

@client.command(aliases=['rrd', 'rrs'], brief='Remove a dynamic response | Owner only')
async def removeresponse(ctx, *, response):
    if ctx.message.author.id == ownerid or ctx.author.guild_permissions.manage_messages or ctx.author.guild_permissions.administrator:
        pass
    else:
        await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["permission_denied"])
        return
    if ctx.message.content.startswith("?rrd"):
        try:
            key = list(responses.get(str(ctx.guild.id), {"dynamic": {}})["dynamic"].keys())[list(responses.get(str(ctx.guild.id), {"dynamic": []})["dynamic"].values()).index(response)]
        except ValueError:
            await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["response_not_found"].format(response=response))
            return
        if responses[str(ctx.guild.id)]["dynamic"].pop(key) == response:
            await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["dynamic_response_removed"].format(value=response, key=key))
    elif ctx.message.content.startswith("?rrs"):
        try:
            key = list(responses.get(str(ctx.guild.id), {"static": {}})["static"].keys())[list(responses.get(str(ctx.guild.id), {"static": {}})["static"].values()).index(response)]
        except ValueError:
            await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["response_not_found"].format(response=response))
            return
        if responses[str(ctx.guild.id)]["static"].pop(key) == response:
            await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["static_response_removed"].format(value=response, key=key))
    else:
        await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["specify_response"])
        return
    with open('responses.json', 'w') as json_file:
        json.dump(responses, json_file)
    if use_postgres: backup()


@client.command(brief='Dashboard')
async def website(ctx):
    embed=discord.Embed(colour=0x87ceeb,
                        title="WikiBot Web Dashboard",
                        url="https://wikibot.tech/")
    await ctx.send(embed=embed)

@client.command(brief='Vote for bot')
async def vote(ctx):
    embed=discord.Embed(colour=0x87ceeb,
                        title="Vote for WikiBot",
                        url="https://top.gg/bot/720738328714018816/vote")
    await ctx.send(embed=embed)

@client.command(brief='Invite bot')
async def invite(ctx):
    embed=discord.Embed(colour=0x87ceeb,
                        title="Invite WikiBot",
                        url="https://top.gg/bot/720738328714018816/invite")
    await ctx.send(embed=embed)

@client.command(brief='Vote for bot')
async def toggle(ctx, *, parameter):
    if "dad" in parameter:
        if misc["dadbot"].setdefault(str(ctx.guild.id), True):
            misc["dadbot"][str(ctx.guild.id)]=False
            await ctx.send("Dadbot off ⛔")
        else:
            misc["dadbot"][str(ctx.guild.id)]=True
            await ctx.send("Dadbot on ✅")
    if "repeat" in parameter:
        if misc["repeat"].setdefault(str(ctx.guild.id), True):
            misc["repeat"][str(ctx.guild.id)]=False
            await ctx.send("Repeat off ⛔")
        else:
            misc["repeat"][str(ctx.guild.id)]=True
            await ctx.send("Repeat on ✅")
    if "wolfram" in parameter or "what is" in parameter:
        if misc["wolfram"].setdefault(str(ctx.guild.id), True):
            misc["wolfram"][str(ctx.guild.id)]=False
            await ctx.send("Wolfram off ⛔")
        else:
            misc["wolfram"][str(ctx.guild.id)]=True
            await ctx.send("Wolfram on ✅")


@client.command(aliases=['fixlink'], brief='Fix media.discordapp.net link (embed)')
async def fix(ctx, *, link):
    await ctx.message.delete()
    if "media.discordapp.net" in link:
        await ctx.send(link.replace("media.discordapp.net", "cdn.discordapp.com"))
        return
    await ctx.send("Invalid link!", delete_after=5)
    return


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    await client.process_commands(message)
    global message_history
    check = len(message.content) < 30
    for key in responses.get(str(message.guild.id), {"static": {}})["static"]:
        if key == message.content.lower():
            await message.channel.send(responses[str(message.guild.id)]["static"][key])
            return

    for key in responses.get(str(message.guild.id), {"dynamic": {}})["dynamic"]:
        if key in message.content.lower():
            await message.channel.send(responses[str(message.guild.id)]["dynamic"][key])
            return
    
    #dadbot
    if ((message.content.lower().startswith('ja sam ') and len(message.content) > 7 and guild_language.setdefault(str(message.guild.id), False)) or (message.content.lower().replace('\'', '').startswith('im ') and len(message.content) > 3 and not (guild_language.setdefault(str(message.guild.id), "en")=="hr"))) and check:
            if misc["dadbot"].get(str(message.guild.id), True):
                await message.channel.send((f'Bok {message.content[7:]}, ja sam tata') if guild_language.setdefault(str(message.guild.id), default_lang)=="hr" else (f'Hi {str(message.content)[4:] if ord(str(message.content)[1]) == 39 else str(message.content)[3:]}, I\'m dad'))
            return
    
    if started:

        #wolfram
        if misc["wolfram"].get(str(message.guild.id), True):
            if guild_language.setdefault(str(message.guild.id), default_lang)=="en" and (message.content.lower().startswith('what is') or message.content.lower().startswith('what\'s') or message.content.lower().startswith('whats') or message.content.lower().startswith('how much is')):
                await message.channel.trigger_typing()
                thread = threading.Thread(target=wolfram_query, args=('s ', message.content.lower(), message,))
                thread.start()
                return
            if guild_language.setdefault(str(message.guild.id), default_lang)=="hr" and (message.content.lower().startswith('kolko je') or message.content.lower().startswith('koliko je') or message.content.lower().startswith('šta je')):
                await message.channel.trigger_typing()
                thread = threading.Thread(target=wolfram_query, args=(' je ', message.content.lower(), message,))
                thread.start()
                return

        
        # repeat messages
        if not message.content.startswith('?') and misc["repeat"].get(str(message.guild.id), True):
            #print(f'{message.guild.name} - {message.channel.name}({str(message.channel.id)})')
            Channel = message_history.setdefault(message.channel.id, [None, None, None])
            if Channel == [None, None, None]:
                # Channel = [message.content, None, None]
                counter=0
                first=True
                try:
                    async for messages in client.get_channel(message.channel.id).history(limit=4):
                        if first:
                            first=False                        
                        else:
                            message_history[message.channel.id][counter]=messages.content
                            counter += 1
                    # print("Added channel {channel} from server {guild}".format(channel=message.channel.name, guild=message.guild.name))
                except discord.NoMoreItems:
                    print("NoMoreItems")
                except:
                    print("idk lol")
            Channel = message_history.setdefault(message.channel.id, [None, None, None])
            #print(f'{message.author.name}#@{message.author.discriminator}: {message.content}')
            if Channel[0] == message.content and Channel[1] == message.content and Channel[2] != message.content and message.content != "":
                await message.channel.send(f'{message.content}')
                print(f'Repetition in {message.guild.name+" - "+message.channel.name}: {message.content}')
            message_history[message.channel.id] = [message.content, Channel[0], Channel[1]]


def sigterm(signal, frame):
    print("Graceful exit")
    """
    if use_postgres:
        backup()"""


def wolfram_query(sep, msg, ctx):
    channelid=ctx.channel.id
    channel=client.get_channel(channelid)
    embed=None
    query = msg.split(sep, maxsplit=1)[1]
    try:
        res = wolfram.query(query)
        pod=res.pods
        title=next(pod).text
        embed=discord.Embed(colour=0xff4500,
                        title=title)
        description=next(pod).text
        for field in description.split("\n"):
            if field.count("|")==1:
                field_list=field.split("|", maxsplit=1)
                while field_list[1].startswith(" "):
                    field_list[1]=field_list[1][1:]
                embed.add_field(name=field_list[0], value=field_list[1])
            else:
                if embed.description==discord.Embed.Empty:
                    embed.description=field+"\n"
                else:
                    embed.description+=field+"\n"
        embed.set_footer(text="from Wolfram",
                                icon_url="https://cdn.discordapp.com/attachments/795406810844495944/839226953206595654/wolfram.png")
        client.loop.create_task(channel.send(embed=embed))
        return
    except:
        pass
    try:
        urbandefinition = ud.define(query)
        ud_definition=urbandefinition[0].definition.replace('[', '').replace(']', '')
        if len(ud_definition)>1024:
            ud_definition=ud_definition[:1021]+"..."
        embed=discord.Embed(colour=0xe86222,
                            title=urbandefinition[0].word,
                            url="https://www.urbandictionary.com/define.php?term={word}".format(word=urbandefinition[0].word.replace(" ", "%20")))
        embed.add_field(name="Definition", value=ud_definition, inline=False)
        embed.set_footer(text="from Urban Dictionary",
                            icon_url="https://cdn.discordapp.com/attachments/795406810844495944/799297576766799882/ud.png")
        client.loop.create_task(channel.send(embed=embed))
        return
    except:
        pass
    try:
        global wikipedia_language
        try:
            wikipedia_language = restore(file="wikipedia_language.json")
        except Exception as e:
            print("Unable to restore Wikipedia languages: \n{exception}".format(exception=e))
            restore()
            try:
                with open('wikipedia_language.json') as json_file:
                    wikipedia_language = json.load(json_file)
                print('wikipedia_language.json loaded')
                print(f'wikipedia_language:\n```{wikipedia_language}```')
            except:
                print('wikipedia_language.json not found')
        page=None
        wikipedia.set_lang(str(wikipedia_language.setdefault(str(ctx.author.id), guild_language.get(str(ctx.guild.id), "en"))))
        try:
            page=wikipedia.page(wikipedia.search(query)[0])
        except wikipedia.exceptions.DisambiguationError as e:
            counter=0
            while page==None:
                try:
                    page=wikipedia.page(e.options[counter])
                except:
                    counter+=1
        summary=page.summary.split("\n")[0]
        if len(summary)>2048:
            summary=summary[:2045]+"..."
        embed=discord.Embed(colour=0xfefefe,
                            title=page.title,
                            description=summary,
                            url=page.url,)
        embed.set_footer(text="from Wikipedia",
                        icon_url="https://cdn.discordapp.com/attachments/601676952134221845/799319569025335406/wikipedia.png")
        if page.images:
            embed.set_thumbnail(url=page.images[0])
        client.loop.create_task(channel.send(embed=embed))
        return
    except:
        pass
                


signal.signal(signal.SIGTERM, sigterm)
client.run(token)
