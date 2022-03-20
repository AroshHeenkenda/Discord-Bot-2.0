"""
Author: Arosh Heenkenda
Created: 10/01/2022
Edited: 21/03/2022
Purpose: Bot commands that I made for fun and to get used to the format.
"""

#IMPORTS
import discord
from discord.ext import commands
import random

#CONSTANTS
BLACKLISTED_IDS = [583174880145702925, 244001170710855682,253475162047905792] #stace, luke, ryan
CREATOR_ID = 443360265141092352

class FunCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    #Tells us that the cog is ready
    @commands.Cog.listener()
    async def on_ready(self):
        print("'Fun' cog ready...")

    #Hello command
    @commands.command(name="hello")
    async def hello_command(self, ctx):
        await ctx.send(f"Hello {ctx.author.mention}!")


    #Bitches Check command as requested by Carms
    @commands.command(name="bitches-check")
    async def bitchescheck_command(self, ctx):
        user_id = ctx.author.id
        if (user_id in BLACKLISTED_IDS): #This is stop stace geting bitches
            await ctx.send(f"{ctx.author.mention} you have a zero bitches.\nYou have zero play homie.")
        #Everyone else will get a randomized number
        else:
            await ctx.send(f"You have {random.randint(2, 100)} bitches.")

    #Dice command
    @commands.command(name="dice", aliases=["roll"])
    async def dice_command(self, ctx, die_num: int = 6):
        await ctx.send(f"The dice returned {random.randint(0, die_num)}!")



#Need this for every cog to run
def setup(bot):
    bot.add_cog(FunCommands(bot))

