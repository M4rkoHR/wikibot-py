import pickle
import random
import re
import discord
import praw
import urbandictionary as ud
import wikipedia
import time
import json
from discord.ext import commands
from youtube_api import YoutubeDataApi
from time import sleep

with open('my_config.json') as config_file:
    config = json.load(config_file)
token = config["discord_bot_token"]
reddit = praw.Reddit(client_id=config["praw"]["client_id"],
                     client_secret=config["praw"]["client_secret"],
                     user_agent=config["praw"]["user_agent"])
autor = config["bot_owner"]["name"]
banned_subs = config["banned_subs"]
ownerid = config["bot_owner"]["id"]
ytid = config["youtube_api_key"]
specific_responses_static = config["specific_responses_static"]
specific_responses_dynamic = config["specific_responses_dynamic"]
ownerdm = None # gets initialized to send messages to the bot owner later
defaultlang = "en"
defaultlg = wikipedia.languages()[defaultlang]
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
        with open('guild_language.pkl', 'rb') as pickle_file:
            guild_language = pickle.load(pickle_file)
        print(guild_language)
        await ownerdm.send('guild_language.pkl loaded')
        await ownerdm.send(f'guild_language:\n```{guild_language}```')
    except:
        await ownerdm.send('Exception, generating new guild_language.pkl')
        for guild in client.guilds:
            if guild.id == 601663624175419412:
                guild_language.update({guild.id: True})
            else:
                guild_language.update({guild.id: False})
        with open('guild_language.pkl', 'wb') as pickle_file:
            pickle.dump(guild_language, pickle_file)
    try:
        global wikipedia_language
        with open('wikipedia_language.pkl', 'rb') as pickle_file:
            wikipedia_language = pickle.load(pickle_file)
        await ownerdm.send('wikipedia_language.pkl loaded')
        await ownerdm.send(f'wikipedia_language:\n```{wikipedia_language}```')
    except:
        await ownerdm.send('wikipedia_language.pkl not found')
    try:
        global subsettings
        with open('subsettings.pkl', 'rb') as pickle_file:
            subsettings = pickle.load(pickle_file)
        await ownerdm.send('subsettings.pkl loaded')
        await ownerdm.send(f'subsettings:\n```{subsettings}```')
    except:
        await ownerdm.send('subsettings.pkl not found')
    try:
        global userwarns
        with open('warns.pkl', 'rb') as pickle_file:
            userwarns = pickle.load(pickle_file)
        await ownerdm.send('warns.pkl loaded')
    except:
        await ownerdm.send('warns.pkl not found')
    await ownerdm.send('Done')
    print("Done")


@client.command(brief='debug command')
async def d(ctx, *, string):
    if ctx.message.author.id != ownerid:
        await ctx.send(f'You are not {autor}')
        return
    if str(string).lower() == 'backup':
        await ownerdm.send(file=discord.File('guild_language.pkl'))
        await ownerdm.send(file=discord.File('wikipedia_language.pkl'))
        # await ownerdm.send(file=discord.File('kanali.pkl'))
        await ownerdm.send(file=discord.File('subsettings.pkl'))
        await ownerdm.send(file=discord.File('warns.pkl'))
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
        wikipedia.set_lang(str(wikipedia_language.setdefault(ctx.message.author.id, "en")))
    except:
        wikipedia.set_lang("en")
    finally:
        await ctx.send(f'{wikipedia.summary(query, sentences=3)}')


