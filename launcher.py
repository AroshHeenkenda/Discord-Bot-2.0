"""
Author: Arosh Heenkenda
Created: 12/01/2022
Edited: 13/02/2022
Purpose: Launcher file for the discord bot.
"""

#Imports
from bot import AroshBot

#Main function creates the bot and runs itjava
def main():
    bot = AroshBot()
    bot.run()

#Ensures can only be run from here
if __name__ == "__main__":
    main()

#Need to run Lavalink server
# C:\Users\Arosh Heenkenda\Desktop\Coding Projects\Discord Bot 2.0\jdk-13.0.2\bin -> then write java -jar Lavalink.jar