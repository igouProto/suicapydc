# adapted from tutorial: https://github.com/Carberra/discord.py-music-tutorial/blob/master/bot/cogs/music.py

import asyncio
import async_timeout
import typing as t
# wavelink module
import wavelink

# discord py modules
import discord
from discord.ext import commands
import asyncio

'''
This cog is my attempt to rewrite the music function with wavelink
'''

players = {}
queues = {}
loopQueues = {}
timers = {}

pauseFlags = {}
loopFlags = {}
isLooping = {}

loopCount = {}


class AlreadyConnected(commands.CommandError):
    pass

class NoVC(commands.CommandError):
    pass

class EmptyQueue(commands.CommandError):
    pass

class PlayerAlreadyPaused(commands.CommandError):
    pass

class NoMoreSongs(commands.CommandError):
    pass

class NoPrevSong(commands.CommandError):
    pass

class Queue:
    def __init__(self):
        self._queue = []
        self.position = 0

    def add(self, *args):
        self._queue.extend(args)  # multiple "append"
        print(len(self._queue))

    def getFirstTrack(self):
        if not self._queue:
            raise EmptyQueue
        return self._queue[0]

    def getNextTrack(self):
        if not self._queue:
            raise EmptyQueue
        self.position += 1
        if self.position > len(self._queue) - 1:
            print("reached end of queue")
            return None
        return self._queue[self.position]

    def getCurrentTrack(self):
        if not self._queue:
            raise EmptyQueue
        return self._queue[self.position]

    def getUpcoming(self):
        if not self._queue:
            raise EmptyQueue
        return self._queue[self.position + 1:]

    def getPlayHistory(self):
        if not self._queue:
            raise EmptyQueue
        return self._queue[self.position - 1] # i want to only display the last song

    def getLength(self):
        return len(self._queue)

    def clearQueue(self):
        self._queue.clear()

class WavePlayer(wavelink.Player):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue = Queue()

    async def connect(self, ctx, channel=None):  # overloaded WV;s player connect
        if self.is_connected:
            raise AlreadyConnected

        channel = getattr(ctx.author.voice, "channel", channel)
        if channel is None:
            raise NoVC

        await super().connect(channel.id)
        return channel

    async def teardown(self):  # so we still need to rename this...
        try:
            await self.destroy()
        except KeyError:
            pass

    async def addTrack(self, ctx, tracks):
        # if isinstance(tracks, wavelink.TrackPlaylist):
        #    self.queue.add(*tracks.tracks)
        self.queue.add(tracks[0])
        if not self.is_playing:
            await self.startPlaying()

    async def startPlaying(self):
        # print('called startplaying')
        await self.play(self.queue.getFirstTrack())

    async def advance(self):
        try:
            track = self.queue.getNextTrack()
            if track is not None:
                await self.play(track)
        except:
            pass


