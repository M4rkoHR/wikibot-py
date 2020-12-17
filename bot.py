import random
import re
import discord
import praw
import urbandictionary as ud
import wikipedia
import time
import json
import wolframalpha
from discord.ext import commands
from youtube_api import YoutubeDataApi
from time import sleep

with open('my_config.json') as config_file:
    config = json.load(config_file)
with open('responses.json') as responses_file:
    responses = json.load(responses_file)
with open('languages.json') as languages_file:
    languages = json.load(languages_file)
token = config["discord_bot_token"]
reddit = praw.Reddit(client_id=config["praw"]["client_id"],
                     client_secret=config["praw"]["client_secret"],
                     user_agent=config["praw"]["user_agent"])
autor = config["bot_owner"]["name"]
banned_subs = config["banned_subs"]
ownerid = config["bot_owner"]["id"]
ytid = config["youtube_api_key"]
wolfram = wolframalpha.Client(config["wolfram_api_key"])
ownerdm = None # gets initialized to send messages to the bot owner later
default_lang = "en"
wikipedia_language = {}
kanali = {}
answered = {}
subsettings = {}
userwarns = {}
guild_language = {} #returns True for a given guild if not english, otherwise False, automatically generated
intents = discord.Intents(messages=True, guilds=True, members=True)
client = commands.Bot(command_prefix = '?', intents=intents)
odgovori = [ # answers for 8ball in Croatian
    "Zasigurno",
    "Bez sumnje",
    "U to se možeš uzdati",
    "Da, definitivno",
    "Naravno",
    "Da je očit odgovor",
    "Da, najvjerovatnije",
    "Da.",
    "Da, retarde",
    "Svi znakovi upućuju na da",
    "Ne razumijem, pokušaj ponovno",
    "Kakvo je to pitanje jebemti",
    "Pitaj ponovo kasnije",
    "Nemogu sada predvidjeti",
    "Usredotoči se i pitaj ponovno",
    "Ne računaj na to",
    "Izgledi nisu dobri",
    "Moji izvori kažu ne",
    "Sumnjam",
    "Ne, zašto pitaš"
]
answers = [ # answers for 8ball in English
    'It is certain',
    'It is decidedly so',
    'Without a doubt',
    'Yes – definitely',
    'You may rely on it',
    'As I see it, yes',
    'Most likely',
    'Outlook good',
    'Yes Signs point to yes',
    'Well, obviously...',
    'Reply hazy', 'try again',
    'Ask again later',
    'Better not tell you now',
    'Cannot predict now',
    'Concentrate and ask again',
    'Dont count on it',
    'My reply is no',
    'My sources say no',
    'Outlook not so good',
    'Very doubtful'
]


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    await client.change_presence(activity=discord.Game(name='type ?help for help'))
    global ownerdm
    ownerdm = client.get_user(ownerid)
    await ownerdm.send('Generating kanali{}')
    for guild in client.guilds:
        for channel in guild.channels:
            if str(channel.type) == "text":
                kanali.update({channel.id: [None, None, None]})
                counter=0
                try:
                    async for message in channel.history(limit=3):
                        kanali[channel.id][counter]=message.content
                        print(message.content)
                        counter += 1
                except discord.NoMoreItems:
                    print("No more items")
                except:
                    kanali.update({channel.id: [None, None, None]})
                    print("Exception")
    try:
        global guild_language
        with open('guild_language.json') as json_file:
            guild_language = json.load(json_file)
        print(guild_language)
        await ownerdm.send('guild_language.json loaded')
        await ownerdm.send(f'guild_language:\n```{guild_language}```')
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
        await ownerdm.send(f'wikipedia_language:\n```{wikipedia_language}```')
    except:
        await ownerdm.send('wikipedia_language.json not found')
    try:
        global subsettings
        with open('subsettings.json') as json_file:
            subsettings = json.load(json_file)
        await ownerdm.send('subsettings.json loaded')
        await ownerdm.send(f'subsettings:\n```{subsettings}```')
    except:
        await ownerdm.send('subsettings.json not found')
    try:
        global userwarns
        with open('warns.json') as json_file:
            userwarns = json.load(json_file)
        await ownerdm.send('warns.json loaded')
    except:
        await ownerdm.send('warns.json not found')
    await ownerdm.send('Done')
    print("Done")