@client.command(brief='Changes language for Wikipedia search PER USER')
async def wikilang(ctx, language):
    query=language
    if query in wikipedia.languages():
        wikipedia_language.update({ctx.message.author.id: str(query)})
        lg = wikipedia.languages()[query]
        await ctx.send(f'Vas jezik za Wikipediju je uspješno postavljen u \"{query}\" - {lg}' if guild_language.setdefault(ctx.guild.id, False) else f'Your Wikipedia language has been successfully set to \"{query}\" - {lg}')
    else:
        if guild_language.setdefault(ctx.guild.id, False):
            wikipedia_language.update({ctx.message.author.id: str("hr")})
        else:
            wikipedia_language.update({ctx.message.author.id: str(defaultlang)})
        await ctx.send(f'Pogreska! Vas jezik Wikipedije je prema zadanom \"hr\" - hrvatski' if guild_language.setdefault(ctx.guild.id, False) else f'Error! Your Wikipedia language is by default \"{defaultlang}\" - {defaultlg}')
    with open('wikipedia_language.pkl', 'wb') as pickle_file:
        pickle.dump(wikipedia_language, pickle_file)


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
    query=user
    await ctx.send(f'+warn {query} slijedeci put kad ovako nesto postas ovdje pobrat ces ban, doslovce se vidi da je netko umro' if guild_language.setdefault(ctx.guild.id, False) else f'+warn {query} next time you send something like this here you\'ll catch a ban, you can literally see someone has died')


@client.command(aliases=['8ball'], brief='Magic 8 Ball... also ?8ball')
async def magic8ball(ctx, *, question):
    query=question
    global odgovori
    global answered
    alreadyanswered = answered.setdefault(ctx.message.author.id, ["a", "b"])
    if query.lower() in alreadyanswered:
        await ctx.send(f'Već sam ti odgovorio na to pitanje...' if guild_language.setdefault(ctx.guild.id, False) else f'I\'ve already answered that question...')
    else:
        answer = random.choice(odgovori if guild_language.setdefault(ctx.guild.id, False) else answers)
        for i in range(10, 15):
            if answer == (odgovori if guild_language.setdefault(ctx.guild.id, False) else answers)[i]:
                await ctx.send(f'{answer}')
                return
        alreadyanswered.append(str(query).lower())
        answered.update({ctx.message.author.id: alreadyanswered})
        await ctx.send(f'{answer}')


@client.command(aliases=['cp', 'cropasta', 'pasta'], brief='Searches copy|cropasta for given query')
async def copypasta(ctx, *, query):
    maxlength=2000
    for submission in reddit.subreddit("cropasta" if guild_language.setdefault(ctx.guild.id, False) else "copypasta").search(query):
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
            sub = str(subsettings[ctx.message.author.id])
            print(f'{ctx.message.author.id}: {str(subsettings[ctx.message.author.id])}')
        except:
            await ctx.send("Niste postavili zadani subreddit(komandom ?hotsource|memesource) za korištenje sa praznom ?hot naredbom" if guild_language.setdefault(ctx.guild.id, False) else "You have not set a default subreddit(using command ?hotsource|memesource) to use with an empty ?hot command")
            return
    else:
        sub = query.replace(' ', '')
        if sub.startswith("r/"):
            sub=sub[2:]
    for banan in banned_subs:
        if banan in sub:
            await ctx.send(f'{banan} te napravio' if guild_language.setdefault(ctx.guild.id, False) else f'{banan} is forbidden')
            return
    subreddit = reddit.subreddit(sub)
    if subreddit.over18:
        if not ctx.channel.nsfw:
            await ctx.send("NSFW Subreddit, aborting...")
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
        subsettings.update({ctx.message.author.id: str(query)})
        await ctx.send(f'Vaš preferirani subreddit za praznu ?hot|meme naredbu je postavljen u {sub}' if guild_language.setdefault(ctx.guild.id, False) else f'Your preferred subreddit for an empty ?hot|meme command has been set to {sub}')
    except:
        await ctx.send('Subreddit nije pronađen' if guild_language.setdefault(ctx.guild.id, False) else 'Subreddit not found')
    with open('subsettings.pkl', 'wb') as pickle_file:
        pickle.dump(subsettings, pickle_file)


@client.command(aliases=['tkojepitao', 'tkojepito'], brief='Nobody asked')
async def whoasked(ctx):
    await ctx.send("**Sada svira**: Tko je pitao? (Feat: Nitko) ───────────:white_circle:────── ◄◄⠀▐▐⠀►► 𝟸:𝟷𝟾 / 𝟹:𝟻𝟼⠀───○ :loud_sound:" if guild_language.setdefault(ctx.guild.id, False) else "**Now playing**: Who asked? (Feat: Nobody) ───────────:white_circle:────── ◄◄⠀▐▐⠀►► 𝟸:𝟷𝟾 / 𝟹:𝟻𝟼⠀───○ :loud_sound:")


