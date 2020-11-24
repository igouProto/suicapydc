# ytdl module
import youtube_dl  # IT'S BACK

# discord py modules
import discord
from discord.ext import commands
import asyncio
import random

# os module
import os

'''
This cog contains EVERYTHING about the music playing function. Still looks like spaghetti though.
More documentation will come soon as there is a lot to say about it... (Probably?)
'''
# TODO: jump to track function (_jump())

players = {}
queues = {}
loopQueues = {}
timers = {}

pauseFlags = {}
loopFlags = {}
isLooping = {}

loopCount = {}

ytdl_format_options = {
    'format': 'bestaudio/best',
    'extract-audio': True,
    'audio-format': 'opus',
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': True,
    'quiet': False,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}
ffmpeg_options = "-vn -loglevel panic -f s16le -filter_complex 'loudnorm'"  # some filters can help improve the radio-like quality, perhaps...
# full doc of filters: https://ffmpeg.org/ffmpeg-filters.html
beforeArgs = "-nostdin -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):  # make it work like create_ytdl_player in the old version. Taken from Rapptz's example.
    def __init__(self, source, *, data, volume=1.0):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.duration = data.get('duration')
        self.thumbnail = data.get('thumbnail')
        self.page_url = data.get('webpage_url')
        self.uploader = data.get('uploader')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True):  # stream: download then play or stream directly.
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, before_options=beforeArgs, options=ffmpeg_options), data=data)

