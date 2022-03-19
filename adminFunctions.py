import subprocess

import discord
from discord.ext import commands
import asyncio
import json
import os
import sys
# import psutil

import config

# TODO (igouP):Add a function that allows others to add another announcement channel.
# This cog is for all the administration related functions, including some actions that requires higher level of permissions, like restarting the bot
# ping and manual are also moved here.
class adminFunctions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ping")  # ping function, used for testing the bot's respond time.
    async def _ping(self, ctx):
        t = await ctx.send('正在測量........')
        # the values
        botLatency = round(self.bot.latency * 1000)
        cmdLatency = round((t.created_at - ctx.message.created_at).total_seconds() * 1000)
        '''
        voiceLatency = "--"
        if ctx.voice_client is not None:
            voiceLatency = round(ctx.voice_client.latency * 1000)
        '''
        # the embed
        embed = discord.Embed(title=":clipboard: 西瓜的各種Ping", description=f'💓 Dokidoki Discord API Heartbeat ... **{botLatency}**ms\n⏱️ 總反應時間 ... **{cmdLatency}**ms')
        await ctx.send(embed=embed)

    @commands.is_owner()
    @commands.command(name="restart", aliases=['res'])  # restart the bot
    async def _restart(self, ctx):
        await self.bot.change_presence(activity=discord.Game(name='重新啟動中'))
        await ctx.send('正在重新啟動...')
        os.execl(sys.executable, sys.executable, *sys.argv)

    @commands.is_owner()
    @commands.command(name="upannounce", aliases=['upd'])  # This is for me to sent the update notes to the announcement channels
    async def _upannounce(self, ctx):
        await ctx.send("輸入公告內容或輸入cancel取消。")
        channel = ctx.message.channel

        def check(author):
            def messageCheck(message):
                if author != message.author:
                    return False
                else:
                    return True
            return messageCheck

        try:
            message = await self.bot.wait_for('message', check=check(ctx.message.author), timeout=120)  # wait for the announcement content, will time out after 120 secs.
        except asyncio.TimeoutError:
            await channel.send('操作逾時。')
        else:
            announcement = message.content
            try:
                if announcement == 'cancel':  # cancel the operation if 'cancel' is entered in the announcement
                    await ctx.send('操作已取消。')
                    return
                else:
                    with open('announce_channels.json') as file:
                        channels = json.load(file)
                        channel_list = channels["channels"]  # read all the channel id's written in the list
                        for each in channel_list:
                            await self.bot.get_channel(each).send(announcement)  # and send the announcement to all the channels
                    file.close()
                    await ctx.send('已發出更新公告。')
            except IOError as e:
                ctx.send("無法讀取公告頻道清單。")

    @commands.is_owner()
    @commands.command(name="purge")  # batch-deletes messages
    async def _purge(self, ctx, amount: int):
        await ctx.message.channel.purge(limit=amount)
        cmd = ctx.message
        msg = await ctx.send('已清除包含指令在內的**{}**則訊息'.format(amount))
        await asyncio.sleep(1)
        await msg.delete()

    @commands.is_owner()
    @commands.command(name="port")  # changes 'portal' destination, the 'portal' is defined in messageHandler.py
    async def _port(self, ctx, dest: int):
        message_handler = self.bot.get_cog('messageHandler')
        message_handler.set_destination(dest)
        destination = message_handler.get_destination()
        await ctx.send('傳聲筒目的地已設為**{}** - {}'.format(self.bot.get_channel(destination).name, self.bot.get_channel(destination).guild.name))

    # TODO: Arrange a extension list and reload them through ONE statement!
    @commands.is_owner()
    @commands.command(name='reload', aliases=['rl']) # reloads all the extensions
    async def _reload(self, ctx):
        await ctx.send('重新載入所有plugin...')
        self.bot.reload_extension('manager')
        self.bot.reload_extension('adminFunctions')
        self.bot.reload_extension('messageHandler')
        self.bot.reload_extension('luckyDraws')
        self.bot.reload_extension('kancolle')
        self.bot.reload_extension('stonks')
        self.bot.reload_extension('doodads')
        self.bot.reload_extension('musicPlayer_wavelink')
        await ctx.send('完成。')

    @commands.command(name="manual", aliases=['man', 'help'])  # print the manual out
    async def _manual(self, ctx):
        manual = open('help.txt', 'r')
        msg = manual.read()
        await ctx.send(msg)
        manual.close()

    @commands.command(name="about")
    async def _about(self, ctx):
        await ctx.trigger_typing()
        # retrive the discord app information
        self.bot.appinfo = await self.bot.application_info()
        self.botid = self.bot.appinfo.id
        name = self.bot.appinfo.name
        owner = self.bot.appinfo.owner.mention
        borntime = "2018-08-01 05:47:51.880000"
        embed = discord.Embed(title='**S**ugoi **U**ltra **I**ntelligent **C**hat **A**ssistant, SUICA', colour=0xff0000)
        embed.set_author(name="關於西瓜(SUICA)", icon_url=self.bot.user.avatar_url)
        embed.description = 'ID:{}\n' \
                            '應用程式名稱：{}' \
                            '\n應用程式擁有者：{}' \
                            '\n建置時間：{}' \
                            '\n作者：igouProto [(GitHub!)](https://github.com/igouProto/suicapydc)'.format(self.botid, name, owner, borntime)
        embed.set_footer(text="{} • 使用 discord.py 及 Wavelink (播放器)".format(config.getVersion()))
        await ctx.send(embed=embed)

    @commands.is_owner()
    @commands.command(name='update') # remote git pull
    async def _update(self, ctx, *args: str):
        await ctx.trigger_typing()
        result = subprocess.run(['git', 'pull'], stdout=subprocess.PIPE).stdout.decode('utf-8')
        display = (result[:1990] + '...') if len(result) >= 1990 else result
        await ctx.send(f"```{display}```")
        if args and '-soft' in args:  # "soft-restart"
            await ctx.invoke(self.bot.get_command('reload'))
        else:
            await ctx.invoke(self.bot.get_command('restart'))

    @commands.is_owner()
    @commands.command(name='terminal', aliases=['term'])
    async def _terminal(self, ctx, *args: str):
        cmd = []
        for item in args:
            cmd.append(item)
        result = subprocess.run(cmd, stdout=subprocess.PIPE)
        output = result.stdout.decode('utf-8')
        if output:
            display = (output[:1990] + '...') if len(output) >= 1990 else output
            await ctx.send(f"```{display}```")
        else:
            if result.returncode == 0:
                await ctx.message.add_reaction("✅")

    @commands.is_owner()
    @commands.command(name='msghandleroff', aliases=['msgoff'])
    async def _msghandleroff(self, ctx):
        self.bot.unload_extension('messageHandler')
        await ctx.send('已關閉關鍵字回覆及傳聲筒。')

    @commands.is_owner()
    @commands.command(name='msghandleron', aliases=['msgon'])
    async def _msghandleron(self, ctx):
        self.bot.load_extension('messageHandler')
        await ctx.send('已開啟關鍵字回覆及傳聲筒。')


def setup(bot):
    bot.remove_command('help')  # I want my own help cmd.
    bot.add_cog(adminFunctions(bot))
    print("Admin functions loaded.")
