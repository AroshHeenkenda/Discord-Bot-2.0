"""
Author: Arosh Heenkenda
Created: 12/01/2022
Edited: 16/02/2022
Purpose: Music playback commands to be imported into other python files.
"""

#Imports
import random
import asyncio
import datetime as dt
import re
import typing as t
import discord
import wavelink
from discord.ext import commands
from enum import Enum

#Constants
URL_REGEX = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
OPTIONS = {
    "1️⃣": 0,
    "2⃣": 1,
    "3⃣": 2,
    "4⃣": 3,
    "5⃣": 4,
}

#---------------------------------------------------------------------------------------------------

#Error Handling Classes
class AlreadyConnectedToChannel(commands.CommandError):
    pass

class NoVoiceChannel(commands.CommandError):
    pass

class QueueIsEmpty(commands.CommandError):
    pass

class NoTracksFound(commands.CommandError):
    pass

class PlayerIsAlreadyPaused(commands.CommandError):
    pass

class PlayerIsAlreadyPlaying(commands.CommandError):
    pass

class NoMoreTracks(commands.CommandError):
    pass

class NoPreviousTracks(commands.CommandError):
    pass

class InvalidRepeatMode(commands.CommandError):
    pass


#Volume Control Error Handling Classes
class VolumeTooLow(commands.CommandError):
    pass

class VolumeTooHigh(commands.CommandError):
    pass

class MaxVolume(commands.CommandError):
    pass

class MinVolume(commands.CommandError):
    pass


#Repeat Mode Class
class RepeatMode(Enum): #Enums can be used instead of if statements allow for extra readability
    NONE = 0
    ONE = 1
    ALL = 2

#-----------------------------------------------------------------------------------------------------------------
#CLASSES THAT LINK TO THE COG & COMMANDS

#QUEUE CLASS
class Queue:
    #Initialisation
    def __init__(self):
        self._queue = [] #private variable, empty list
        self.position = 0 #public variable, set to 0
        self.repeat_mode = RepeatMode.NONE #public variable, repeat mode set to None

    #PROPERTIES FOR QUEUE CLASS
    #Defines if the queue is empty
    @property
    def is_empty(self):
        return not self._queue #returns a boolean

    #Returns the first track
    @property
    def first_track(self):
        #Error handling if the queue is empty
        if not self._queue:
            raise QueueIsEmpty
        #get first element from the queue list
        return self._queue[0]


    #Gets current track playing
    @property
    def current_track(self):
        #Error hadling if queue is empty
        if not self._queue:
            raise QueueIsEmpty
        #As long as position is not greater than number of tracks, will return the track at that position
        if self.position <= len(self._queue) - 1:
            return self._queue[self.position]

    #Shows list of tracks to come
    @property
    def upcoming(self):
        #Error handling if the queue is empty
        if not self._queue:
            raise QueueIsEmpty
        #If not empty return all tracks that are beyond the current track
        return self._queue[self.position + 1:]

    #Shows previously played songs
    @property
    def history(self):
        #Error handling if queue is empty
        if not self._queue:
            raise QueueIsEmpty
        #Else will return previously played songs, from the position
        return self._queue[:self.position]

    #Length of the queue
    @property
    def length(self):
        return len(self._queue)

    #FUNCTIONS FOR QUEUE CLASS
    #Adding a track to the queue
    def add(self, *args):
        self._queue.extend(args) #use extend method to add song


    #Function to get the next track
    def get_next_track(self):
        #raise an error when the queue is empty
        if not self._queue:
            raise QueueIsEmpty

        #If not empty, increment the position
        self.position += 1

        if self.position < 0:
            return None

        #If the position is greater than the max position, returns None signifies end of queue
        elif self.position > len(self._queue) - 1:
            if self.repeat_mode == RepeatMode.ALL:
                self.position = 0
            else:
                return None

        #else -> returns the element at that position in the queue
        return self._queue[self.position]


    #Shuffling queue method
    def shuffle(self):
        #Raise an error if the queue is empty
        if not self._queue:
            raise QueueIsEmpty
        #Shuffling functionality, by altering exisitng list onwards
        upcoming = self.upcoming
        random.shuffle(upcoming)
        self._queue = [*self._queue[:self.position + 1]]
        self._queue.extend(upcoming)
        #random.shuffle(self._queue) -> shuffles whole tracklist


    #Set repeat mode
    def set_repeat_mode(self, mode):
        if mode == "none":
            self.repeat_mode = RepeatMode.NONE
        elif mode == "1":
            self.repeat_mode = RepeatMode.ONE
        elif mode == "all":
            self.repeat_mode = RepeatMode.ALL


    #Method to empty the queue
    def empty(self):
        self._queue.clear()
        self.position = 0 #reset the position


