# followed tutorial: https://github.com/Carberra/discord.py-music-tutorial/blob/master/bot/cogs/music.py
# some functions are stripped
# new player based on wavelink + lavalink
import asyncio
import math
import random
import typing as t
import wavelink
import discord
from discord.ext import commands

'''
This cog is my attempt to rewrite the music function with wavelink
'''


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


class NoTrackFoundByProbe(commands.CommandError):
    pass


class AttemptedToRemoveCurrentTrack(commands.CommandError):
    pass


class NothingIsPlaying(commands.CommandError):
    pass


class SeekPositionOutOfBound(commands.CommandError):
    pass


class Queue:
    def __init__(self):
        self._queue = []
        self.position = 0
        self.repeat_flag = False
        self.shuffle_flag = False
        self.waiting_for_next = False  # indicates if the player is waiting for more songs while staying in the vc.

    def add(self, *args):
        self._queue.extend(args)  # multiple "append"

    def remove(self, index):
        del self._queue[index]
        if index < self.position:  # move position backwards if something before the playing song was removed
            self.position -= 1

    @property
    def getFirstTrack(self):
        if not self._queue:
            raise EmptyQueue
        return self._queue[0]

    @property
    def getNextTrack(self):
        if not self._queue:
            raise EmptyQueue
        self.waiting_for_next = False
        if self.shuffle_flag and self.waiting_for_next is False:
            self.position = random.randrange(0, self.getLength - 1, 1)
        else:
            self.position += 1
            if self.position > len(self._queue) - 1:
                print("reached end of queue.")
                self.waiting_for_next = True
                self.position -= 1  # move one step back so that the next track can be retrieved when the session is resumed
                return None
        return self._queue[self.position]

    @property
    def getCurrentTrack(self):
        if not self._queue:
            raise EmptyQueue
        return self._queue[self.position]

    @property
    def getUpcoming(self):
        if not self._queue:
            raise EmptyQueue
        return self._queue[self.position + 1:]

    @property
    def getPlayHistory(self):
        if not self._queue:
            raise EmptyQueue
        if self.position == 0:  # if it is at the top of the queue then return none.
            return None
        return self._queue[self.position - 1]  # i want to only display the last song

    def probeForTrack(self, index: int):  # probe for track in any position
        if not self._queue:
            raise EmptyQueue
        if index >= self.getLength:
            return None
        if index < 0:
            return None
        return self._queue[index]

    @property
    def getLength(self):
        return len(self._queue)

    @property
    def getPosition(self):  # get the position (track number) in the queue
        return self.position

    @property
    def getFullQueue(self):
        return self._queue

    def clearQueue(self):  # clear the entire queue
        self._queue.clear()
        self.position = 0

    def clearNotPlaying(self):  # clear the queue (but the current playing song)
        del(self._queue[self.position + 1:])  # clear upcoming songs
        del (self._queue[:self.position])  # clear played songs
        self.position = 0  # reset player queue position

    def toggleRepeat(self):
        self.repeat_flag = not self.repeat_flag

    def toggleShuffle(self):
        self.shuffle_flag = not self.shuffle_flag

    def jump(self, index: int):
        self.position = index - 1


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
        if isinstance(tracks, wavelink.TrackPlaylist):
            self.queue.add(*tracks.tracks)
        else:
            self.queue.add(tracks[0])

        if not self.is_playing:
            await self.startPlaying()

    async def startPlaying(self):
        if self.queue.waiting_for_next:
            await self.play(self.queue.getNextTrack)
        else:
            await self.play(self.queue.getFirstTrack)

    async def advance(self):
        try:
            track = self.queue.getNextTrack
            if track is not None:
                await self.play(track)
        except:
            pass

    async def repeatTrack(self):
        current = self.queue.getCurrentTrack
        await self.play(current)


