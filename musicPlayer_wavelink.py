# followed tutorial: https://github.com/Carberra/discord.py-music-tutorial/blob/master/bot/cogs/music.py
# some functions are stripped
# new player based on wavelink + lavalink
import asyncio
import math
import random
import datetime
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


class AttemptedToSkipOutOfBounds(commands.CommandError):
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
            self.position = random.randint(0, self.getLength - 1)
        else:
            self.position += 1
            if self.position > len(self._queue) - 1:
                # print("reached end of queue.")
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
        del (self._queue[self.position + 1:])  # clear upcoming songs
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
        self.active_music_controller = 0
        self.bounded_channel = 0

    async def connect(self, ctx, channel=None):  # overloaded WV;s player connect
        if self.is_connected:
            raise AlreadyConnected

        channel = getattr(ctx.author.voice, "channel", channel)
        if channel is None:
            raise NoVC

        await super().connect(channel.id)
        # self.bounded_channel = channel.id
        # print(f"player bounded to {self.bounded_channel}")
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

    def time_parser(self, raw_duration: int):
        minutes, seconds = divmod(int(raw_duration), 60)  # minutes = duration / 60, second = duration % 60
        hours, minutes = divmod(int(minutes), 60)  # hours = minutes / 60, minutes = minutes % 60
        duration = []
        if hours > 0:
            duration.append(f"{hours}")
        duration.append(f"{minutes:02d}")
        duration.append(f"{seconds:02d}")
        return ":".join(duration)

    #  info embed builders
    def nowplay_embed(self, ctx, player) -> discord.Embed:
        track = player.current
        if not track:
            raise NothingIsPlaying

        # current track information
        title = track.title
        length = track.info['length'] / 1000
        url = track.info['uri']
        raw_pos = player.position / 1000
        duration = self.time_parser(length)
        pos = self.time_parser(raw_pos)

        # player status display before progress bar
        statdisp = ''  # the space for the status indicators (pause, loop, shuffle buttons)
        if player.is_paused:
            statdisp += ' :pause_button: '
        if player.queue.repeat_flag:
            statdisp += ' :repeat_one:'
        if player.queue.shuffle_flag:
            statdisp += ' :twisted_rightwards_arrows:'

        # the progress bar display
        if track.is_stream:
            progress = f"{statdisp} ` 🔴 LIVE ` "
        else:
            progress = int((raw_pos / length) * 100 / 5)
            progress_bar = "───────────────────"
            progress_bar_disp = progress_bar[:progress] + '⚪' + progress_bar[progress:]
            progress = f"{statdisp} ` {progress_bar_disp} ` {pos} / {duration}"

        if player.queue.getUpcoming:
            embed = discord.Embed(title=f"`{player.queue.getPosition:02d}.` **{title}**",
                                  url=url, description=progress)
        else:
            embed = discord.Embed(title=f"**{title}**",
                                  url=url, description=progress)

        embed.set_author(name="現正播放～♪",
                         icon_url=self.bot.get_guild(ctx.guild.id).icon_url)

        if track and track.thumb is not None:
            embed.set_thumbnail(url=track.thumb)

        now = datetime.datetime.now().strftime("%m/%d %H:%M:%S")
        embed.set_footer(text=f"上次更新：{now}")

        return embed

    def new_song_embed(self, ctx, track) -> discord.Embed:
        title = track.title
        length = track.info['length'] / 1000
        author = track.info['author']
        url = track.info['uri']
        embed = discord.Embed(title=f"{title}", url=url)
        embed.add_field(name='上傳頻道', value=author)
        raw_duration = length
        if track.is_stream:
            duration = '直播'
        else:
            duration = self.time_parser(length)
        embed.add_field(name='時長', value=duration, inline=True)
        embed.set_author(name=f"{ctx.author.display_name} 已將歌曲加入播放清單～♪", icon_url=ctx.author.avatar_url)

        if track.thumb is not None:
            embed.set_thumbnail(url=track.thumb)

        return embed

    def queue_embed(self, ctx, page, player) -> discord.Embed:
        index = 0
        list_duration = 0
        full_list = []
        sliced_lists = []
        for track in player.queue.getFullQueue:
            if track.is_stream:
                tr_length = 0
            else:
                tr_length = int(track.info['length'] / 1000)
            track_info = f"`{index:02d}.` {track.title} `({self.time_parser(tr_length)})`\n"
            if index == player.queue.getPosition and player.is_playing:
                track_info = f"**[{track_info}]({track.info['uri']})**"
            full_list.append(track_info)
            list_duration += tr_length
            index += 1
        sliced_lists = [full_list[i: i + 10] for i in range(0, len(full_list), 10)]  # 10 item per sub list

        # prepare for the info queue
        track = player.current  # get the current plyting track
        if not track:  # if nothing is playing and the player is waiting
            track = player.queue.probeForTrack(player.queue.getPosition)  # get the last played song

        title = track.title
        length = track.info['length'] / 1000
        url = track.info['uri']
        raw_pos = player.position / 1000
        duration = self.time_parser(length)
        pos = self.time_parser(raw_pos)
        thumb = track.thumb

        # display specific page of sliced list
        queue_disp = ''
        for track_info in sliced_lists[page - 1]:
            queue_disp += track_info

        # player status display before progress bar
        statdisp = ''  # the space for the status indicators (pause, loop, shuffle buttons)
        if player.is_paused:
            statdisp += ' :pause_button: '
        if player.queue.repeat_flag:
            statdisp += ' :repeat_one:'
        if player.queue.shuffle_flag:
            statdisp += ' :twisted_rightwards_arrows:'

        # the progress bar display
        if track.is_stream:
            progress = f"{statdisp} ` 🔴 LIVE `"
        else:
            progress = int((raw_pos / length) * 100 / 5)
            progress_bar = "───────────────────"
            progress_bar_disp = progress_bar[:progress] + '⚪' + progress_bar[progress:]
            progress = f"{statdisp} ` {progress_bar_disp} ` {pos} / {duration}"

        embed = discord.Embed(title=f"`{player.queue.getPosition:02d}.` **{title}**",
                              url=url, description=progress)

        formatted_queue_size = f"{player.queue.getLength} 首"
        formatted_list_length = f"總時長 {self.time_parser(list_duration)}"
        formatted_page_indicator = f'頁數 {page} / {len(sliced_lists)}'

        embed.add_field(name=f"播放清單 ({formatted_page_indicator})",
                        value=queue_disp, inline=False)

        if thumb is not None:
            embed.set_thumbnail(url=thumb)

        embed.set_footer(text=f"{formatted_queue_size} • {formatted_list_length}")
        if player.queue.waiting_for_next:
            embed.set_footer(text='播放器閒置中。請使用.play指令繼續點歌，或使用.pr / .jump指令回到上一首或指定曲目。')

        embed.set_author(name=f"{self.bot.get_guild(ctx.guild.id).name} 的播放清單～♪",
                         icon_url=self.bot.get_guild(ctx.guild.id).icon_url)

        return embed

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

    # below are music commands

    @commands.command(name='join', aliases=['summon'])
    async def _summon(self, ctx, *, channel: t.Optional[discord.VoiceChannel]):
        player = self.get_player(ctx)
        channel = await player.connect(ctx, channel)
        await ctx.send(f":white_check_mark: 已加入語音頻道**{channel.name}**。")

    @_summon.error
    async def _summon_error(self, ctx, exception):
        if isinstance(exception, AlreadyConnected):
            await ctx.send(":question: 我已經加入語音頻道囉？")
        elif isinstance(exception, NoVC):
            await ctx.send(":question: 窩不知道你在哪裡QQ")

    @commands.command(name='disconnect', aliases=['dc'])
    async def _disconnect(self, ctx, *args):
        player = self.get_player(ctx)
        if (player.is_paused or player.is_playing) and "f" not in args:  # pass f to force disconnect
            warn_reason = ""
            if player.is_paused:
                warn_reason = "發現暫停中的曲目。"
            elif player.is_playing:
                warn_reason = "發現播放中的曲目。"
            warning = await ctx.send(f":warning: {warn_reason}按一下 :regional_indicator_y: 來確定解除連接，或忽略此提示以取消。")
            await warning.add_reaction('🇾')

            def check(react, usr):
                if usr.bot:
                    return False
                if react.message.guild.id != ctx.message.guild.id:  # prevent cross-guild remote control glitch
                    return False
                else:
                    return True

            reaction = None
            while True:
                if str(reaction) == '🇾':
                    await player.teardown()
                    if player.queue.getLength > 1:
                        await ctx.send(":boom: 已清除播放清單。")
                    await ctx.send(":arrow_left: 已解除連接。")
                    break
                try:
                    reaction, user = await self.bot.wait_for('reaction_add', timeout=7,
                                                             check=check)
                except:
                    await warning.edit(content=":information_source: 已取消解除連接。")
                    await warning.clear_reactions()
                    break
            # await warning.clear_reactions()
        else:
            await player.teardown()
            if player.queue.getLength > 1:
                await ctx.send(":boom: 已清除播放清單。")
            await ctx.send(":arrow_left: 已解除連接。")

    @commands.command(name='play', aliases=['p'])
    async def _play(self, ctx, *, query: str):
        player = self.get_player(ctx)
        if not player.is_connected:
            await player.connect(ctx)

        await ctx.send(":mag_right: 正在搜尋`{}`...".format(query))
        await ctx.trigger_typing()
        #  pre-process the query string  TODO: Try regex match, perhaps??
        if 'https://' not in query:
            query = f'ytsearch:{query}'  # treat non-url queries as youtube search

        if '&list=' in query:  # if user attempts to add song with playlist open
            query = query.split('&')[0]  # strips away playlist and other stuff from url (arbitrarily)
            await ctx.send(':information_source: 如要新增播放清單，請在 play 指令後方貼上清單網址。')

        #  get the tracks and add to the player queue
        tracks = await self.bot.wavelink.get_tracks(query)
        if not tracks:
            await ctx.send(':x: 搜尋結果為空。')
            if '/playlist?' in query:
                await ctx.send(':warning: 此清單可能為私人清單，請檢查播放清單檢視權限。')
        await player.addTrack(ctx=ctx, tracks=tracks)

        # get the track info to be displayed
        if '/playlist?' in query:  # if user stuffed a playlist
            track = tracks.tracks[0]
            await ctx.send(':white_check_mark: 已成功新增播放清單。輸入 **.queue** 以查看。')
        else:
            track = tracks[0]
            embed = self.new_song_embed(ctx=ctx, track=track)
            msg = await ctx.send(embed=embed)

    @_play.error
    async def _play_error(self, ctx, exception):
        if isinstance(exception, NoVC):
            await ctx.send(":question: 窩不知道你在哪裡QQ")

    @commands.command(name='nowplay', aliases=['np'])  # now with interactive controller, yay
    async def _nowplay(self, ctx, *args: str):
        player = self.get_player(ctx)
        if not player.is_connected:
            raise NoVC

        embed = self.nowplay_embed(ctx=ctx, player=player)
        nowplay = await ctx.send(embed=embed)

        if args and '-nc' in args:  # pass -nc to disable interactive button for this display
            return
        else:
            player.active_music_controller = nowplay.id  # register the current embed as the controller
            print(f"{nowplay.guild.id}:{player.active_music_controller}")
            #  interactive buttons
            await nowplay.add_reaction('🔄')
            await nowplay.add_reaction('⏮')
            await nowplay.add_reaction('⏯️')
            await nowplay.add_reaction('⏭️')
            await nowplay.add_reaction('🔂')
            await nowplay.add_reaction('🔀')
            await nowplay.add_reaction('🔼')

            def check(react, usr):
                if usr.bot:
                    return False
                if react.message.guild.id != ctx.message.guild.id:  # prevent cross-guild remote control glitch
                    return False
                elif react.message.guild.id == ctx.message.guild.id:  # i want to be more precise (idk if it helps tho)
                    if react.message.id == player.active_music_controller:
                        return True
                    else:
                        return False
                else:
                    return False

            reaction = None
            while nowplay.id == player.active_music_controller and not player.queue.waiting_for_next:
                if str(reaction) == '⏮':
                    if player.queue.position > 0 and not player.queue.waiting_for_next:
                        if player.queue.repeat_flag:
                            player.queue.repeat_flag = False
                        player.queue.position -= 2
                        await player.stop()
                        new_player = self.get_player(ctx)
                        await asyncio.sleep(0.5)
                        await nowplay.edit(embed=self.nowplay_embed(ctx=ctx, player=new_player))
                elif str(reaction) == '⏯️':
                    if player.is_paused:
                        await player.set_pause(False)
                    else:
                        await player.set_pause(True)
                    await nowplay.edit(embed=self.nowplay_embed(ctx=ctx, player=player))
                elif str(reaction) == '⏭️':
                    if player.queue.getUpcoming:
                        if player.queue.repeat_flag:
                            player.queue.repeat_flag = False
                        await player.stop()
                        new_player = self.get_player(ctx)
                        await asyncio.sleep(0.5)
                        await nowplay.edit(embed=self.nowplay_embed(ctx=ctx, player=new_player))
                elif str(reaction) == '🔂':
                    player.queue.toggleRepeat()
                    await nowplay.edit(embed=self.nowplay_embed(ctx=ctx, player=player))
                elif str(reaction) == '🔀':
                    player.queue.toggleShuffle()
                    await nowplay.edit(embed=self.nowplay_embed(ctx=ctx, player=player))
                elif str(reaction) == '🔄':
                    await nowplay.edit(embed=self.nowplay_embed(ctx=ctx, player=player))
                elif str(reaction) == '🔼':  # break to hide the controls
                    player.active_music_controller = 0
                    break
                try:
                    reaction, user = await self.bot.wait_for('reaction_add',
                                                             timeout=20,
                                                             check=check)  # close the controller after being idle 10 minutes
                    await nowplay.remove_reaction(reaction, user)
                except:  # when in doubt, break. whatever.
                    player.active_music_controller = 0
                    break
            await nowplay.clear_reactions()

            if (not player.queue.waiting_for_next) and player.is_connected:
                embed = self.nowplay_embed(ctx=ctx, player=player)
                now = datetime.datetime.now().strftime("%m/%d %H:%M:%S")
                embed.set_footer(text=f'按鈕已隱藏。用 .np 以叫出新的操作面板。上次更新：{now}')
                await nowplay.edit(embed=embed)

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

        if not page or page <= 0 or page > math.ceil(player.queue.getLength / 10):
            # if no pg num is indicated, or pg num is invalid (i.e. -1 or out of bounds)
            # then automatically jump to the page where the current playing track is in,
            page = math.floor(int(player.queue.getPosition) / 10) + 1

        embed = self.queue_embed(ctx=ctx, page=page, player=player)
        queue_display = await ctx.send(embed=embed)

        if math.ceil(player.queue.getLength / 10) > 1:  # display interactive buttons only when there's more than 1 page
            # interactive buttons
            # solution taken from: https://stackoverflow.com/questions/55075157/discord-rich-embed-buttons/65336328#65336328
            await queue_display.add_reaction('⏪')
            await queue_display.add_reaction('⬅️')
            await queue_display.add_reaction('⏺️')
            await queue_display.add_reaction('➡️')
            await queue_display.add_reaction('⏩')
            await queue_display.add_reaction('🔼')

            def check(reaction, user):
                if user.bot:
                    return False
                if reaction.message.guild.id != ctx.message.guild.id:
                    return False
                else:
                    return True

            reaction = None
            while True:
                if str(reaction) == '⏪':
                    page = 1
                    await queue_display.edit(embed=self.queue_embed(ctx=ctx, page=page, player=player))
                elif str(reaction) == '⬅️':
                    if page > 1:
                        page -= 1
                        await queue_display.edit(embed=self.queue_embed(ctx=ctx, page=page, player=player))
                elif str(reaction) == '⏺️':
                    page = math.floor(int(player.queue.getPosition) / 10) + 1
                    await queue_display.edit(embed=self.queue_embed(ctx=ctx, page=page, player=player))
                elif str(reaction) == '➡️':
                    if page < math.ceil(player.queue.getLength / 10):
                        page += 1
                        await queue_display.edit(embed=self.queue_embed(ctx=ctx, page=page, player=player))
                elif str(reaction) == '⏩':
                    page = math.ceil(player.queue.getLength / 10)
                    await queue_display.edit(embed=self.queue_embed(ctx=ctx, page=page, player=player))
                elif str(reaction) == '🔼':  # break to hide the controls
                    break
                try:
                    reaction, user = await self.bot.wait_for('reaction_add', timeout=20,
                                                             check=check)  # close the buttons after 30 secs
                    await queue_display.remove_reaction(reaction, user)
                except:
                    break
            await queue_display.clear_reactions()

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
        msg = await ctx.send(":pause_button: 暫停！")
        # await asyncio.sleep(2)
        # await msg.delete()
        # await ctx.message.delete()

    @_pause.error
    async def _pause_error(self, ctx, exception):
        if isinstance(exception, PlayerAlreadyPaused):
            msg = await ctx.send(":pause_button: 已經暫停了。")
            # await asyncio.sleep(2)
            # await msg.delete()
            # await ctx.message.delete()

    @commands.command(name='resume', aliases=['re'])
    async def _resume(self, ctx):
        player = self.get_player(ctx)
        await player.set_pause(False)
        msg = await ctx.send(":arrow_forward: 繼續！")
        # await asyncio.sleep(2)
        # await msg.delete()
        # await ctx.message.delete()

    @commands.command(name='skip', aliases=['sk'])
    async def _skip(self, ctx, step: int = None):
        player = self.get_player(ctx)
        if player.queue.repeat_flag:
            player.queue.toggleRepeat()
            await ctx.send(':arrow_right: 已自動停用單曲循環播放。')

        if not player.queue.getUpcoming:
            raise NoMoreSongs

        if step:
            if player.queue.position + step > player.queue.getLength:
                raise AttemptedToSkipOutOfBounds
            else:
                player.queue.position += (step - 1)

        await player.stop()
        info = ":track_next: 跳過！"
        msg = await ctx.send(info)
        if player.active_music_controller != 0:
            info_append = await ctx.send("\n:information_source: 按一下播放器下方的 🔄 更新狀態顯示。")
            await asyncio.sleep(5)
            await msg.delete()
            await info_append.delete()
            await ctx.message.delete()
        # await ctx.invoke(self.bot.get_command('nowplay'))

    @_skip.error
    async def _skip_error(self, ctx, exception):
        player = self.get_player(ctx)

        if isinstance(exception, NoMoreSongs):
            await player.stop()
            await ctx.send(":track_next: 跳過！")
            await ctx.send(":warning: 沒歌了喔。")
        if isinstance(exception, EmptyQueue):
            await ctx.send(":information_source: 播放清單為空。")
        if isinstance(exception, AttemptedToSkipOutOfBounds):
            await ctx.send(":warning: 超出播放清單範圍。")

    @commands.command(name='previous', aliases=['pr', 'prev'])
    async def _previous(self, ctx):
        player = self.get_player(ctx)

        if player.queue.waiting_for_next:  # if user decided to go backward while the player is waiting
            await(player.play(
                player.queue.probeForTrack(player.queue.position)))  # pick up the current song and play it again
            player.queue.waiting_for_next = False  # remember to flip this back to false, cause the player is not waiting for new song now...
        else:
            if not player.queue.getPlayHistory:
                raise NoPrevSong
            if player.queue.position <= 0:  # if the player is beyond the top of queue (cap pos at 0)
                player.queue.position = 0
                raise NoPrevSong
            player.queue.position -= 2  # step back 2 steps first
            await player.stop()  # then let it advance 1 step
        info = ":track_previous: 上一首！"
        msg = await ctx.send(info)
        if player.active_music_controller != 0:
            info_append = await ctx.send("\n:information_source: 按一下播放器下方的 🔄 更新狀態顯示。")
            await asyncio.sleep(5)
            await msg.delete()
            await info_append.delete()
            await ctx.message.delete()
        # await ctx.invoke(self.bot.get_command('nowplay'))

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
            msg = await ctx.send(':repeat_one: 單曲循環播放已啟用。')
        else:
            msg = await ctx.send(':arrow_right: 單曲循環播放已停用。')
        # await asyncio.sleep(2)
        # await msg.delete()
        # await ctx.message.delete()

    @commands.command(name='shuffle', aliases=['shuf', 'sh'])
    async def _shuffle(self, ctx):
        player = self.get_player(ctx)
        player.queue.toggleShuffle()
        if player.queue.shuffle_flag:
            msg = await ctx.send(':twisted_rightwards_arrows: 隨機播放已啟用。')
        else:
            msg = await ctx.send(':arrow_right: 隨機播放已停用。')
        if player.active_music_controller != 0:
            await asyncio.sleep(2)
            await msg.delete()
            await ctx.message.delete()

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
        await ctx.send(f'🚮 已從播放清單移除 **{track.title}**。輸入 **.queue** 以查看清單。')
        # await ctx.invoke(self.bot.get_command('queue'))

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
        url = track.info['uri']
        embed = discord.Embed(title=f"**{title}**",
                              url=url, description=f"{url}")
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
            msg = await ctx.send(f':fast_forward: 已跳轉至 **{self.time_parser(seekDisp)}**')
            # await ctx.invoke(self.bot.get_command('nowplay'))
            await asyncio.sleep(5)
            await msg.delete()
            await ctx.message.delete()

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
                await asyncio.sleep(2)
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

    @_replay.error
    async def _replay_error(self, ctx, exception):
        if isinstance(exception, NoVC):
            await ctx.send(':zzz: 未連接至語音頻道。')
        if isinstance(exception, NothingIsPlaying):
            await ctx.send(":zzz: 沒有播放中的曲目。")
        if isinstance(exception, SeekPositionOutOfBound):
            await ctx.send(":x: 指定的時間點超出歌曲範圍。")

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
            msg = await ctx.send('🚮 已清除播放清單。')
            player.queue.position = -1
        else:
            player.queue.clearNotPlaying()
            msg = await ctx.send('🚮 已清除播放清單（保留當前曲目）。')

        if player.queue.shuffle_flag:
            player.queue.shuffle_flag = False
            await ctx.send(':arrow_right: 已自動停用隨機播放。')

    @_clear.error
    async def _clear_error(self, ctx, exception):
        if isinstance(exception, EmptyQueue):
            msg = await ctx.send(":u7a7a: 播放清單為空。")
            await asyncio.sleep(2)
            await msg.delete()
            await ctx.message.delete()

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
            # lp_toggle = await ctx.send(':arrow_right: 已自動停用單曲循環播放。')

        player.queue.jump(index)
        await player.stop()

        if player.queue.waiting_for_next:  # if the player is waiting for the next song, and user decided to jump to track...
            await player.advance()  # then do an advance
            player.queue.waiting_for_next = False

        msg = await ctx.send(":track_next: 跳過！\n")
        if player.active_music_controller != 0:
            await ctx.send(":information_source: 按一下播放器下方的 🔄 更新狀態顯示。")
        # await asyncio.sleep(5)
        # await msg.delete()
        # await ctx.message.delete()
        # await ctx.invoke(self.bot.get_command('nowplay'))

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

    @commands.command(name='volume', aliases=['vol'])
    async def _volume(self, ctx, vol: int = None):
        player = self.get_player(ctx)
        if vol:
            if vol > 100 or vol < 0:
                vol = 100
            vol_before = player.volume
            await player.set_volume(vol)
            msg = await ctx.send(f":loud_sound: 音量調整：**{player.volume}%**") if vol >= vol_before else await ctx.send(f":sound: 音量調整：**{player.volume}%**")
        else:
            msg = await ctx.send(f":sound: 目前音量：**{player.volume}%**")
        await asyncio.sleep(5)
        await msg.delete()
        await ctx.message.delete()

    # auto disconnect when everyone is gone from the VC
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.channel is not None:
            print(f"{before.channel.id} - {len(before.channel.members)} members.")
            if (self.bot.user in before.channel.members) and len(before.channel.members) <= 1:
                player = self.bot.wavelink.get_player(before.channel.guild.id)
                await player.teardown()


def setup(bot):
    bot.add_cog(Music(bot))
    print("Wavelink (Lavalink) Music player loaded.")