@client.command(brief='debug command')
async def d(ctx, *, string):
    if ctx.message.author.id != ownerid:
        await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["not_author"].format(author=autor))
        return
    if str(string).lower() == 'backup':
        await ownerdm.send(file=discord.File('guild_language.json'))
        await ownerdm.send(file=discord.File('wikipedia_language.json'))
        # await ownerdm.send(file=discord.File('kanali.json'))
        await ownerdm.send(file=discord.File('subsettings.json'))
        await ownerdm.send(file=discord.File('warns.json'))
        await ownerdm.send(file=discord.File('responses.json'))
        return
    command = f"{str(string)}"
    await ctx.send(f'{command}')


@client.command(aliases=['youtube'], brief='Searches YouTube for given query and returns link')
async def yt(ctx, *, query):
    yt = YoutubeDataApi(ytid)
    searches = yt.search(str(query))
    url = 'https://www.youtube.com/watch?v=' + searches[0]['video_id']
    searches.clear()
    await ctx.send(f'{url}')


@client.command(aliases=['wikipedia'], brief='Searches Wikipedia for given query in desired language(?wikilang)', description='Searches Wikipedia for given query in desired language(default english, changed with ?wikilang) and returns 3 sentences from summary')
async def wiki(ctx, *, query):
    try:
        wikipedia.set_lang(str(wikipedia_language.setdefault(str(ctx.message.author.id), default_lang)))
    except:
        wikipedia.set_lang(guild_language.setdefault(str(ctx.guild.id), "en"))
    finally:
        await ctx.send(f'{wikipedia.summary(query, sentences=3)}')


@client.command(brief='Changes language for Wikipedia search PER USER')
async def wikilang(ctx, language):
    defaultlang = guild_language.setdefault(str(ctx.guild.id), "en")
    defaultlg = wikipedia.languages()[defaultlang]
    query=language
    if query in wikipedia.languages():
        wikipedia_language.update({str(ctx.message.author.id): str(query)})
        lg = wikipedia.languages()[query]
        await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["wikilang_success"].format(query=query, lg=lg))
    else:
        if guild_language.setdefault(str(ctx.guild.id), False):
            wikipedia_language.update({str(ctx.message.author.id): str("hr")})
        else:
            wikipedia_language.update({str(ctx.message.author.id): str(defaultlang)})
        await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["wikilang_error"].format(defaultlang=defaultlang, defaultlg=defaultlg))
    with open('wikipedia_language.json', 'w') as json_file:
        json.dump(wikipedia_language, json_file)


@client.command(aliases=['urbandefinition'], brief='Gives a definition for a given query from urban dictionary')
async def urban(ctx, *, query):
    urbandefinition = ud.define(query)
    udefiniton = urbandefinition[0].definition.replace('[', '').replace(']', '')
    await ctx.send(f'{udefiniton}')


@client.command(brief='Gives an example for a given query from urban dictionary')
async def urbanexample(ctx, *, query):
    urbandefinition = ud.define(query)
    for d in urbandefinition:
        dexample = d.example
        dexample = dexample.replace('[', '')
        dexample = dexample.replace(']', '')
        await ctx.send(f'{dexample}')
        break


@client.command(aliases=['bebacekic'], brief='Warns user for their inappropriate behavior')
async def babyhammer(ctx, *, user):
    await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["babyhammer"].format(user=user))

@client.command(aliases=['8ball'], brief='Magic 8 Ball... also ?8ball')
async def magic8ball(ctx, *, question):
    query=question
    global odgovori
    global answered
    alreadyanswered = answered.setdefault(str(ctx.message.author.id), ["a", "b"])
    if query.lower() in alreadyanswered:
        await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["already_answered"])
    else:
        answer = random.choice(odgovori if guild_language.setdefault(str(ctx.guild.id), False) else answers)
        for i in range(10, 15):
            if answer == (odgovori if guild_language.setdefault(str(ctx.guild.id), False) else answers)[i]:
                await ctx.send(f'{answer}')
                return
        alreadyanswered.append(str(query).lower())
        answered.update({str(ctx.message.author.id): alreadyanswered})
        await ctx.send(f'{answer}')