class Music(commands.Cog, wavelink.WavelinkMixin):

    def __init__(self, bot):
        self.bot = bot
        if not hasattr(bot, 'wavelink'):
            self.bot.wavelink = wavelink.Client(bot=self.bot)

        self.bot.loop.create_task(self.start_nodes())

    async def start_nodes(self):  # connect to a lavalink node
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
        print("Lavalink is ready!")

    @wavelink.WavelinkMixin.listener('on_track_stuck')
    @wavelink.WavelinkMixin.listener('on_track_end')
    @wavelink.WavelinkMixin.listener('on_track_exception')  # hop to the next track when whatever happened
    async def onPlayerStop(self, node, payload):
        if payload.player.queue.repeat_flag:
            await payload.player.repeatTrack()
        else:
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
        # await ctx.send(":boom: 已清除播放清單。")
        await ctx.send(":arrow_left: 已解除連接。")

    @commands.command(name='play', aliases=['p'])
    async def _play(self, ctx, *, query: str):
        player = self.get_player(ctx)
        if not player.is_connected:
            await player.connect(ctx)

        await ctx.send(":mag_right: 正在搜尋`{}`...".format(query))
        await ctx.trigger_typing()
        #  TODO: Try regex match, perhaps??
        if 'https://' not in query:
            query = f'ytsearch:{query}'  # treat non-url queries as youtube search

        if '&list=' in query:  # if user attempts to add song with playlist open
            query = query.split('&')[0]  # strips away playlist and other stuff from url (arbitrarily)
            await ctx.send(':information_source: 如要新增播放清單，請在 play 指令後方貼上清單網址。')

        tracks = await self.bot.wavelink.get_tracks(query)
        if not tracks:
            await ctx.send(':x: 搜尋結果為空。')
            if '/playlist?' in query:
                await ctx.send(':warning: 此清單可能為私人清單，請檢查播放清單檢視權限。')

        await player.addTrack(ctx=ctx, tracks=tracks)

        # the info embed
        if '/playlist?' in query:  # if user stuffed a playlist
            track = player.current  # display the current song (cuz i can't directly access TrackPlayList, hmm)
            await ctx.send(':white_check_mark: 已成功新增播放清單。輸入 **.queue** 以查看。')
        else:
            track = tracks[0]
        title = track.title
        length = track.info['length'] / 1000
        author = track.info['author']
        url = track.info['uri']
        embed = discord.Embed(title=f"{title}", url=url)
        embed.add_field(name='上傳頻道', value=author)
        raw_duration = length
        duration = "{:02d}:{:02d}".format(int(raw_duration / 60), int(raw_duration % 60))
        embed.add_field(name='時長', value=duration, inline=True)
        # if player.queue.getUpcoming():
        #     embed.add_field(name='播放順位', value=(player.queue.getLength() - 1 - player.queue.position), inline=True)
        embed.set_author(name="{} 已將歌曲加入播放清單～♪".format(ctx.author.display_name), icon_url=ctx.author.avatar_url)

        if track.thumb is not None:
            embed.set_thumbnail(url=track.thumb)

        await ctx.send(embed=embed)

    @commands.command(name='nowplay', aliases=['np'])
    async def _nowplay(self, ctx):
        player = self.get_player(ctx)

        if not player.is_connected:
            raise NoVC

        track = player.current
        if not track:
            raise NothingIsPlaying

        title = track.title
        length = track.info['length'] / 1000
        url = track.info['uri']
        raw_pos = player.position / 1000
        duration = "{:02d}:{:02d}".format(int(length / 60), int(length % 60))
        pos = "{:02d}:{:02d}".format(int(raw_pos / 60), int(raw_pos % 60))

        progress = "{} / {}".format(pos, duration)

        if player.queue.repeat_flag:
            progress += ' :repeat_one:'

        if player.queue.shuffle_flag:
            progress += ' :twisted_rightwards_arrows:'

        if player.queue.getUpcoming:
            embed = discord.Embed(title="`{:02d}.` **{}**".format(player.queue.getPosition, title),
                                  url=url, description=progress)
        else:
            embed = discord.Embed(title="**{}**".format(title),
                                  url=url, description=progress)

        if player.is_paused:
            embed.set_author(name="已暫停",
                             icon_url=self.bot.get_guild(ctx.guild.id).icon_url)
        else:
            embed.set_author(name="現正播放～♪",
                             icon_url=self.bot.get_guild(ctx.guild.id).icon_url)

        if track.thumb is not None:
            embed.set_thumbnail(url=track.thumb)

        await ctx.send(embed=embed)
        # print(f"pos: {player.queue.position}")

    @_nowplay.error
    async def _nowplay_error(self, ctx, exception):
        if isinstance(exception, NoVC):
            await ctx.send(":zzz: 未連接至語音頻道。")
        if isinstance(exception, NothingIsPlaying):
            await ctx.send(":zzz: 沒有播放中的曲目。")

    @commands.command(name='queue', aliases=['q'])
    async def _queue(self, ctx, page: int = None):
        player = self.get_player(ctx)

        if player.queue.getLength == 0:  # if the queue is empty
            raise EmptyQueue

        if not player.is_connected:
            await ctx.send(":zzz: 未連接至語音頻道。")
            return

        # prepare the queue. load the full queue and slice them into 10 items per sublist
        index = 0
        listDuration = 0
        fullList = []
        slicedLists = []
        for track in player.queue.getFullQueue:
            length = int(track.info['length'] / 1000)
            track_info = "`{:02d}.` {} `({:02d}:{:02d})`\n".format(index,
                                                                   track.title,
                                                                   int(length / 60),
                                                                   int(length % 60))
            if index == player.queue.getPosition and player.is_playing:
                track_info = "**[{}]({})**".format(track_info, track.info['uri'])
            fullList.append(track_info)
            listDuration += length
            index += 1
        slicedLists = [fullList[i: i + 10] for i in range(0, len(fullList), 10)]  # 10 item per sub list

        if not page or page <= 0 or page > len(slicedLists):
            # automatically jump to the page where the current playing track is in,
            # if no pg num is indicated, or pg num is invalid (i.e. -1 or out of bounds)
            page = math.floor(int(player.queue.getPosition) / 10) + 1

        # prepare for the info queue
        track = player.current
        if not track:
            track = player.queue.probeForTrack(player.queue.getPosition)
        title = track.title
        length = track.info['length'] / 1000
        url = track.info['uri']
        raw_pos = player.position / 1000
        duration = "{:02d}:{:02d}".format(int(length / 60), int(length % 60))
        pos = "{:02d}:{:02d}".format(int(raw_pos / 60), int(raw_pos % 60))
        thumb = track.thumb

        # display specific page of sliced list
        queueDisp = ''
        for track_info in slicedLists[page - 1]:
            queueDisp += track_info

        progress = "{} / {}".format(pos, duration)

        if player.queue.repeat_flag:
            progress += ' :repeat_one:'

        if player.queue.shuffle_flag:
            progress += ' :twisted_rightwards_arrows:'

        embed = discord.Embed(title="`{:02d}.` **{}**".format(player.queue.getPosition, title),
                              url=url, description=progress)

        embed.set_author(name="{} 的播放清單～♪".format(self.bot.get_guild(ctx.guild.id).name),
                         icon_url=self.bot.get_guild(ctx.guild.id).icon_url)

        if player.queue.getFullQueue:
            embed.add_field(name="播放清單 ({}首 • 總時長 {:02d}:{:02d} • 頁數 {} / {})".format(player.queue.getLength,
                                                                                      int(listDuration / 60),
                                                                                      int(listDuration % 60),
                                                                                      page, len(slicedLists)),
                            value=queueDisp,
                            inline=False)

        if thumb is not None:
            embed.set_thumbnail(url=thumb)

        if player.queue.waiting_for_next:
            embed.set_footer(text='播放器閒置中。請使用.play指令繼續點歌，或使用.pr / .jump指令回到上一首或指定曲目。')

        await ctx.send(embed=embed)

    @_queue.error
    async def _queue_error(self, ctx, exception):
        if isinstance(exception, EmptyQueue):
            await ctx.send(':u7a7a: 播放清單為空。')

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
        if player.queue.repeat_flag:
            player.queue.toggleRepeat()
            await ctx.send(':arrow_right: 已自動停用單曲循環播放。')

        if not player.queue.getUpcoming:
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

    @commands.command(name='previous', aliases=['pr', 'prev'])
    async def _previous(self, ctx):
        player = self.get_player(ctx)

        if player.queue.waiting_for_next:  # if user decided to go backward while the player is waiting
            await(player.play(player.queue.probeForTrack(player.queue.position)))  # pick up the current song and play it again
            player.queue.waiting_for_next = False  # remember to flip this back to false, cause the player is not waiting for new song now...
        else:
            if not player.queue.getPlayHistory:
                raise NoPrevSong

            if player.queue.position <= 0:  # if the player is beyond the top of queue (cap pos at 0)
                player.queue.position = 0
                raise NoPrevSong

            player.queue.position -= 2  # step back 2 steps first
            await player.stop()  # then let it advance 1 step
        await ctx.send(":track_previous: 上一首！")

        await ctx.invoke(self.bot.get_command('nowplay'))

    @_previous.error
    async def _previous_error(self, ctx, exception):
        player = self.get_player(ctx)
        if isinstance(exception, NoPrevSong):
            if player.queue.waiting_for_next:
                await player.play(player.queue.probeForTrack(player.queue.position))
                await ctx.send(":track_previous: 上一首！")
                await ctx.invoke(self.bot.get_command('nowplay'))
            else:
                await ctx.send(":warning: 到頂了喔。")
        if isinstance(exception, EmptyQueue):
            await ctx.send(":u7a7a: 播放清單為空。")

    @commands.command(name='loop', aliases=['lp', 'repeat'])
    async def _repeat(self, ctx):
        player = self.get_player(ctx)
        player.queue.toggleRepeat()
        if player.queue.repeat_flag:
            await ctx.send(':repeat_one: 單曲循環播放已啟用。')
        else:
            await ctx.send(':arrow_right: 單曲循環播放已停用。')

    @commands.command(name='shuffle', aliases=['shuf', 'sh'])
    async def _shuffle(self, ctx):
        player = self.get_player(ctx)
        player.queue.toggleShuffle()
        if player.queue.shuffle_flag:
            await ctx.send(':twisted_rightwards_arrows: 隨機播放已啟用。')
        else:
            await ctx.send(':arrow_right: 隨機播放已停用。')

    @commands.command(name='remove', aliases=['rm'])
    async def _remove(self, ctx, index: int):
        player = self.get_player(ctx)
        if not player.is_connected:
            raise NoVC

        if not player.queue.probeForTrack(index):
            raise NoTrackFoundByProbe
        if index == player.queue.getPosition:
            raise AttemptedToRemoveCurrentTrack
        if index < 0:
            raise NoTrackFoundByProbe

        track = player.queue.probeForTrack(index)
        player.queue.remove(index)
        await ctx.send(f':white_check_mark: 已從播放清單移除 **{track.title}**。')
        await ctx.invoke(self.bot.get_command('queue'))

    @_remove.error
    async def _remove_error(self, ctx, exception):
        if isinstance(exception, NoTrackFoundByProbe):
            await ctx.send(':warning: 曲目編號超出範圍。')
        if isinstance(exception, EmptyQueue):
            await ctx.send(':u7a7a: 播放清單為空。')
        if isinstance(exception, AttemptedToRemoveCurrentTrack):
            await ctx.send(':x: 無法移除播放中的曲目。')
        if isinstance(exception, NoVC):
            await ctx.send(':zzz: 未連接至語音頻道。')

    @commands.command(name='save', aliases=['s'])  # need error handler
    async def _save(self, ctx):
        player = self.get_player(ctx)

        if not player.is_connected:
            await ctx.send(":zzz: 未連接至語音頻道。")
            return

        track = player.current

        if not track:
            await ctx.send(":zzz: 沒有播放中的曲目。")
            return

        title = track.title
        length = track.info['length'] / 1000
        url = track.info['uri']
        duration = "{:02d}:{:02d}".format(int(length / 60), int(length % 60))

        embed = discord.Embed(title="**{}**".format(title),
                              url=url, description="{}".format(url))
        embed.set_author(name="早安啊，這是你剛剛存下來的曲子♪", icon_url=self.bot.user.avatar_url)

        if track.thumb is not None:
            embed.set_thumbnail(url=track.thumb)

        await ctx.message.author.send(embed=embed)
        await ctx.send(":white_check_mark: 已將歌曲資訊傳送到私訊！")

    @commands.command(name='seek', aliases=['se'])
    async def _seek(self, ctx, pos: str = None):
        player = self.get_player(ctx)

        if not player.is_connected:
            raise NoVC

        track = player.current
        if not track:
            raise NothingIsPlaying

        if pos is not None:
            if ':' in pos:  # support for format like xx:xx
                converted_pos = pos.split(':')
                seek = (int(converted_pos[0]) * 60 + int(converted_pos[1])) * 1000
            else:  # if number is directly input
                seek = int(pos) * 1000

            if seek > player.current.length or seek < 0:
                raise SeekPositionOutOfBound

            seekDisp = int(seek / 1000)
            await player.seek(position=seek)
            await ctx.send(':fast_forward: 已跳轉至 **{:02d}:{:02d}**'.format(int(seekDisp / 60), seekDisp % 60))
            await ctx.invoke(self.bot.get_command('nowplay'))

    @_seek.error
    async def _seek_error(self, ctx, exception):
        if isinstance(exception, NoVC):
            await ctx.send(':zzz: 未連接至語音頻道。')
        if isinstance(exception, NothingIsPlaying):
            await ctx.send(":zzz: 沒有播放中的曲目。")
        if isinstance(exception, SeekPositionOutOfBound):
            await ctx.send(":x: 指定的時間點超出歌曲範圍。")

    @commands.command(name='fastforward', aliases=['ff'])
    async def _fast_forward(self, ctx, step: int = None):
        player = self.get_player(ctx)
        if step:
            pos = int(player.position / 1000) + step
            await ctx.invoke(self.bot.get_command('seek'), pos=str(pos))
            if step < 0:
                msg = await ctx.send(':information_source: 下次要不要考慮試試看 **.rew**？')
                await asyncio.sleep(1)
                await msg.delete()

    @_fast_forward.error
    async def _fast_forward_error(self, ctx, exception):
        if isinstance(exception, NoVC):
            await ctx.send(':zzz: 未連接至語音頻道。')
        if isinstance(exception, NothingIsPlaying):
            await ctx.send(":zzz: 沒有播放中的曲目。")
        if isinstance(exception, SeekPositionOutOfBound):
            await ctx.send(":x: 指定的時間點超出歌曲範圍。")

    @commands.command(name='rewind', aliases=['rew'])
    async def _rewind(self, ctx, step: int = None):
        player = self.get_player(ctx)
        if step:
            pos = int(player.position / 1000) - step
            await ctx.invoke(self.bot.get_command('seek'), pos=str(pos))
            if step < 0:
                msg = await ctx.send(':information_source: 下次要不要考慮試試看 **.ff**？')
                await asyncio.sleep(1)
                await msg.delete()

    @_rewind.error
    async def _rewind_error(self, ctx, exception):
        if isinstance(exception, NoVC):
            await ctx.send(':zzz: 未連接至語音頻道。')
        if isinstance(exception, NothingIsPlaying):
            await ctx.send(":zzz: 沒有播放中的曲目。")
        if isinstance(exception, SeekPositionOutOfBound):
            await ctx.send(":x: 指定的時間點超出歌曲範圍。")

    @commands.command(name='replay', aliases=['rp'])  # shorthand to '.seek 0'
    async def _replay(self, ctx):
        await ctx.invoke(self.bot.get_command('seek'), pos='0')

    @commands.command(name='clear', aliases=['cl'])  # clears everything in the queue (but keeps the one's playing if player's not waiting)
    async def _clear(self, ctx):
        player = self.get_player(ctx)

        if player.queue.getLength == 0:  # if the queue is empty
            raise EmptyQueue

        if not player.is_connected:
            await ctx.send(":zzz: 沒有播放中的曲目，或未連接至語音頻道。")
            return

        if player.queue.waiting_for_next:
            player.queue.clearQueue()
            await ctx.send(':boom: 已清除播放清單。')
        else:
            player.queue.clearNotPlaying()
            await ctx.send(':boom: 已清除播放清單（保留當前曲目）。')

        if player.queue.shuffle_flag:
            player.queue.shuffle_flag = False
            await ctx.send(':arrow_right: 已自動停用隨機播放。')

    @_clear.error
    async def _clear_error(self, ctx, exception):
        if isinstance(exception, EmptyQueue):
            await ctx.send(":u7a7a: 播放清單為空。")

    @commands.command(name='jump', aliases=['j', 'jmp'])
    async def _jump(self, ctx, step: int):
        player = self.get_player(ctx)
        if not player.is_connected:
            raise NoVC

        index = step
        if not player.queue.probeForTrack(index):
            raise NoTrackFoundByProbe

        if player.queue.repeat_flag:
            player.queue.toggleRepeat()
            await ctx.send(':arrow_right: 已自動停用單曲循環播放。')

        player.queue.jump(index)
        await player.stop()

        if player.queue.waiting_for_next:  # if the player is waiting for the next song, and user decided to jump to track...
            await player.advance()  # then do an advance
            player.queue.waiting_for_next = False

        await ctx.send(":track_next: 跳過！")

        await ctx.invoke(self.bot.get_command('nowplay'))

    @_jump.error
    async def _jump_error(self, ctx, exception):
        if isinstance(exception, NoTrackFoundByProbe):
            await ctx.send(':warning: 曲目編號超出範圍。')
        if isinstance(exception, EmptyQueue):
            await ctx.send(':u7a7a: 播放清單為空。')
        if isinstance(exception, AttemptedToRemoveCurrentTrack):
            await ctx.send(':x: 無法移除播放中的曲目。')
        if isinstance(exception, NoVC):
            await ctx.send(':zzz: 未連接至語音頻道。')


def setup(bot):
    bot.add_cog(Music(bot))
    print("Wavelink (Lavalink) Music player loaded.")
