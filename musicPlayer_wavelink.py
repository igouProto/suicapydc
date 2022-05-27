# followed tutorial: https://github.com/Carberra/discord.py-music-tutorial/blob/master/bot/cogs/music.py
# some functions are stripped
# new player based on wavelink + lavalink
import asyncio
import base64
import math
import os
import random
import datetime
import typing as t
import wavelink
import discord
from discord.ext import commands

import pickle  # for dumping the playlist
from cryptography.fernet import Fernet  # let's try some encryption
import config

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


class UserCancelledOperation(commands.CommandError):
    pass


class Queue:
    def __init__(self):
        self._queue = []
        self.position = 0
        self.repeat_flag = False
        self.shuffle_flag = False
        self.repeat_all_flag = False
        self.waiting_for_next = False  # indicates if the player is waiting for more songs while staying in the vc.
        self.jumping = False  # indicates whether the user is explicitly jumping to a certain track, avoids jumping to the wrong one when shuffle is on.

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
        if self.shuffle_flag and self.waiting_for_next is False and not self.jumping:
            self.position = random.randint(0, self.getLength - 1)
        else:
            self.position += 1
            if self.position > len(self._queue) - 1:
                # print("reached end of queue.")
                self.waiting_for_next = True
                self.position -= 1  # move one step back so the next track can be retrieved when the session is resumed
                return None
        self.jumping = False
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

    def probeForTrack(self, index: int):  # probe for track in any position
        if not self._queue:
            raise EmptyQueue
        if index >= self.getLength:
            return None
        if index < 0:
            return None
        return self._queue[index]

    @property
    def queue(self):
        return self._queue


class WavePlayer(wavelink.Player):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bounded_channel = None  # txt channel of last command, track error would be sent there.
        self.queue = Queue()
        self.active_music_controller = 0
        self.controller_registered_time = None
        self.music_controller_is_active = False  # indicates whether there's an active controller panel. For deciding whether to delete text-command messages.
        self.controller_mode = 1  # 1 = nowplay, 2 = queue
        self.repeated_times = 0  # a counter for how many times a song was repeated (cuz i'm bored)
        self.nowplay_is_visible = True  # indicates if the panel has been washed too far away
        self.queue_is_using_buttons = False  # indicates if the user is navigating the playlists by the buttons. Prevents embed from updating while they're navigating.

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
                self.repeated_times = 0
        except:
            pass

    async def repeatTrack(self):
        current = self.queue.getCurrentTrack
        await self.play(current)
        self.repeated_times += 1