@client.command(aliases=['garand'], brief='It\'s a garand ping...')
async def m1garand(ctx):
    await ctx.send("**PING!**\nhttps://cdn.discordapp.com/attachments/601676952134221845/728732427815616672/PING.mp4")


@client.command(aliases=['changelanguage'], brief='Debug command')
async def changelang(ctx):
    if ctx.message.author.id != ownerid:
        await ctx.send(f'You are not Bot Owner')
        return
    global guild_language
    if guild_language.setdefault(ctx.guild.id, False):
        guild_language[ctx.guild.id] = False
        await ctx.send("Bot language has been changed to English")
    else:
        guild_language[ctx.guild.id] = True
        await ctx.send("Jezik bota je promijenjen u Hrvatski")
    try:
        with open('guild_language.pkl', 'wb') as pickle_file:
                pickle.dump(guild_language, pickle_file)
        await ownerdm.send('guild_language.pkl updated')
    except:
        await ownerdm.send('guild_language.pkl update error')


@client.command(aliases=['banaj', 'banuj'], brief='A definetly real warn command')
async def warn(ctx, *, args):
    warnovi = []
    kaomod=False
    try:
        person, reason = args.split('>', maxsplit=1)
        if reason == '':
            await ctx.send(f'Molimo odredite razlog upozorenja' if guild_language.setdefault(ctx.guild.id, False) else f'Please specify a reason')
            return
        while reason[0] == ' ':
            reason=reason[1:]
    except:
        await ctx.send(f'Nisi spomenuo korisnika u poruci, pokusaj ponovo' if guild_language.setdefault(ctx.guild.id, False) else f'You haven\'t mentioned an user in your message, try again...')
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
        await ctx.send(f'Nemate dozvolu!' if guild_language.setdefault(ctx.guild.id, False) else f'You don\'t have permissions')
        return
    try:
        ime = ctx.message.mentions[0].name + "#" + ctx.message.mentions[0].discriminator
    except:
        await ctx.send(f'Nisi spomenuo korisnika u poruci, pokusaj ponovo' if guild_language.setdefault(ctx.guild.id, False) else f'You haven\'t mentioned an user in your message, try again...')
        return
    userid=ctx.message.mentions[0].id
    try:
        warnovi = userwarns.pop(userid)
    except:
        warnovi = []
    finally:
        warnovi.append(reason)
        userwarns.update({userid: warnovi})
        await ctx.send(f':white_check_mark: Korisnik **{ime}** je upozoren iz razloga:\n{reason}' if guild_language.setdefault(ctx.guild.id, False) else f':white_check_mark: User **{ime}** has been warned for:\n{reason}')
        await client.get_user(userid).send(f'Upozoreni ste u ste u serveru **{ctx.guild.name}** iz razloga:\n{reason}' if guild_language.setdefault(ctx.guild.id, False) else f'You were warned in **{ctx.guild.name}** because of the following reason:\n{reason}')
        with open('warns.pkl', 'wb') as pickle_file:
            pickle.dump(userwarns, pickle_file)


