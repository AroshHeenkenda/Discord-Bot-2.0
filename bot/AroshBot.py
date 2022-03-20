'''

IGNORE THIS FILE, ONLY STORED HERE FOR REFERENCE

import discord
from discord.ext import commands
from SimpleCommands import SimpleCommands
from memberCommands import MemberCommands

TOKEN =  #Bot token
PREFIX = '##' #Bot prefix

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='##', intents=intents)

#Adding the commands to the bot
bot.add_cog(SimpleCommands(bot))
bot.add_cog(MemberCommands(bot))

#Let me know the bot has logged in
@bot.event 
async def on_ready():
    #print('We have logged in as {0.user}.'.format(bot))
    print('Logged in as:')
    print('{0.user.name}'.format(bot))
    print('{0.user.id}'.format(bot))
    print('-----------')

bot.run(TOKEN)


#TO RUN TYPE -> py -3 AroshBot.py <- IN TERMINAL

#Need to run Lavalink server
# C:\Users\Arosh Heenkenda\Desktop\Coding Projects\Discord Bot 2.0\jdk-13.0.2\bin -> then write java -jar Lavalink.jar


#Saying hello to a user
@bot.event
async def on_message(message):

    #Get some variables for use
    username = str(message.author).split('#')[0] #Gets the user name
    user_message = str(message.content) #Gets content of the message
    channel = str(message.channel.name) #Name of channel it is sent in
    #Print this info, log the data
    print(f'{username}: {user_message} ({channel})')

    #If the author is the bot, return nothing
    if (message.author == bot.user):
        return
    
    #Say hello
    if (user_message.lower() == 'hello'):
        await message.channel.send(f'Hello {username} !')
        return 

    #Say polo, after saying marco
    elif (user_message.lower() == 'marco'):
        await message.channel.send(f'{username} Polo!')
        return 


@bot.command(name='ping')
async def pong(ctx):
    await ctx.channel.send('pong')


#To ensure the bot runs
bot.run(TOKEN)
'''