#PLAYER CLASS
class Player(wavelink.Player):
    #Initialisation
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue = Queue() #public queue variable calls Queue Class


    #Connect Function
    async def connect(self, ctx, channel=None):
        #Raise error if bot already connected to a channel
        if self.is_connected:
            raise AlreadyConnectedToChannel

        #Raise an error if there is no voice channel to join
        if (channel := getattr(ctx.author.voice, "channel", channel)) is None:
            raise NoVoiceChannel

        #Else will connect to a channel
        await super().connect(channel.id) #note can't use self, as we've overwritten it in the def
        return channel


    #Disconnect Function
    async def teardown(self):
        try:
            await self.destroy()
        except KeyError:
            pass


    #Add Tracks Function
    async def add_tracks(self, ctx, tracks):
        #If there are no tracks, raise an error
        if not tracks:
            raise NoTracksFound

        #If there are tracks (as a link)
        if isinstance(tracks, wavelink.TrackPlaylist):
            self.queue.add(*tracks.tracks)

        #If there is only 1 track in the queue, add it
        elif len(tracks) == 1:
            self.queue.add(tracks[0])
            await ctx.send(f"Added {tracks[0].title} to the queue.")

        #Else, if the track chosen isn't none, add it to the queue
        else:
            if (track := await self.choose_track(ctx, tracks)) is not None:
                self.queue.add(track)
                await ctx.send(f"Added {track.title} to the queue.")

        #If nothing is playing and the queue isn't empty, start playback
        if not self.is_playing and not self.queue.is_empty:
            await self.start_playback()


    #Choose Track Function
    async def choose_track(self, ctx, tracks):
        #Function that checks to see the person who replies is the one that asked for the track
        def _check(r, u): #where 'r' is reply and 'u' is user
            return (
                r.emoji in OPTIONS.keys()
                and u == ctx.author
                and r.message.id == msg.id
            )

        #Creating an embed
        embed = discord.Embed(
            title = "Choose a song",
            description=(
                "\n".join(
                    f"**{i+1}.** {t.title} ({t.length//60000}:{str(t.length%60).zfill(2)})"
                    for i, t in enumerate(tracks[:5])
                )
            ),
            colour=ctx.author.colour,
            timestamp=dt.datetime.utcnow()
        )
        #More embed properties
        embed.set_author(name="Query Results")
        embed.set_footer(text=f"Invoked by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)

        #Send the message and the associated reaction emojis
        msg = await ctx.send(embed=embed)
        for emoji in list(OPTIONS.keys())[:min(len(tracks), len(OPTIONS))]:
            await msg.add_reaction(emoji)

        try:
            reaction, _ = await self.bot.wait_for("reaction_add", timeout=60.0, check=_check)
        #Deletes message if reaches timeout time
        except asyncio.TimeoutError:
            await msg.delete()
            await ctx.message.delete()
        #Else will add the track, and delete the embed message
        else:
            await msg.delete()
            return tracks[OPTIONS[reaction.emoji]]


    #Start Playback function
    async def start_playback(self):
        await self.play(self.queue.current_track)    #had instead await self.play(self.queue.first_track) THIS IS WRONG


    #Advance function
    async def advance(self):
        try:
            if (track := self.queue.get_next_track()) is not None:
                await self.play(track)
        except QueueIsEmpty:
            pass

    #Repeat track function
    async def repeat_track(self):
        await self.play(self.queue.current_track)


#-------------------------------------------------------------------------------------------


#MUSIC CLASS (USING COGS & COMMANDS)
class Music(commands.Cog, wavelink.WavelinkMixin):#commands.Cog and wavelink.WavelinkMixin has listeners you can use
    #Initialisation
    def __init__(self, bot):
        self.bot = bot
        self.wavelink = wavelink.Client(bot=bot)
        self.bot.loop.create_task(self.start_nodes())

    #State of the voice channel
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not member.bot and after.channel is None:
            if not [m for m in before.channel.members if not m.bot]:
                #Disconnect the bot from the channel, when no one else is there
                await self.get_player(member.guild).teardown()
                #await ctx.send("Disconnected due to inactivity.")

    #Tells us the node is ready to use
    @wavelink.WavelinkMixin.listener()
    async def on_node_ready(self, node):
        print(f"Wavelink node '{node.identifier}' ready.")

    @wavelink.WavelinkMixin.listener("on_track_stuck")
    @wavelink.WavelinkMixin.listener("on_track_end")
    @wavelink.WavelinkMixin.listener("on_track_exception")
    async def on_player_stop(self, node, payload):
        if payload.player.queue.repeat_mode == RepeatMode.ONE:
            await payload.player.repeat_track()
        else:
            await payload.player.advance()

    @commands.Cog.listener()
    async def on_ready(self):
        print("'Music' cog ready...")

    async def cog_check(self, ctx):
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.send("Music commands are not available in DMs.")
            return False

        return True

    #Start all our nodes
    async def start_nodes(self):
        await self.bot.wait_until_ready()

        #Nodes need to be in dictionary
        nodes = {
            "MAIN": {
                "host": "127.0.0.1",
                "port": 2333,
                "rest_uri": "http://127.0.0.1:2333",
                "password": "youshallnotpass",
                "identifier": "MAIN",
                "region": "europe",
            }
        }

        for node in nodes.values():
            await self.wavelink.initiate_node(**node)

    #Utility to get player
    def get_player(self, obj):
        if isinstance(obj, commands.Context):
            return self.wavelink.get_player(obj.guild.id, cls=Player, context=obj)
        elif isinstance(obj, discord.Guild):
            return self.wavelink.get_player(obj.id, cls=Player)


    #Connect to Voice Channel Command
    @commands.command(name="connect", alias=["join"])
    #channel: t.Optional[discord.VoiceChannel] ->optional argument if player wants to specify the vc
    async def connect_command(self, ctx, *, channel: t.Optional[discord.VoiceChannel]):
        player = self.get_player(ctx)
        channel = await player.connect(ctx, channel)
        await ctx.send(f"Connected to {channel.name}.")

    #Error Handling for Connect to Voice Channel Command
    @connect_command.error
    async def connect_command_error(self, ctx, exc):
        if isinstance(exc, AlreadyConnectedToChannel):
            await ctx.send("Already connected to a voice channel.")
        elif isinstance(exc, NoVoiceChannel):
            await ctx.send("No suitable voice channel was provided.")


    #Disconnect Command
    @commands.command(name="disconnect", alias=["leave"])
    async def disconnect_command(self, ctx):
        player = self.get_player(ctx)
        await player.teardown()
        await ctx.send("Disconnected.")


    #Play Command
    @commands.command(name="play")
    async def play_command(self, ctx, *, query: t.Optional[str]):
        player = self.get_player(ctx)

        #If the player isn't connected, will connect it
        if not player.is_connected:
            await player.connect(ctx)

        #Resumes playback is paused
        if query is None:
            #Error handling if player is playing
            #if not player.is_paused:
            #    raise PlayerIsAlreadyPlaying
            if player.is_playing and not player.is_paused:
                raise PlayerIsAlreadyPlaying

            #Error handling if queue is empty
            if player.queue.is_empty:
                raise QueueIsEmpty

            #Otherwise resume playback
            await player.set_pause(False)
            await ctx.send("Playback resumed.")

        else:
            query = query.strip("<>") #get rid of embedd link
            if not re.match(URL_REGEX, query):
                query = f"ytsearch:{query}"

            await player.add_tracks(ctx, await self.wavelink.get_tracks(query))

    #Error Handling for Play Command
    @play_command.error
    async def play_command_error(self, ctx, exc):
        #If player is playing a song
        if isinstance(exc, PlayerIsAlreadyPlaying):
            await ctx.send("Already playing.")
        #If the queue is empty
        elif isinstance(exc, QueueIsEmpty):
            await ctx.send("No songs to play, as queue is empty.")
        elif isinstance(exc, NoVoiceChannel):
            await ctx.send("No suitable voice channel was provided.")


    #Pause Command
    @commands.command(name="pause")
    async def pause_command(self, ctx):
        player = self.get_player(ctx)

        #Error handling if already paused
        if player.is_paused:
            raise PlayerIsAlreadyPaused

        #Else pauses playback
        await player.set_pause(True)
        await ctx.send("Playback paused.")

    #Error handling for pause command
    @pause_command.error
    async def pause_command_error(self, ctx, exc):
        if isinstance(exc, PlayerIsAlreadyPaused):
            await ctx.send("Playback is already paused.")


    #Stop Command
    @commands.command(name="stop")
    async def stop_command(self, ctx):
        player = self.get_player(ctx)
        player.queue.empty()
        await player.stop()
        await ctx.send("Playback stopped.")


    #Skip Command
    @commands.command(name="next", aliases=["skip"])
    async def next_command(self, ctx):
        player = self.get_player(ctx)

        #Error handling if no more tracks to play
        if not player.queue.upcoming:
            raise NoMoreTracks

        await player.stop()
        await ctx.send("Playing next track in queue.")

    #Error Handing for Skip Command
    @next_command.error
    async def next_command_error(self, ctx, exc):
        #If queue is empty
        if isinstance(exc, QueueIsEmpty):
            await ctx.send("A skip could not be executed as the queue is currently empty.")
        #If there are no more tracks to play onwards
        elif isinstance(exc, NoMoreTracks):
            await ctx.send("There are no more tracks in the queue.")


    #Previous Command
    @commands.command(name="previous")
    async def previous_command(self, ctx):
        player = self.get_player(ctx)

        #Error handling if no more previous tracks to play
        if not player.queue.history:
            raise NoPreviousTracks

        #Botching this by manually offsetting the queue position
        player.queue.position -= 2
        await player.stop()
        await ctx.send("Playing previous track in queue.")

    #Error handing for Previous Command
    @previous_command.error
    async def previous_command_error(self, ctx, exc):
        # If queue is empty
        if isinstance(exc, QueueIsEmpty):
            await ctx.send("This could not be executed as the queue is currently empty.")
        # If there are no more tracks to play onwards
        elif isinstance(exc, NoPreviousTracks):
            await ctx.send("There are no previous tracks in the queue.")


    #Shuffle Command
    @commands.command(name="shuffle")
    async def shuffle_command(self, ctx):
        player = self.get_player(ctx)
        player.queue.shuffle()
        await ctx.send("Queue shuffled.")

    #Error handling for Shuffle Command
    @shuffle_command.error
    async def shuffle_command_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            await ctx.send("The queue could not be shuffled, as it is currently empty.")


    #Repeating command
    @commands.command(name="repeat")
    async def repeat_command(self, ctx, mode: str):
        if mode not in ("none", "1", "all"):
            raise InvalidRepeatMode

        player = self.get_player(ctx)
        player.queue.set_repeat_mode(mode)
        await ctx.send(f"The repeat mode has been set to {mode}.")


    #Queue Command
    @commands.command(name="queue")
    async def queue_command(self, ctx, show: t.Optional[int] = 10):
        player = self.get_player(ctx)

        #error handling if queue is empty
        if player.queue.is_empty:
            raise QueueIsEmpty

        embed = discord.Embed(
            title="Queue",
            description=f"Showing up to next {show} tracks.",
            colour=ctx.author.colour,
            timestamp=dt.datetime.utcnow()
        )
        embed.set_author(name="Query Results")
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)
        embed.add_field(name="Currently playing",
                        value=getattr(player.queue.current_track, "title", "No tracks currently playing."),
                        inline=False)
        if upcoming := player.queue.upcoming:
            embed.add_field(
                name="Next up",
                value="\n".join(t.title for t in player.queue.upcoming[:show]),
                inline=False
            )

        msg = await ctx.send(embed=embed)

    #Error Handling for Queue Command
    @queue_command.error
    async def queue_command_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            await ctx.send("The queue is currently empty.")


    #Volume control
    @commands.group(name="volume", invoke_without_command=True)
    async def volume_group(self, ctx, volume: int):
        player = self.get_player(ctx)

        if volume < 0:
            raise VolumeTooLow

        if volume > 150:
            raise VolumeTooHigh

        await player.set_volume(volume)
        await ctx.send(f"Volume set to {volume:,}%")

    #Volume control error handling
    @volume_group.error
    async def volume_group_error(self, ctx, exc):
        if isinstance(exc, VolumeTooLow):
            await ctx.send("The volume must be 0% or above.")
        elif isinstance(exc, VolumeTooHigh):
            await ctx.send("The volume must be 150% or below.")

    #Volume Up
    @volume_group.command(name="up")
    async def volume_up_command(self, ctx):
        player = self.get_player(ctx)

        if player.volume == 150:
            raise MaxVolume
        await player.set_volume(value := min(player.volume+ 10, 150))
        await ctx.send(f"Volume set to {value:,}%")

    #Volume Up Error Handling
    @volume_up_command.error
    async def volume_up_command_error(self, ctx, exc):
        if isinstance(exc, MaxVolume):
            await ctx.send("The player is already at max volume.")

    #Volume Down
    @volume_group.command(name="down")
    async def volume_down_command(self, ctx):
        player = self.get_player(ctx)

        if player.volume == 0:
            raise MinVolume
        await player.set_volume(value := max(0, player.volume -10))
        await ctx.send(f"Volume set to {value:,}%")

    #Volume Down Error Handling
    @volume_down_command.error
    async def volume_down_command_error(self, ctx, exc):
        if isinstance(exc, MinVolume):
            await ctx.send("The player is already at min volume.")

#---------------------------------------------------------------------------------------------------------------------

#Bot Setup, must do this for all cogs
def setup(bot):
    bot.add_cog(Music(bot))