@client.command(aliases=['warnovi'], brief='Lists warnings for given user')
async def warns(ctx, *, user=None):
    warnovi = ''
    try:
        userid=ctx.message.mentions[0].id
    except:
        if user == None or str(user).replace(' ', '') == '':
            userid=ctx.message.author.id
            try:
                for warn in userwarns[userid]:
                    warnovi = warnovi+warn+'\n'
                if not warnovi == '':
                    await ctx.send(f'```{warnovi}```')
                else:
                    await ctx.send(f'Nemate upozorenja :blush:' if guild_language.setdefault(ctx.guild.id, False) else f'You don\'t have any warnings :blush:')
                    return
            except:
                await ctx.send(f'Nemate upozorenja :blush:' if guild_language.setdefault(ctx.guild.id, False) else f'You don\'t have any warnings :blush:')
                return
            return
    try:
        for warn in userwarns[userid]:
            warnovi = warnovi+warn+'\n'
        if not warnovi == '':
            await ctx.send(f'```{warnovi}```')
        else:
            await ctx.send(f'Nisi spomenuo korisnika u poruci ili korisnik nema upozorenja' if guild_language.setdefault(ctx.guild.id, False) else f'You haven\'t mentioned an user in your message or the user has not yet been warned')
    except:
        await ctx.send(f'Nisi spomenuo korisnika u poruci ili korisnik nema upozorenja' if guild_language.setdefault(ctx.guild.id, False) else f'You haven\'t mentioned an user in your message or the user has not yet been warned')

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
        await ctx.send(f'Nemate dozvolu!' if guild_language.setdefault(ctx.guild.id, False) else f'You don\'t have permissions')
        return
    try:
        userid=ctx.message.mentions[0].id
        userwarns.pop(userid)
    except:
        await ctx.send(f'Nisi spomenuo korisnika u poruci, pokusaj ponovo' if guild_language.setdefault(ctx.guild.id, False) else f'You haven\'t mentioned an user in your message, try again...')
        return
    await ctx.send(f':white_check_mark: Korisniku **{ctx.message.mentions[0].name}#{ctx.message.mentions[0].discriminator}** su obrisana upozorenja' if guild_language.setdefault(ctx.guild.id, False) else f':white_check_mark: **{ctx.message.mentions[0].name}#{ctx.message.mentions[0].discriminator}\'s** warns have been deleted')
    with open('warns.pkl', 'wb') as pickle_file:
            pickle.dump(userwarns, pickle_file)

@client.command(aliases=['dobrodosao', 'willkommen'], brief='Welcomes the user')
async def welcome(ctx, *, user):
    try:
        userid=ctx.message.mentions[0].id
        await ctx.send(f'<@!{userid}> dobrodošao imaš u <#601676952134221845> korisne komande u pinned messages, uživaj' if guild_language.setdefault(ctx.guild.id, False) else f'<@!{userid}>, Welcome!')
    except:
        await ctx.send(f'Nisi spomenuo korisnika u poruci' if guild_language.setdefault(ctx.guild.id, False) else f'You haven\'t mentioned an user in your message')


@client.command(aliases=['message'], brief='Mod command')
async def send(ctx, channel, *, message):
    try:
        kanal = ctx.message.channel_mentions[0]
        await kanal.send(f'{message}')
    except:
        await ctx.send(f'Nisi spomenuo kanal u poruci' if guild_language.setdefault(ctx.guild.id, False) else f'You haven\'t mentioned a channel in your message')


@client.command(aliases=['checklang'], brief='Check current Discord server language')
async def lang(ctx):
    await ctx.send('Language is: HR' if guild_language.setdefault(ctx.guild.id, False) else 'Language is: EN') #return guild's language

@client.command(aliases=['latency'], brief='Check bot latency')
async def ping(ctx):
    embed = discord.Embed(title=f'{round(client.latency*1000, 1)}ms', colour=0xfefefe)
    embed.set_author(name='Pong!', icon_url='https://cdn.discordapp.com/attachments/601676952134221845/748535727389671444/toilet.gif') #spinning toilet
    await ctx.send(embed=embed)


@client.event
async def on_message(message):
    global kanali
    check = len(message.content) < 30
    if message.author == client.user:
        return

    for key in specific_responses_static:
        if key == message.content.lower():
            await message.channel.send(specific_responses_static[key])
            return

    for key in specific_responses_dynamic:
        if key in message.content.lower():
            await message.channel.send(specific_responses_dynamic[key])
            return

    #dadbot
    check = len(message.content) < 30
    if ((message.content.lower().startswith('ja sam ') and len(message.content) > 7 and guild_language.setdefault(message.guild.id, False)) or (message.content.lower().replace('\'', '').startswith('im ') and len(message.content) > 3 and not guild_language.setdefault(message.guild.id, False))) and check:
            await message.channel.send((f'Bok {message.content[7:]}, ja sam tata') if guild_language.setdefault(message.guild.id, False) else (f'Hi {str(message.content)[4:] if ord(str(message.content)[1]) == 39 else str(message.content)[3:]}, I\'m dad'))
            return


    # repeat messages
    if not message.content.startswith('?'):
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