class Music(commands.Cog, wavelink.WavelinkMixin):

    def __init__(self, bot):
        self.bot = bot
        if not hasattr(bot, 'wavelink'):
            self.bot.wavelink = wavelink.Client(bot=self.bot)

        self.bot.loop.create_task(self.start_nodes())

    async def start_nodes(self):
        await self.bot.wait_until_ready()

        # Initiate our nodes. For this example we will use one server.
        # Region should be a discord.py guild.region e.g sydney or us_central (Though this is not technically required)
        await self.bot.wavelink.initiate_node(host='127.0.0.1',
                                              port=2333,
                                              rest_uri='http://127.0.0.1:2333',
                                              password='igproto',
                                              identifier='MAIN',
                                              region='Hong Kong', )

    def get_player(self, obj):
        if isinstance(obj, commands.Context):
            return self.bot.wavelink.get_player(obj.guild.id, cls=WavePlayer, context=obj)
        elif isinstance(obj, discord.Guild):
            return self.bot.wavelink.get_player(obj.id, cls=WavePlayer)

    @wavelink.WavelinkMixin.listener()
    async def on_node_ready(self, node):
        print("Wavelink is ready!")

    @wavelink.WavelinkMixin.listener('on_track_stuck')
    @wavelink.WavelinkMixin.listener('on_track_end')
    @wavelink.WavelinkMixin.listener('on_track_exception')  # do smth for whatever happened
    async def onPlayerStop(self, node, payload):
        await payload.player.advance()

    @commands.command(name='join', aliases=['summon'])
    async def _summon(self, ctx, *, channel: t.Optional[discord.VoiceChannel]):
        player = self.get_player(ctx)
        channel = await player.connect(ctx, channel)
        await ctx.send(":white_check_mark: 已加入語音頻道**{}**。".format(channel.name))

    @_summon.error
    async def _summon_error(self, ctx, exception):
        if isinstance(exception, AlreadyConnected):
            await ctx.send("我已經加入語音頻道囉？")
        elif isinstance(exception, NoVC):
            await ctx.send("窩不知道你在哪裡QQ")

    @commands.command(name='disconnect', aliases=['dc'])
    async def _disconnect(self, ctx):
        player = self.get_player(ctx)
        await player.teardown()
        await ctx.send(":boom: 已清除播放清單。")
        await ctx.send(":arrow_left: 已解除連接。")

    @commands.command(name='play', aliases=['p'])
    async def _play(self, ctx, *, query: str):
        player = self.get_player(ctx)
        if not player.is_connected:
            await player.connect(ctx)

        await ctx.send(":mag_right: 正在搜尋`{}`...".format(query))
        await ctx.trigger_typing()

        if 'https://' not in query:
            query = f'ytsearch:{query}'

        tracks = await self.bot.wavelink.get_tracks(query)
        if not tracks:
            await ctx.send(':x: 搜尋結果為空。')

        await player.addTrack(ctx=ctx, tracks=tracks)

        # the info embed
        track = tracks[0]
        title = track.title
        length = track.info['length'] / 1000
        author = track.info['author']
        url = track.info['uri']
        embed = discord.Embed(title="**{}**".format(title), url=url)
        embed.add_field(name='上傳頻道', value=author)
        raw_duration = length
        duration = "{:02d}:{:02d}".format(int(raw_duration / 60), int(raw_duration % 60))
        embed.add_field(name='時長', value=duration, inline=True)
        embed.set_author(name="已將歌曲新增至播放清單～♪")
        # embed.set_footer(text='全新的播放器使用 Lavalink 作為音效引擎，全面提升品質及穩定度。借我宣傳一下 UwU')
        await ctx.send(embed=embed)

    @commands.command(name='nowplay', aliases=['np'])
    async def _nowplay(self, ctx):
        player = self.get_player(ctx)

        if not player.is_connected:
            await ctx.send(":zzz: 沒有播放中的曲目，或未連接至語音頻道。")

        track = player.current

        title = track.title
        length = track.info['length'] / 1000
        url = track.info['uri']
        raw_pos = player.position / 1000
        duration = "{:02d}:{:02d}".format(int(length / 60), int(length % 60))
        pos = "{:02d}:{:02d}".format(int(raw_pos / 60), int(raw_pos % 60))

        embed = discord.Embed(title="**{}**".format(title),
                              url=url, description="{} / {}".format(pos, duration))
        embed.set_author(name="現正播放～♪")

        await ctx.send(embed=embed)

    @commands.command(name='queue', aliases=['q'])
    async def _queue(self, ctx, show=10):
        player = self.get_player(ctx)

        if player.queue.getLength() <= 0: # if the queue is empty
            raise EmptyQueue

        if not player.is_connected:
            await ctx.send(":zzz: 沒有播放中的曲目，或未連接至語音頻道。")

        # prepare for the info queue
        track = player.current
        title = track.title
        length = track.info['length'] / 1000
        url = track.info['uri']
        raw_pos = player.position / 1000
        duration = "{:02d}:{:02d}".format(int(length / 60), int(length % 60))
        pos = "{:02d}:{:02d}".format(int(raw_pos / 60), int(raw_pos % 60))

        # prepare for the upcoming list
        next = ''
        index = 0
        for track in player.queue.getUpcoming():
            index += 1
            length = track.info['length'] / 1000
            next += ("`{:02d}.` {} **({:02d}:{:02d})**\n".format(index,
                                                                  track.title,
                                                                  int(length / 60),
                                                                  int(length % 60)))
            if len(next) >= 1500:
                break

        embed = discord.Embed(title="現正播放",
                              description="**{}** ({} / {})".format(title, pos, duration)
        )
        embed.set_author(name="{} 的播放清單～♪".format(self.bot.get_guild(ctx.guild.id).name),
                         icon_url=self.bot.get_guild(ctx.guild.id).icon_url)

        if player.queue.getLength() > 1:
            embed.add_field(name="接下來",
                            value=next,
                            inline=False
            )

        await ctx.send(embed=embed)

    @_queue.error
    async def _queue_error(self, ctx, exception):
        if isinstance(exception, EmptyQueue):
            await ctx.send(":information_source: 播放清單為空。")

    @commands.command(name='pause', aliases=['pa'])
    async def _pause(self, ctx):
        player = self.get_player(ctx)

        if player.is_paused:
            raise PlayerAlreadyPaused

        await player.set_pause(True)
        await ctx.send(":pause_button: 暫停！")

    @_pause.error
    async def _pause_error(self, ctx, exception):
        if isinstance(exception, PlayerAlreadyPaused):
            await ctx.send(":pause_button: 已經暫停了。")

    @commands.command(name='resume', aliases=['re'])
    async def _resume(self, ctx):
        player = self.get_player(ctx)
        await player.set_pause(False)
        await ctx.send(":arrow_forward: 繼續！")

    @commands.command(name='skip', aliases=['sk'])
    async def _skip(self, ctx):
        player = self.get_player(ctx)

        if not player.queue.getUpcoming():
            raise NoMoreSongs

        await player.stop()
        await ctx.send(":track_next: 跳過！")

        await ctx.invoke(self.bot.get_command('nowplay'))

    @_skip.error
    async def _skip_error(self, ctx, exception):
        player = self.get_player(ctx)

        if isinstance(exception, NoMoreSongs):
            await player.stop()
            await ctx.send(":track_next: 跳過！")
            await ctx.send(":warning: 沒歌了喔。")
        if isinstance(exception, EmptyQueue):
            await ctx.send(":information_source: 播放清單為空。")

    @commands.command(name='previous', aliases=['pr'])
    async def _previous(self, ctx):
        player = self.get_player(ctx)

        if not player.queue.getPlayHistory():
            raise NoPrevSong

        player.queue.position -= 2
        await player.stop()
        await ctx.send(":track_previous: 上一首！")

        await ctx.invoke(self.bot.get_command('nowplay'))

    @_previous.error
    async def _previous_error(self, ctx, exception):
        player = self.get_player(ctx)

        if isinstance(exception, NoPrevSong):
            await ctx.send(":warning: 到頂了喔。") # doesn't to be working hmm
        if isinstance(exception, EmptyQueue):
            await ctx.send(":information_source: 播放清單為空。")




def setup(bot):
    bot.add_cog(Music(bot))
    print("Wavelink Music player loaded.")