@client.command(aliases=['cp', 'cropasta', 'pasta'], brief='Searches copy|cropasta for given query')
async def copypasta(ctx, *, query):
    maxlength=2000
    for submission in reddit.subreddit("cropasta" if guild_language.setdefault(str(ctx.guild.id), default_lang)=="hr" else "copypasta").search(query):
        textpost=submission.selftext
        while len(textpost)>maxlength:
            await ctx.send(textpost[:maxlength])
            textpost=textpost[maxlength:]
        await ctx.send(textpost)
        break


@client.command(aliases=['meme'], brief='Random post from given subreddit', description='Random post from subreddit <query> or if subreddit is left out it defaults to your desired setting in ?hotsource|memesource')
async def hot(ctx, *, subreddit=None):
    query=subreddit
    embed=discord.Embed(colour=discord.Colour.blue())
    if query == None:
        try:
            sub = str(subsettings[str(ctx.message.author.id)])
            print(f'{ctx.message.author.id}: {str(subsettings[str(ctx.message.author.id)])}')
        except:
            await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["default_sub_not_set"])
            return
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
        if not ctx.channel.nsfw:
            await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["nsfw_sub"])
            return
    for submission in subreddit.random_rising():
        if not submission.is_self:
            print(submission.url)
            if "v.redd.it" not in submission.url and "youtu" not in submission.url and "imgur" not in submission.url and "vimeo" not in submission.url and "twitter" not in submission.url and "dailymotion" not in submission.url and "tiktok" not in submission.url and "gfycat" not in submission.url: #check for video content not supported in embed
                embed.set_image(url=submission.url)
                embed.set_author(name=submission.title)
                await ctx.send(embed=embed)
                return
    await ctx.send("Not found.")


@client.command(aliases=['hotsource'], brief='Changes source subreddit for an empty ?hot|meme comamnd')
async def memesource(ctx, *, subreddit):
    query=subreddit
    sub = query.replace(' ', '')
    if sub.startswith("r/"):
        sub=sub[2:]
    try:
        if reddit.subreddit(sub).over18:
            pass
        subsettings.update({str(ctx.message.author.id): str(query)})
        await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["default_sub_success"].format(sub=sub))
    except:
        await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["default_sub_fail"])
    with open('subsettings.json', 'w') as json_file:
        json.dump(subsettings, json_file)


@client.command(aliases=['tkojepitao', 'tkojepito'], brief='Nobody asked')
async def whoasked(ctx):
    await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["who_asked"])


@client.command(aliases=['garand'], brief='It\'s a garand ping...')
async def m1garand(ctx):
    await ctx.send("**PING!**\nhttps://cdn.discordapp.com/attachments/601676952134221845/728732427815616672/PING.mp4")


@client.command(aliases=['changelanguage'], brief='Debug command')
async def changelang(ctx, language=None):
    global guild_language
    if ctx.message.author.id != ownerid or not ctx.author.guild_permissions.manage_messages:
        await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["permission_denied"])
        return
    if language in languages:
        guild_language[str(ctx.guild.id)] = str(language)
        await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["language_change"])
    if language == None:
        guild_language[str(ctx.guild.id)] = "hr"*(guild_language[str(ctx.guild.id)]=="en")+"en"*(guild_language[str(ctx.guild.id)]=="hr")
        await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["language_change"])
    try:
        with open('guild_language.json', 'w') as json_file:
                json.dump(guild_language, json_file)
        await ownerdm.send('guild_language.json updated')
    except:
        await ownerdm.send('guild_language.json update error')


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
        warnovi.append(reason)
        userwarns.update({str(userid): warnovi})
        await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["warn_success"].format(ime=ime, reason=reason))
        await client.get_user(userid).send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["warned"].format(guild_name=ctx.guild.name, reason=reason))
        with open('warns.json', 'w') as json_file:
            json.dump(userwarns, json_file)


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

@client.command(aliases=['dobrodosao', 'willkommen'], brief='Welcomes the user')
async def welcome(ctx, *, user):
    try:
        userid=ctx.message.mentions[0].id
        await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["welcome"].format(userid=userid))
    except:
        await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["specify_user"])