class Music(commands.Cog, wavelink.WavelinkMixin):

    def __init__(self, bot):
        self.bot = bot
        if not hasattr(bot, 'wavelink'):
            self.bot.wavelink = wavelink.Client(bot=self.bot)
        self.bot.loop.create_task(self.start_nodes())

        self.timerTask = None
        self.node = None

    async def start_nodes(self):  # connect to a lavalink node
        await self.bot.wait_until_ready()

        # Initiate our nodes. For this example we will use one server.
        # Region should be a discord.py guild.region e.g sydney or us_central (Though this is not technically required)
        self.node = await self.bot.wavelink.initiate_node(host='lava.link',
                                                          port=80,
                                                          rest_uri='http://lava.link:80',
                                                          password='anything',
                                                          region='singapore',
                                                          identifier='MAIN')

    def get_player(self, obj) -> WavePlayer:
        if isinstance(obj, commands.Context):
            return self.bot.wavelink.get_player(obj.guild.id, cls=WavePlayer, context=obj)
        elif isinstance(obj, discord.Guild):
            return self.bot.wavelink.get_player(obj.id, cls=WavePlayer)

    # converts seconds to h:mm:ss
    def time_parser(self, raw_duration: int):
        minutes, seconds = divmod(int(raw_duration), 60)  # minutes = duration / 60, second = duration % 60
        hours, minutes = divmod(int(minutes), 60)  # hours = minutes / 60, minutes = minutes % 60
        duration = []
        if hours > 0:
            duration.append(f"{hours}")
        duration.append(f"{minutes:02d}")
        duration.append(f"{seconds:02d}")
        return ":".join(duration)

    # gets rid of markdowns in song titles
    def title_parser(self, raw_title):
        if '*' in raw_title:
            ind = raw_title.index('*')
            return_title = raw_title[:ind] + '\\' + raw_title[ind:]
            return return_title
        else:
            return raw_title

    # progress bar display for nowplay and queue
    def progress_bar(self, track, player):
        # current player status
        title = self.title_parser(track.title)
        length = track.info['length'] / 1000
        url = track.info['uri']
        raw_pos = math.floor(player.position / 1000)
        duration = self.time_parser(length)
        pos = self.time_parser(raw_pos)
        vol = player.volume

        # player status display before progress bar (smth looks like: ⏸️  ───────⚪────────────  01:43 / 04:49 • 🔊 100%)
        pauseIcon = ''
        lpShufIcon = ''
        if player.is_paused:
            pauseIcon = ' :pause_button: '
        if player.queue.repeat_flag:
            lpShufIcon += ' :repeat_one:'
        if player.queue.shuffle_flag:
            lpShufIcon += ' :twisted_rightwards_arrows:'
        statDisp = f'{pauseIcon + lpShufIcon}'

        # draw the progress bar
        if track.is_stream:
            progress = f"{statDisp} ` 🔴 LIVE ` "
        else:
            progress = int((raw_pos / length) * 100 / 5)
            progress_bar = "───────────────────"
            progress_bar_disp = progress_bar[:progress] + '⚪' + progress_bar[progress:]
            progress = f"{statDisp} ` {progress_bar_disp} ` {pos} / {duration}"

        progress += f' • 🔊 {vol}%'

        return title, url, progress

    #  info embed builders
    def nowplay_embed(self, guild, player) -> discord.Embed:
        track = player.current
        if not track:
            raise NothingIsPlaying

        title, url, progress = self.progress_bar(track, player)

        embed = discord.Embed(title=f"**{title}**", url=url, description=progress)
        embed.set_author(name=f"現正播放～♪",  # [{self.bot.get_channel(player.channel_id).name}]",
                         icon_url=self.bot.get_guild(guild.id).icon_url)

        if track and track.thumb is not None:
            embed.set_thumbnail(url=track.thumb)

        footer = f'{datetime.datetime.now().strftime("%m/%d %H:%M:%S")}'
        if player.queue.repeat_flag:
            footer += f' • 中毒循環中：{player.repeated_times}次'

        embed.set_footer(text=f"上次更新：{footer}")

        return embed

    def new_song_embed(self, ctx: discord.ext.commands.Context, track) -> discord.Embed:
        title = self.title_parser(track.title)
        length = track.info['length'] / 1000
        author = track.info['author']
        url = track.info['uri']
        embed = discord.Embed(title=f"{title}", url=url)
        # embed.add_field(name='上傳者', value=author)
        raw_duration = length
        if track.is_stream:
            duration = '直播'
        else:
            duration = self.time_parser(length)
        # embed.add_field(name='時長', value=duration, inline=True)
        embed.set_author(name=f"{ctx.author.display_name} 已將歌曲加入播放清單～♪", icon_url=ctx.author.avatar_url)
        embed.description = f"{author}  •  {duration}"

        if track.thumb is not None:
            embed.set_thumbnail(url=track.thumb)

        return embed

    def queue_embed(self, guild, page, player) -> discord.Embed:
        index = 0
        list_duration = 0
        full_list = []
        sliced_lists = []
        for track in player.queue.getFullQueue:
            if track.is_stream:
                tr_length = 0
            else:
                tr_length = int(track.info['length'] / 1000)
            track_info = f"`{index:02d}.` {self.title_parser(track.title)} `({self.time_parser(tr_length)})`\n"
            if index == player.queue.getPosition and player.is_playing:
                track_info = f"**[{track_info}]({track.info['uri']})**"
            full_list.append(track_info)
            list_duration += tr_length
            index += 1
        sliced_lists = [full_list[i: i + 10] for i in range(0, len(full_list), 10)]  # 10 item per sub list

        # prepare for the info queue
        track = player.current  # get the current playing track
        if not track:  # if nothing is playing and the player is waiting
            track = player.queue.probeForTrack(player.queue.getPosition)  # get the last played song

        title, url, progress = self.progress_bar(track, player)

        formatted_queue_size = f"{player.queue.getLength} 首"
        formatted_list_length = f"總時長 {self.time_parser(list_duration)}"
        formatted_page_indicator = f'頁數 {page} / {len(sliced_lists)}'

        # display specific page of sliced list
        queue_disp = ''
        for track_info in sliced_lists[page - 1]:
            queue_disp += track_info

        embed = discord.Embed(title=f"**{title}**", url=url, description=progress)

        embed.add_field(name=f"播放清單",
                        value=queue_disp, inline=False)

        if track and track.thumb is not None:
            embed.set_thumbnail(url=track.thumb)

        embed.set_footer(text=f"{formatted_page_indicator} • {formatted_queue_size} • {formatted_list_length}")
        if player.queue.waiting_for_next:
            embed.set_footer(text='播放器閒置中。請使用.play指令繼續點歌，或使用.pr / .jump指令回到上一首或指定曲目。')

        embed.set_author(name=f"現正播放～♪",
                         icon_url=self.bot.get_guild(guild.id).icon_url)

        return embed

    # panel updater (for updating the panel while text commands are used)
    async def nowplay_update(self, ctx: discord.ext.commands.Context):
        player = self.get_player(ctx)
        nowplay_panel = await ctx.fetch_message(player.active_music_controller)
        if nowplay_panel:
            if player.controller_mode == 1:
                await nowplay_panel.edit(embed=self.nowplay_embed(guild=ctx.guild, player=player))
            elif player.controller_mode == 2:
                page = math.floor(int(player.queue.getPosition) / 10) + 1
                await nowplay_panel.edit(embed=self.queue_embed(guild=ctx.guild, page=page, player=player))

    # auto panel updater - updates itself when track starts (and it's not washed too far away)
    @wavelink.WavelinkMixin.listener('on_track_start')
    async def auto_panel_updater(self, node, payload):
        player = payload.player
        bounded_channel = player.bounded_channel
        messages = await player.bounded_channel.history(limit=15, after=player.controller_registered_time).flatten()
        if player.controller_registered_time:
            messages_length = 0
            messages_with_embed_or_attatch = 0
            for item in messages:
                messages_length += len(item.content)
                if item.embeds or item.attachments:
                    messages_with_embed_or_attatch += 1
            if len(messages) < 10 and messages_length < 300 and messages_with_embed_or_attatch < 2:
                try:
                    nowplay_panel = await bounded_channel.fetch_message(player.active_music_controller)
                    new_embed = None
                    if nowplay_panel:
                        if player.controller_mode == 1:
                            new_embed = self.nowplay_embed(guild=nowplay_panel.guild, player=player)
                        elif player.controller_mode == 2:
                            if not player.queue_is_using_buttons:
                                page = math.floor(int(player.queue.getPosition) / 10) + 1
                                new_embed = self.queue_embed(guild=nowplay_panel.guild, page=page, player=player)
                        await nowplay_panel.edit(embed=new_embed)
                        player.nowplay_is_visible = True
                except:
                    pass
            else:
                player.nowplay_is_visible = False

    # interactive buttons (via giving reactions)
    async def nowplay_buttons(self, nowplay, player: WavePlayer, ctx: discord.ext.commands.Context):
        player.music_controller_is_active = True
        # set the player's controller mode to nowplay (1)
        player.controller_mode = 1
        #  interactive buttons
        await nowplay.add_reaction('🔄')
        await nowplay.add_reaction('⏮')
        await nowplay.add_reaction('⏯️')
        await nowplay.add_reaction('⏭️')
        await nowplay.add_reaction('🔂')
        await nowplay.add_reaction('🔀')
        await nowplay.add_reaction('📋')
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
        np_disp_id = nowplay.id
        while np_disp_id == player.active_music_controller and not player.queue.waiting_for_next:
            if str(reaction) == '⏮':
                if player.position >= 5000:
                    await player.seek(0)
                    await asyncio.sleep(0.5)
                    await nowplay.edit(embed=self.nowplay_embed(guild=ctx.guild, player=player))
                elif player.queue.position > 0 and not player.queue.waiting_for_next:
                    if player.queue.repeat_flag:
                        player.queue.repeat_flag = False
                    player.queue.position -= 2
                    await player.stop()
            elif str(reaction) == '⏯️':
                if player.is_paused:
                    await player.set_pause(False)
                else:
                    await player.set_pause(True)
                await nowplay.edit(embed=self.nowplay_embed(guild=ctx.guild, player=player))
            elif str(reaction) == '⏭️':
                if player.queue.getUpcoming or player.queue.shuffle_flag:  # if there's an upcoming song or the shuffle function is on
                    if player.queue.repeat_flag:
                        player.queue.repeat_flag = False
                    await player.stop()
            elif str(reaction) == '🔂':
                player.queue.toggleRepeat()
                await nowplay.edit(embed=self.nowplay_embed(guild=ctx.guild, player=player))
            elif str(reaction) == '🔀':
                player.queue.toggleShuffle()
                await nowplay.edit(embed=self.nowplay_embed(guild=ctx.guild, player=player))
            elif str(reaction) == '🔄':
                await nowplay.edit(embed=self.nowplay_embed(guild=ctx.guild, player=player))
            elif str(reaction) == '🔼':  # break to hide the controls
                # player.active_music_controller = 0
                break
            elif str(reaction) == '📋':  # switch to queue display mode
                current_page = math.floor(int(player.queue.getPosition) / 10) + 1
                await nowplay.clear_reactions()
                await nowplay.edit(embed=self.queue_embed(guild=ctx.guild, page=current_page, player=player))
                await self.queue_buttons(nowplay, player, page=current_page, ctx=ctx)
                break
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=600,
                                                         check=check)  # close the controller after being idle 10 minutes
                await nowplay.remove_reaction(reaction, user)
            except:  # when in doubt, break. whatever.
                break
        # reset controller status
        # player.active_music_controller = 0
        player.music_controller_is_active = False
        player.controller_mode = 1
        await nowplay.clear_reactions()

    async def queue_buttons(self, queue_display, player, page, ctx: discord.ext.commands.Context,
                            mode=1):  # mode: 1=with shortcut to nowplay; 0=navi buttons only
        player.music_controller_is_active = True
        player.queue_is_using_buttons = True
        # set the player's controller mode to queue (2)
        player.controller_mode = 2
        # interactive buttons
        await queue_display.add_reaction('🔄')
        if math.ceil(player.queue.getLength / 10) > 1:  # display interactive buttons only when there's more than 1 page
            await queue_display.add_reaction('⏪')
            await queue_display.add_reaction('⬅️')
            await queue_display.add_reaction('➡️')
            await queue_display.add_reaction('⏩')
        if mode == 1:
            await queue_display.add_reaction('🎵')
        await queue_display.add_reaction('🔼')

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
        queue_disp_id = queue_display.id
        while queue_disp_id == player.active_music_controller and not player.queue.waiting_for_next:
            if str(reaction) == '⏪':
                page = 1
                await queue_display.edit(embed=self.queue_embed(guild=ctx.guild, page=page, player=player))
            elif str(reaction) == '⬅️':
                if page > 1:
                    page -= 1
                    await queue_display.edit(embed=self.queue_embed(guild=ctx.guild, page=page, player=player))
            elif str(reaction) == '🔄':
                page = math.floor(int(player.queue.getPosition) / 10) + 1
                await queue_display.edit(embed=self.queue_embed(guild=ctx.guild, page=page, player=player))
            elif str(reaction) == '➡️':
                if page < math.ceil(player.queue.getLength / 10):
                    page += 1
                    await queue_display.edit(embed=self.queue_embed(guild=ctx.guild, page=page, player=player))
            elif str(reaction) == '⏩':
                page = math.ceil(player.queue.getLength / 10)
                await queue_display.edit(embed=self.queue_embed(guild=ctx.guild, page=page, player=player))
            elif str(reaction) == '🔼':  # break to hide the controls (and switch back to nowplay)
                await queue_display.edit(embed=self.nowplay_embed(guild=ctx.guild, player=player))
                break
            elif str(reaction) == '🎵':  # switch to nowplay display mode
                await queue_display.clear_reactions()
                await queue_display.edit(embed=self.nowplay_embed(guild=ctx.guild, player=player))
                await self.nowplay_buttons(queue_display, player, ctx=ctx)
                break
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=30,
                                                         check=check)  # close the buttons after 30 secs
                await queue_display.remove_reaction(reaction, user)
            except:
                break
        # reset controller status
        # player.active_music_controller = 0
        player.music_controller_is_active = False
        player.queue_is_using_buttons = False
        player.controller_mode = 2
        await queue_display.edit(embed=self.nowplay_embed(guild=ctx.guild, player=player))
        await queue_display.clear_reactions()

    @wavelink.WavelinkMixin.listener()
    async def on_node_ready(self, node):
        print("Lavalink is ready!")

    @wavelink.WavelinkMixin.listener('on_track_stuck')
    @wavelink.WavelinkMixin.listener('on_track_end')
    @wavelink.WavelinkMixin.listener('on_track_exception')
    async def onPlayerStop(self, node, payload):
        if payload.player.queue.repeat_flag:
            await payload.player.repeatTrack()
        else:
            await payload.player.advance()

        # turn off repeat and shuffle is something bad happened (avoids the player being stuck in the limbo of looping the same failed track)
        if isinstance(payload, wavelink.events.TrackStuck) or isinstance(payload, wavelink.events.TrackException):
            footer = ''
            if isinstance(payload, wavelink.events.TrackStuck):
                footer = f"Track stucked at {payload.threshold}"
            elif isinstance(payload, wavelink.events.TrackException):
                footer = f"Error: {payload.error}"
            desc = "曲目發生問題，已跳過。可嘗試使用 .pr 重新播放。"
            if payload.player.queue.repeat_flag or payload.player.queue.shuffle_flag:
                payload.player.queue.repeat_flag = False
                payload.player.queue.shuffle_flag = False
                desc += '\n已自動停用單曲循環及隨機播放，輸入 .lp 或 .shuf 以重新啟用。'
            embed = discord.Embed(title=":x: 糟了個糕", description=desc)
            embed.set_footer(text=footer)
            await payload.player.bounded_channel.send(embed=embed)

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

    @commands.command(name='disconnect', aliases=['dc', 'leave'])
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
                    await warning.edit(content=":arrow_left: 已解除連接。")
                    break
                try:
                    reaction, user = await self.bot.wait_for('reaction_add', timeout=7, check=check)
                except:
                    await warning.edit(content=":information_source: 已取消解除連接。")
                    await warning.clear_reactions()
                    break
            await warning.clear_reactions()
        else:
            await player.teardown()
            if player.queue.getLength > 1:
                await ctx.send(":boom: 已清除播放清單。")
            await ctx.send(":arrow_left: 已解除連接。")

    @commands.command(name='play', aliases=['p'])
    async def _play(self, ctx: discord.ext.commands.Context, *, query: str, ):
        player = self.get_player(ctx)
        if not player.is_connected:
            await player.connect(ctx)
        player.bounded_channel = ctx.channel

        await ctx.send(":mag_right: 正在搜尋`{}`...".format(query))
        await ctx.trigger_typing()

        #  pre-process the query string  TODO: Try regex match, perhaps??
        if 'https://' not in query:
            query = f'ytsearch:{query}'  # treat non-url queries as youtube search
        if '&list=' in query:  # if user attempts to add song with playlist open
            query = query.split('&')[0]  # strips away playlist and other stuff from url (arbitrarily)
            await ctx.send(':information_source: 如要新增播放清單，請在 play 指令後方貼上清單網址。')
        if '>' in query or '<' in query:  # if someone knows adding a pair of <> removes the embed, then this is for them
            query = query.strip('>')
            query = query.strip('<')

        #  get the tracks and add to the player queue
        tracks = await self.bot.wavelink.get_tracks(query)
        if not tracks:
            await ctx.send(':x: 搜尋結果為空。')
            if '/playlist?' in query:
                await ctx.send(':warning: 此清單可能為私人清單，請檢查播放清單檢視權限。')

        # stuff the songs into the player
        await player.addTrack(ctx=ctx, tracks=tracks)

        # get the track info to be displayed
        if '/playlist?' in query:  # if user stuffed a playlist
            track = tracks.tracks[0]
            await ctx.send(f':white_check_mark: 已成功從播放清單新增**{len(tracks.tracks)}**首歌曲。輸入 **.queue** 以查看。')
        else:
            track = tracks[0]
        # display new song embed
        await ctx.send(embed=self.new_song_embed(ctx=ctx, track=track))

    @_play.error
    async def _play_error(self, ctx, exception):
        if isinstance(exception, NoVC):
            await ctx.send(":question: 窩不知道你在哪裡QQ")

    @commands.command(name='nowplay', aliases=['np'])  # now with interactive controller, yay
    async def _nowplay(self, ctx, *args: str):
        player = self.get_player(ctx)
        if not player.is_connected:
            raise NoVC

        embed = self.nowplay_embed(guild=ctx.guild, player=player)
        nowplay = await ctx.send(embed=embed)
        player.controller_registered_time = nowplay.created_at

        player.active_music_controller = nowplay.id  # register the current embed as the controller
        player.controller_mode = 1
        player.nowplay_is_visible = True

        # experimental live update panel
        if self.timerTask:
            self.timerTask.cancel()
        if 'live' in args:
            self.timerTask = self.bot.loop.create_task(self.timer(ctx=ctx))
            await ctx.send(':information_source: 此面板將會每30秒更新一次。')

        if args and 'panel' in args:
            await self.nowplay_buttons(nowplay, player, ctx)  # show the control panel
            if (not player.queue.waiting_for_next) and player.is_connected:
                embed = self.nowplay_embed(guild=ctx.guild, player=player)
                now = datetime.datetime.now().strftime("%m/%d %H:%M:%S")
                embed.set_footer(text=f'按鈕已隱藏。用 .panel 以叫出新的操作面板。上次更新：{now}')
                await nowplay.edit(embed=embed)

    @_nowplay.error
    async def _nowplay_error(self, ctx, exception):
        if isinstance(exception, NoVC):
            await ctx.send(":zzz: 未連接至語音頻道。")
        if isinstance(exception, NothingIsPlaying):
            await ctx.send(":zzz: 沒有播放中的曲目。")

    @commands.command(name='panel', aliases=['pan'])
    async def _panel(self, ctx):
        await ctx.invoke(self.bot.get_command('nowplay'), 'f', 'panel')

    @commands.command(name='queue', aliases=['q'])
    async def _queue(self, ctx, page: int = None, *args):
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

        embed = self.queue_embed(guild=ctx.guild, page=page, player=player)
        queue_display = await ctx.send(embed=embed)
        player.controller_registered_time = queue_display.created_at
        player.active_music_controller = queue_display.id  # register the current embed as the controller
        player.controller_mode = 2
        player.nowplay_is_visible = True

        await self.queue_buttons(queue_display, player, page, ctx, mode=0)

        if (not player.queue.waiting_for_next) and player.is_connected:
            embed = self.queue_embed(guild=ctx.guild, page=math.floor(int(player.queue.getPosition) / 10) + 1,
                                     player=player)
            now = datetime.datetime.now().strftime("%m/%d %H:%M:%S")
            embed.set_footer(text=f'按鈕已隱藏。用 .queue 以叫出新的按鈕。上次更新：{now}')
            await queue_display.edit(embed=embed)

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
        if player.nowplay_is_visible:
            await self.nowplay_update(ctx)
            await asyncio.sleep(5)
            await msg.delete()
            await ctx.message.delete()

    @_pause.error
    async def _pause_error(self, ctx, exception):
        if isinstance(exception, PlayerAlreadyPaused):
            msg = await ctx.send(":pause_button: 已經暫停了。")
            await asyncio.sleep(2)
            await msg.delete()
            await ctx.message.delete()

    @commands.command(name='resume', aliases=['re'])
    async def _resume(self, ctx):
        player = self.get_player(ctx)
        await player.set_pause(False)
        msg = await ctx.send(":arrow_forward: 繼續！")
        if player.nowplay_is_visible:
            await self.nowplay_update(ctx)
            await asyncio.sleep(5)
            await msg.delete()
            await ctx.message.delete()

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
        if player.nowplay_is_visible:
            await asyncio.sleep(5)
            await msg.delete()
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
        if player.nowplay_is_visible:
            await asyncio.sleep(5)
            await msg.delete()
            await ctx.message.delete()

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
        if player.nowplay_is_visible:
            await self.nowplay_update(ctx)
            await asyncio.sleep(5)
            await msg.delete()
            await ctx.message.delete()

    @commands.command(name='shuffle', aliases=['shuf', 'sh'])
    async def _shuffle(self, ctx):
        player = self.get_player(ctx)
        player.queue.toggleShuffle()
        if player.queue.shuffle_flag:
            msg = await ctx.send(':twisted_rightwards_arrows: 隨機播放已啟用。')
        else:
            msg = await ctx.send(':arrow_right: 隨機播放已停用。')
        if player.nowplay_is_visible:
            await self.nowplay_update(ctx)
            await asyncio.sleep(5)
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
        await ctx.send(f'🚮 已從播放清單移除 `{self.title_parser(track.title)}`。輸入 **.queue** 以查看清單。')
        await self.nowplay_update(ctx=ctx)

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
        msg = await ctx.send(":white_check_mark: 已將歌曲資訊傳送到私訊！")
        await asyncio.sleep(5)
        await ctx.message.delete()
        await msg.delete()

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
                seek = 0
                for i in converted_pos:
                    seek += int(i) * (60 ** (len(converted_pos) - converted_pos.index(
                        i) - 1))  # a:b:c -> (a * 60^2 + b * 60^1 + c * 60^0)
            else:  # if number is directly input
                seek = int(pos)

            if seek > player.current.length or seek < 0:
                raise SeekPositionOutOfBound

            await player.seek(position=seek * 1000)
            msg = await ctx.send(f':fast_forward: 已跳轉至 **{self.time_parser(seek)}**')
            # await ctx.invoke(self.bot.get_command('nowplay'))
            if player.nowplay_is_visible:
                await self.nowplay_update(ctx)
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

    @_replay.error
    async def _replay_error(self, ctx, exception):
        if isinstance(exception, NoVC):
            await ctx.send(':zzz: 未連接至語音頻道。')
        if isinstance(exception, NothingIsPlaying):
            await ctx.send(":zzz: 沒有播放中的曲目。")

    @commands.command(name='clear', aliases=[
        'cl'])  # clears everything in the queue (but keeps the one's playing if player's not waiting)
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

        await self.nowplay_update(ctx=ctx)

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

        player.queue.jumping = True
        player.queue.jump(index)
        await player.stop()

        if player.queue.waiting_for_next:  # if the player is waiting for the next song, and user decided to jump to track...
            await player.advance()  # then do an advance
            player.queue.waiting_for_next = False

        msg = await ctx.send(":track_next: 跳過！\n")
        if player.nowplay_is_visible:
            await self.nowplay_update(ctx)
            await asyncio.sleep(5)
            await msg.delete()
            await ctx.message.delete()

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
            msg = await ctx.send(f":loud_sound: 音量調整：**{player.volume}%**") if vol >= vol_before else await ctx.send(
                f":sound: 音量調整：**{player.volume}%**")
        else:
            msg = await ctx.send(f":sound: 目前音量：**{player.volume}%**")
        if player.nowplay_is_visible:
            await self.nowplay_update(ctx=ctx)
            await asyncio.sleep(5)
            await msg.delete()
            await ctx.message.delete()

    # export the current queue as text file and dump
    @commands.command(name='export', aliases=['exp'])
    async def _export(self, ctx, *name):
        player = self.get_player(ctx)

        await ctx.send('🖨️ 正在匯出播放清單...')
        await ctx.trigger_typing()

        if not name:
            path_txt = f'{ctx.guild.id}_{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.txt'
            path_sup = f'{ctx.guild.id}_{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.sup'  # for the list dump. sup: "SUICA Playlist"
        else:
            path_txt = f'{name}_{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.txt'
            path_sup = f'{name}_{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.sup'  # for the list dump

        queue = player.queue.getFullQueue
        if len(queue) == 0:
            raise EmptyQueue

        with open(path_txt, 'w') as file:
            for track in player.queue.getFullQueue:
                file.write(f"{track.info['title']}: {track.info['uri']}\n")
        await ctx.send(file=discord.File(path_txt))
        os.remove(path_txt)

        # generate and encrypt the playlist dump
        with open(path_sup, 'wb') as file_sup:
            pickle.dump(player.queue.getFullQueue, file_sup)
        with open(path_sup, 'rb') as file_sup_raw:
            original = file_sup_raw.read()
        token = config.getToken().encode("UTF-8")  # use the bot's token as the key
        token_as_key = base64.urlsafe_b64encode(token)[:43] + b'='  # the typical length generated by fernet is 44
        fernet = Fernet(token_as_key)
        encrypted = fernet.encrypt(original)

        with open(path_sup, 'wb') as file_sup_encrypted:
            file_sup_encrypted.write(encrypted)
        await ctx.send(file=discord.File(path_sup))
        os.remove(path_sup)
        await ctx.send(':white_check_mark: 匯出成功。')

    @_export.error
    async def _export_error(self, ctx, exception):
        if isinstance(exception, EmptyQueue):
            await ctx.send(':u7a7a: 播放清單為空。')

    # import the dump as playlist cuz it's faster
    @commands.command(name='import', aliases=['imp'])
    async def _import(self, ctx):
        await ctx.send('📥 請上傳匯出的清單（使用.exp指令產生的**.sup檔**），或輸入c以取消。')

        def check(message):
            if message.author.id == ctx.author.id:
                if message.content == 'c':
                    raise UserCancelledOperation
                else:
                    attachments = message.attachments
                    if len(attachments) == 0:
                        return False
                    else:
                        attachment = attachments[0]
                        return attachment.filename.endswith('.sup')
            else:
                return False

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=15)
            imported_list = msg.attachments[0]
            await imported_list.save(imported_list.filename)
        except asyncio.TimeoutError:
            await ctx.send(':x: 操作逾時。')
        except UserCancelledOperation:
            await ctx.send(':x: 操作已取消。')
        else:
            # same procedure as .play
            player = self.get_player(ctx)
            if not player.is_connected:
                await player.connect(ctx)

            await ctx.send('📝 正在匯入...')
            await ctx.trigger_typing()

            with open(imported_list.filename, 'rb') as file:
                encrypted = file.read()
            token = config.getToken().encode("UTF-8")  # use the bot's token as the key
            token_as_key = base64.urlsafe_b64encode(token)[:43] + b'='  # the typical length generated by fernet is 44
            fernet = Fernet(token_as_key)
            try:
                decrypted = fernet.decrypt(encrypted)
                with open(imported_list.filename, 'wb') as file:
                    file.write(decrypted)
                with open(imported_list.filename, 'rb') as file:
                    loaded_list = pickle.load(file)
                    player.queue.queue.extend(loaded_list)
                await ctx.send(f':white_check_mark: 匯入成功。輸入**.queue**以查看播放清單。')
                os.remove(imported_list.filename)
            except:
                os.remove(imported_list.filename)

            if not player.is_playing:
                await player.startPlaying()

    @_import.error
    async def _import_error(self, ctx, exception):
        if isinstance(exception, NoVC):
            await ctx.send(":question: 窩不知道你在哪裡QQ")
        else:
            await ctx.send(":x: 匯入失敗。")

    # auto disconnect when everyone is gone from the VC
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.channel:
            if (self.bot.user in before.channel.members) and len(before.channel.members) <= 1:
                player = self.bot.wavelink.get_player(before.channel.guild.id)
                await player.teardown()
                try:
                    await player.bounded_channel.send('⬅️ 人都跑光光了，那我也要睡啦（已自動解除連接）。')
                except:
                    return

    # try to do a quick pause and resume if the VC's region changed
    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        if isinstance(before, discord.VoiceChannel):
            if self.bot.user in before.members:
                player = self.bot.wavelink.get_player(before.guild.id)
                await player.set_pause(True)
                await asyncio.sleep(1)
                await player.set_pause(False)

    # experimental live panel updater (updates every 30 seconds)
    async def timer(self, ctx):
        while True:
            await self.nowplay_update(ctx=ctx)
            await asyncio.sleep(30)


def setup(bot):
    bot.add_cog(Music(bot))
    print("Wavelink (Lavalink) Music player loaded.")