class musicPlayer(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='summon', aliases=['join', 'j', 'J'])
    async def _summon(self, ctx):
        if ctx.author.voice is None:
            await ctx.send(":warning: 你要先加入語音頻道，才能叫我過去喔。")
            return
        else:
            try:
                voiceChannel = ctx.author.voice.channel
                await voiceChannel.connect()
                await ctx.send(":white_check_mark: 已加入語音頻道**{}**。".format(voiceChannel.name))
            except discord.errors.ClientException as err:
                await ctx.send(":question: 我已經在語音頻道裡了喔？")

    @commands.command(name='disconnect', aliases=['dc', 'd', 'D'])
    async def _disconnect(self, ctx):
        voiceClient = ctx.voice_client
        if voiceClient is None:
            await ctx.send(":x: 未加入語音頻道，無法解除連接。很怪對吧。")
            return
        await voiceClient.disconnect()
        await ctx.send(":arrow_left: 已解除連接。")
        try:  # this needs to be fixed i guess, although it appears to be working fine
            del players[ctx.guild.id]
            del queues[ctx.guild.id]
            del timers[ctx.guild.id]
            del pauseFlags[ctx.guild.id]
            del loopFlags[ctx.guild.id]
            print("cleanup finished")
        except KeyError as err:
            print("nothing to clear, leaving voice channel only")

    @commands.command(name='play', aliases=['p', 'P'])
    async def _play(self, ctx, *, url):

        # the queue system...
        async def checkqueue(ctx):
            print("called checkqueue")
            players[ctx.guild.id].cleanup()
            if loopFlags[ctx.guild.id] == True:  # loop mode
                print('loop triggered')
                isLooping[ctx.guild.id] = True  # triggers the next download
                timers[ctx.guild.id] = 0  # reset the timer every time a new song starts
                player = loopQueues[ctx.guild.id].pop(0)  # take the player from the loop queue
                players[ctx.guild.id] = player
                ctx.voice_client.play(player, after=check_trigger)
            elif queues[ctx.guild.id] != []:  # if we still have something in the queue...
                print("Normal proceeding")
                player = queues[ctx.guild.id].pop(0)
                players[ctx.guild.id] = player
                timers[ctx.guild.id] = 0  # reset the timer
                ctx.voice_client.play(player, after=check_trigger)
            elif queues[ctx.guild.id] == []:
                del players[ctx.guild.id]
                del timers[ctx.guild.id]
                del loopQueues[ctx.guild.id]
                print('reached end of queue, cleaning up players and timers')

        # ...and the function that triggers the queue system
        def check_trigger(error):
            coro = checkqueue(ctx)
            fut = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
            try:
                fut.result()
            except:
                print("queue or loopQueue is empty")
                pass

        # check if the author is connected
        if ctx.author.voice is None:
            await ctx.send(":warning: 你要先加入語音頻道才能點歌喔。")
            return
        # automatic join voice channel if not connected
        if ctx.voice_client is None:
            voiceChannel = ctx.author.voice.channel
            await ctx.trigger_typing()
            await voiceChannel.connect()
            await ctx.send(":white_check_mark: 已加入語音頻道**{}**。".format(voiceChannel.name))

        await ctx.send(":mag_right: 正在搜尋`{}`...".format(url))
        await ctx.trigger_typing()

        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():  # if something is still playing or paused then stuff the song into the queue
            # calculate total time of playlist first
            totalTime = 0
            for player in queues[ctx.guild.id]:
                totalTime += player.duration
            totalTime = totalTime + players[ctx.guild.id].duration - timers[ctx.guild.id]  # and minus how much were played
            # add the player to the list
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            if ctx.guild.id in queues:
                queues[ctx.guild.id].append(player)
            else:
                queues[ctx.guild.id] = [player]
            # The info embed
            embed = discord.Embed(title="**{}**".format(player.title), url=player.page_url, color=0xff0000)
            embed.set_thumbnail(url=player.thumbnail)
            embed.set_author(name="{} 剛剛把歌曲加入了播放清單～♪".format(ctx.author.display_name), icon_url=ctx.author.avatar_url)
            embed.add_field(name='上傳頻道', value=player.uploader)
            duration = "{:02d}:{:02d}".format(int(player.duration / 60), int(player.duration % 60))
            eta = "{:02d}:{:02d}".format(int(totalTime / 60), int(totalTime % 60))
            if player.duration <= 0: # if the added song is also a livestream
                duration = '直播' # mark the length as "livestream"
            if players[ctx.guild.id].duration <= 0:  # if the current song is also a livestream
                eta = '-' # mark the eta as "n/a"
            embed.add_field(name='時長',
                            value= duration,
                            inline=True)
            embed.add_field(name='播放順位', value=len(queues[ctx.guild.id]), inline=True)
            embed.add_field(name='預估等待時間', value=eta,inline=True)
            await ctx.send(embed=embed)
        else:  # fresh play
            print("Fresh play")
            players[ctx.guild.id] = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            player = players[ctx.guild.id]
            ctx.voice_client.play(player, after=check_trigger)  # start the player
            queues[ctx.guild.id] = []  # define a blank queue for this server
            timers[ctx.guild.id] = 0  # reset the timer
            self.bot.loop.create_task(timer(ctx))  # start the timer task
            loopFlags[ctx.guild.id] = False  # define a loop status for this server
            pauseFlags[ctx.guild.id] = False  # and a pause flag for this server
            isLooping[ctx.guild.id] = False  # and a default looping flag for this server
            # the info embed
            embed = discord.Embed(title="**{}**".format(player.title), url=player.page_url)
            embed.add_field(name='上傳頻道', value=player.uploader)
            if player.duration <= 0:
                duration = '直播' # mark the length as "livestream"
            else:
                duration = "{:02d}:{:02d}".format(int(player.duration / 60), int(player.duration % 60))
            embed.add_field(name='時長',
                            value=duration,
                            inline=True)
            embed.set_thumbnail(url=player.thumbnail)
            embed.set_author(name="用閃亮的歌聲開始現場演唱♪", icon_url=self.bot.user.avatar_url)
            await ctx.send(embed=embed)

            # and a tiny little easter egg ;)
            if player.page_url in['https://www.youtube.com/watch?v=rB7XFQgJHBI', 'https://www.youtube.com/watch?v=SmKKG6tCP3M']: # if タイニーリトル・アジアンタム from Shibayan Records is played...
                await ctx.send("https://tenor.com/8ZES.gif") # ...send this minecraft dancing parrot GIF :D
                await ctx.send('嘿，你發現彩蛋了！') # hey you found the easter egg!

    @_play.error
    async def play_error(self, ctx, error):
        embed = discord.Embed(title=':x: 糟了個糕。', colour=0xff0000)
        embed.description = "**{}**".format(error)
        # embed.add_field(name = "好像很厲害但是也有可能不知所云的traceback：", value = '```py{}```'.format(traceback.format_exc()))
        embed.set_footer(text="操作已取消。")
        await ctx.send(embed=embed)

    @commands.command(name='queue', aliases=['qu', 'q', 'Q'])
    async def _queue(self, ctx, page: int = 1):
        await ctx.trigger_typing()
        try:
            fullList = []
            slicedList = []
            listDuration = 0
            index = 1
            upnext = ''
            if page <= 0:
                page = 1
            for player in queues[ctx.guild.id]:  # list out all the upcoming songs in a single msg and calculate the duration
                fullList.append(
                    "`{:02d}.` {} **({:02d}:{:02d})**".format(index,
                                                              player.title,
                                                              int(player.duration / 60),
                                                              int(player.duration % 60)))
                listDuration += player.duration
                index += 1
            if len(queues[ctx.guild.id]) == 0:
                upnext = '-'  # stuff this line if the queue is empty
            else:
                slicedList = [fullList[i: i + 10] for i in range(0, len(fullList), 10)]
                try:
                    for item in slicedList[page - 1]:
                        upnext += item
                        upnext += '\n'
                except IndexError as err:
                    for item in slicedList[len(slicedList) - 1]:
                        upnext += item
                        upnext += '\n'
                    page = len(slicedList)
            # display the queue
            player = players[ctx.guild.id]
            timer = timers[ctx.guild.id]
            embed = discord.Embed(title="現正播放",
                                  description="**{} ({:02d}:{:02d} / {:02d}:{:02d})**".format(player.title,
                                                                                              int(timer / 60),
                                                                                              int(timer % 60),
                                                                                              int(player.duration / 60),
                                                                                              int(player.duration % 60)),
                                  color=0xff0000)
            embed.set_author(name="{} 的播放清單～♪".format(self.bot.get_guild(ctx.guild.id).name),
                             icon_url=self.bot.get_guild(ctx.guild.id).icon_url)
            embed.add_field(name="接下來還有 **{}** 首歌♪ （總時長：**{:02d}:{:02d}**）".format(len(queues[ctx.guild.id]),
                                                                                   int(listDuration / 60),
                                                                                   int(listDuration % 60)),
                            value=upnext, inline=False)
            if page != 0:
                embed.set_footer(text="[{}/{}]".format(page, len(slicedList)))
            await ctx.send(embed=embed)
        except KeyError as err:
            await ctx.send(":zzz: 現在這裡很安靜喔。要不要點一首歌？")

    @commands.command(name='pause', aliases=['pa', 'PA'])
    async def _pause(self, ctx):
        if ctx.voice_client is None:
            await ctx.send(":x: 未加入任何語音頻道。")
            return
        if ctx.voice_client.is_paused():
            await ctx.send(":pause_button: 已經暫停了。")
            return
        else:
            ctx.voice_client.pause()
            pauseFlags[ctx.guild.id] = True
            await ctx.send(":pause_button: 暫停！")

    @commands.command(name='resume', aliases=['re', 'RE'])
    async def _resume(self, ctx):
        if ctx.voice_client is None:
            await ctx.send(":x: 未加入任何語音頻道。")
            return
        if ctx.voice_client.is_playing():
            await ctx.send(":arrow_forward: 播放中。")
            return
        else:
            ctx.voice_client.resume()
            pauseFlags[ctx.guild.id] = False
            self.bot.loop.create_task(timer(ctx))
            await ctx.send(":arrow_forward: 繼續！")

    @commands.command(name='skip', aliases=['sk', 'SK'])
    async def _skip(self, ctx):
        if ctx.voice_client is None:
            await ctx.send(":zzz: 現在這裡很安靜喔。要不要點一首歌？")
            return
        else:
            if loopFlags[ctx.guild.id]: # if loop is enabled, disable it
                loopFlags[ctx.guild.id] = False
                loopQueues[ctx.guild.id] = []
                print("loop deactivated due to skip")
                await ctx.send(":arrow_right: 已自動停用單曲循環播放。")
            await ctx.send(":track_next: 跳過！")
            ctx.voice_client.stop()
            await asyncio.sleep(0.2)
            try:
                player = players[ctx.guild.id]
                duration = "{:02d}:{:02d}".format(int(player.duration / 60),int(player.duration % 60))
                if player.duration <= 0:
                    duration = '直播'
                embed = discord.Embed(title="**{}**".format(player.title), url=player.page_url,
                                      description=duration, color=0xff0000)
                embed.set_thumbnail(url=player.thumbnail)
                embed.set_author(name="下一首♪", icon_url=self.bot.user.avatar_url)
                await ctx.send(embed=embed)
                loopCount[ctx.guild.id] = 0  # reset the loop counter
            except KeyError as err:
                await ctx.send(":warning: 沒歌了喔。")

    @commands.command(name="shuffle", aliases=['shuf', 'sh', 'SH'])
    async def _shuffle(self, ctx):
        try:
            if len(queues[ctx.guild.id]) <= 1:
                await ctx.send(':twisted_rightwards_arrows: 播放清單已隨機排列？')
            else:
                random.shuffle(queues[ctx.guild.id])
                await ctx.send(':twisted_rightwards_arrows: 播放清單已隨機排列。')
        except KeyError as err:
            await ctx.send(':x: 播放清單為空。')

    @commands.command(name="top", aliases=['tp', 'TP'])
    async def _top(self, ctx, index: int = None):
        try:
            queue = queues[ctx.guild.id]
            if index == None:
                await ctx.send(':warning: 請輸入要移動的曲目編號，輸入 **.queue** 以查看播放清單。')
                return
            elif index > len(queue):
                await ctx.send(':warning: 輸入的編號超出清單範圍。')
                return
            elif index <= 0:
                await ctx.send(':white_check_mark: 你高興就好。')
                return
            else:
                queue.insert(0, queue.pop(index - 1))
                await ctx.send(':white_check_mark: 已將 **{}** 移至下一播放順位。'.format(queue[0].title))
        except KeyError as err:
            await ctx.send(':x: 播放清單為空。')

    @commands.command(name="jump", aliases=['jmp'])
    async def _jump(self, ctx, index: int = None):
        pass # finish it later

    @commands.command(name="clear", aliases=['cl', 'c', 'C'])
    async def _clear(self, ctx):
        try:
            if queues[ctx.guild.id] == []:
                await ctx.send(':white_check_mark: 已經很乾淨了。')
                return
            else:
                queues[ctx.guild.id] = []
                await ctx.send(':boom: 已清空播放清單。')
        except KeyError as keyerror:
            await ctx.send(':white_check_mark: 已經很乾淨了。')

    @commands.command(name="remove", aliases=['rm'])
    async def _remove(self, ctx, index: int = None):
        try:
            if index == None:
                await ctx.send(':warning: 請輸入要移除的曲目編號。')
                return
            else:
                if queues[ctx.guild.id] == []:
                    await ctx.send(':white_check_mark: 已經很乾淨了。')
                    return
                elif index > len(queues[ctx.guild.id]):
                    await ctx.send(':warning: 曲目編號超出清單範圍。')
                    return
                else:
                    deletedTitle = queues[ctx.guild.id][index - 1].title
                    del queues[ctx.guild.id][index - 1]
                    await ctx.send(':white_check_mark: 已從播放清單移除 `{}`。'.format(deletedTitle))
        except KeyError as err:
            ctx.send(':white_check_mark: 已經很乾淨了。是說根本還沒放歌吧？')

    @commands.command(name="loop", aliases=['lp', 'l', 'L'])
    async def _loop(self, ctx):
        # the loop system
        async def singleLoop(ctx):
            try:
                print("loop activated")
                loopQueues[ctx.guild.id] = []  # clear or define a fresh loop queue for the server
                loopCount[ctx.guild.id] = 1
                current = players[ctx.guild.id]
                player = await YTDLSource.from_url(current.page_url, loop=self.bot.loop, stream=True)
                loopQueues[ctx.guild.id].append(player)
                while loopFlags[ctx.guild.id] == True:
                    while isLooping[ctx.guild.id] == True:
                        print('downloading song again')
                        current = players[ctx.guild.id]
                        loopCount[ctx.guild.id] += 1
                        player = await YTDLSource.from_url(current.page_url, loop=self.bot.loop, stream=True)
                        loopQueues[ctx.guild.id].append(player)
                        isLooping[ctx.guild.id] = False
                    await asyncio.sleep(1)
            except KeyError as err:
                return

        # below is the command's content
        try:
            if loopFlags[ctx.guild.id] == False:  # activate loop
                loopFlags[ctx.guild.id] = True
                await self.bot.loop.create_task(singleLoop(ctx))  # trigger the loop function
                await ctx.send(':repeat_one: 單曲循環播放已啟用。')
            elif loopFlags[ctx.guild.id] == True:  # deactivate loop
                loopFlags[ctx.guild.id] = False
                isLooping[ctx.guild.id] = False
                loopQueues[ctx.guild.id] = []  # clear the loopQueue
                await ctx.send(':arrow_right: 單曲循環播放已停用。')
        except KeyError as e:
            await ctx.send(':warning: 現在沒東西可以循環喔。')

    @commands.command(name='nowplay', aliases=['np', 'song'])
    async def _nowplay(self, ctx):
        try:
            player = players[ctx.guild.id]
            timer = timers[ctx.guild.id]
            if player.duration <= 0: # handles livestreams
                progress = "直播 • 已連接 {:02d}:{:02d}".format(int(timer / 60), int(timer % 60))
            else:
                progress = "{:02d}:{:02d} / {:02d}:{:02d}".format(int(timer / 60), int(timer % 60),
                                                              int(player.duration / 60), int(player.duration % 60))
            embed = discord.Embed(title="**{}**".format(player.title), url=player.page_url, description=progress,
                                  color=0xff0000)
            embed.set_thumbnail(url=player.thumbnail)
            if pauseFlags[ctx.guild.id]:
                embed.set_author(name="已暫停", icon_url=self.bot.user.avatar_url)
            else:
                embed.set_author(name="現正播放♪", icon_url=self.bot.user.avatar_url)
            if loopFlags[ctx.guild.id]:
                embed.set_footer(text="已啟用循環播放。[{}]".format(loopCount[ctx.guild.id]))
            await ctx.send(embed=embed)
        except KeyError as err:
            await ctx.send(":zzz: 現在這裡很安靜喔。要不要點一首歌？")

    # discord limits file size :(
    @commands.command(name='download', aliases=['dl'])
    async def _download(self, ctx):
        player = players[ctx.guild.id]
        if player.duration <= 0:
            await ctx.send(':x: 無法下載直播中的影片。')
            return
        elif player.duration >= 340: # if the duration is over 340 sec then it may exceed the file size limit if the bit rate is 192kbps (8MB = 65536Kb)
            await ctx.send(':x: 檔案大小超出限制(8MB)。') # tell the user the file size is too large anyway lol
            return
        download_options = {
            'outtmpl': '%(title)s.%(ext)s',
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        await ctx.send(":arrow_down: 正在下載**{}**....".format(player.title))
        await ctx.trigger_typing()
        with youtube_dl.YoutubeDL(download_options) as ydl:
            ydl.download([player.page_url])
        await ctx.send(":white_check_mark: 下載完成，正在傳送檔案...")
        await ctx.trigger_typing()
        filename = "{}.mp3".format((player.title).replace("/", ("_")))
        audio_file = discord.File(filename)
        await ctx.send(file=audio_file)
        os.remove(filename)

    @commands.command(name='save', aliases=['sa', 's'])
    async def _save(self, ctx): # saves the current song to your DM :) no need to fondle with databases yay.
        try:
            player = players[ctx.guild.id]
            embed = discord.Embed(title="**{}**".format(player.title), url=player.page_url, color=0xff0000)
            embed.set_author(name="早安啊，這是你剛剛存下來的曲子♪", icon_url=self.bot.user.avatar_url)
            embed.set_thumbnail(url=player.thumbnail)
            embed.add_field(name='上傳頻道', value=player.uploader)
            embed.add_field(name='時長',
                            value="{:02d}:{:02d}".format(int(player.duration / 60), int(player.duration % 60)),
                            inline=True)
            embed.add_field(name='網址', value=player.page_url, inline=False)
            author = ctx.message.author
            await author.send(embed=embed)
            await ctx.send(":white_check_mark: 已將歌曲資訊傳送到私訊！")
        except KeyError as error:
            await ctx.send(":zzz: 現在這裡很安靜喔。要不要點一首歌？")

# homemade music position counter, yay
async def timer(ctx):
    try:
        while ctx.voice_client.is_playing():
            timers[ctx.guild.id] += 1
            await asyncio.sleep(1)
    except AttributeError as err:
        return

def setup(bot):
    bot.add_cog(musicPlayer(bot))
    print("Music player loaded.")