@client.command(aliases=['message'], brief='Mod command')
async def send(ctx, channel, *, message):
    try:
        kanal = ctx.message.channel_mentions[0]
        await kanal.send(f'{message}')
    except:
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
        if ctx.message.author.id == ownerid:
            kaomod=True
    if not kaomod:
        await ctx.send(languages[str(ctx.guild.id)])
        return
    key, value = response.lower().split(';')
    while key[0] == ' ':
        key = key[1:]
    while value[0] == ' ':
        value = value[1:]
    responses["static"].update({key: value})
    with open('responses.json', 'w') as json_file:
            json.dump(responses, json_file)
    await ownerdm.send(file=discord.File('responses.json'))
    await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["static_response_added"].format(value=value, key=key))

@client.command(aliases=['ard'], brief='Add a dynamic response')
async def addresponsedynamic(ctx, *, response):
    kaomod=False
    for role in ctx.author.roles:
        if role.id == 694533853951295590:
            kaomod=True
    if not kaomod:
        if ctx.author.guild_permissions.manage_messages:
            kaomod=True
        if ctx.message.author.id == ownerid:
            kaomod=True
    if not kaomod:
        await ctx.send(f'Nemate dozvolu!' if guild_language.setdefault(str(ctx.guild.id), False) else f'You don\'t have permissions')
        return
    key, value = response.lower().split(';')
    while key[0] == ' ':
        key = key[1:]
    while value[0] == ' ':
        value = value[1:]
    responses["dynamic"].update({key: value})
    with open('responses.json', 'w') as json_file:
            json.dump(responses, json_file)
    await ownerdm.send(file=discord.File('responses.json'))
    await ctx.send(languages[guild_language.setdefault(str(ctx.guild.id), "en")]["dynamic_response_added"].format(value=value, key=key))


@client.event
async def on_message(message):
    global kanali
    check = len(message.content) < 30
    if message.author == client.user:
        return

    for key in responses["static"]:
        if key == message.content.lower():
            await message.channel.send(responses["static"][key])
            return

    for key in responses["dynamic"]:
        if key in message.content.lower():
            await message.channel.send(responses["dynamic"][key])
            return

    if guild_language.setdefault(str(message.guild.id), default_lang)=="hr" and (message.content.lower().startswith('kolko je') or message.content.lower().startswith('koliko je') or message.content.lower().startswith('šta je')):
        res = wolfram.query(message.content.lower().split(' je ')[1])
        await message.channel.send(next(res.results).text)
        return
    #dadbot
    if ((message.content.lower().startswith('ja sam ') and len(message.content) > 7 and guild_language.setdefault(str(message.guild.id), False)) or (message.content.lower().replace('\'', '').startswith('im ') and len(message.content) > 3 and not guild_language.setdefault(str(message.guild.id), False))) and check:
            await message.channel.send((f'Bok {message.content[7:]}, ja sam tata') if guild_language.setdefault(str(message.guild.id), default_lang)=="hr" else (f'Hi {str(message.content)[4:] if ord(str(message.content)[1]) == 39 else str(message.content)[3:]}, I\'m dad'))
            return


    # repeat messages
    if not message.content.startswith('?'):
        Kanal = [None, None, None]
        print(f'{message.guild.name} - {message.channel.name}({str(message.channel.id)})')
        if message.channel.id in kanali:
            Kanal = kanali.get(message.channel.id, [None, None, None])
        if Kanal == [None, None, None]:
            counter=0
            try:
                async for message in client.get_channel(id).history(limit=3):
                    kanali[message.guild.id][counter]=message.content
                    counter += 1
            except discord.NoMoreItems:
                print("Eol 546")
            except:
                print("Exception 548")
        Kanal = kanali.setdefault(message.channel.id, [None, None, None])
        print(f'{message.author.name}#@{message.author.discriminator}: {message.content}')
        if Kanal[0] == message.content and Kanal[1] == message.content and Kanal[2] != message.content:
            await message.channel.send(f'{message.content}')
            print(f'Repeticija u {message.guild.name+" - "+message.channel.name}:, {message.content}')
        kanali[message.channel.id] = [message.content, Kanal[0], Kanal[1]]
    await client.process_commands(message)

client.run(token)
