import discord
from discord.ext import commands
from datetime import timedelta
import asyncio
import config


class messageHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.keywords = []
        self.response = {}
        self.portal_id = int(config.getPortal())  # load the portal id from config
        self.enable_portal_talk = True
        self.kwreply_blacklist = []  # list of guilds that had turned off the keyword reply function
        # read the keyword pairs from file
        try:
            with open('keywords.txt', 'r') as data:
                for line in data:
                    (kw, resp) = line.split(':', 1)
                    self.response[kw] = str(resp)
                for (kw, resp) in self.response.items():
                    self.keywords.append(kw)
            data.close()
        except IOError:
            print('keyword file does not exist!')

    @commands.Cog.listener()
    async def on_message(self, message):
        # Keyword respond function###
        if message.content in self.keywords:
            if message.author == self.bot.user:
                return
            elif message.guild.id in self.kwreply_blacklist:
                return
            else:
                # print('keyword hit')
                msg = self.response[message.content]
                await message.channel.send(msg)
        '''
        if '呼哈' in message.content and message.author != self.bot.user:
            time = message.created_at + timedelta(hours=1)
            msg = '你的下一次呼哈：{:%H:%M:%S}'.format(time)
            await message.channel.send(msg)
        '''
    # portal talking function
        if message.channel.id == self.portal_id and self.enable_portal_talk:
            if message.content:
                await self.bot.get_channel(self.messagedest).send(message.content)
            if message.attachments:
                for each in message.attachments:
                    await self.bot.get_channel(self.messagedest).send(each.url)

    @classmethod
    def set_destination(self, channel_id):
        self.messagedest = channel_id

    @classmethod
    def get_destination(self):
        return self.messagedest

    @commands.command(name='pekofy', aliases=['peko'])  # message pekofier peko!
    async def _pekofy(self, ctx, *args):
        channel = ctx.message.channel
        messages = []
        if args:  # if you want to pekofy your own message or a specific line
            if "-self" in args:
                async for message in channel.history(limit=10):
                    if "pekofy" not in message.content and message.author == ctx.message.author:
                        messages.append(message.content)
                msg = messages[0]
                if msg:
                    peko = msg + ' peko'
                else:
                    peko = '訊息太遠了我搆不到 peko'
            else:
                msg = ''
                for each in args:
                    msg += (each + ' ')
                peko = msg + 'peko'
        else:
            async for message in channel.history(limit=2):
                if "pekofy" not in message.content: # and message.author == ctx.message.author:
                    messages.append(message.content)
            msg = messages[0]
            peko = msg + ' peko'

        if peko.count("peko") >= 10:  # TMP = too much peko. 
            peko = "太多peko了peko。"

        await ctx.send(peko)

        if "pain peko" in peko:  # pain-peko
            await ctx.send("https://i.pinimg.com/736x/f3/ff/0b/f3ff0bfe160d84d6f85bb53c06319406.jpg")

    @commands.command(name='repoff')  # command for turning keyword reply off for specific guild in case someone gets annoyed lmao
    async def _reply_off(self, ctx):
        if ctx.guild.id not in self.kwreply_blacklist:
            self.kwreply_blacklist.append(ctx.guild.id)
        print(self.kwreply_blacklist)
        guild_name = self.bot.get_guild(ctx.guild.id)
        await ctx.send(f"已為**{guild_name}**暫時關閉關鍵字回覆。打擾ㄌ。")

    @commands.command(name='repon')
    async def _reply_on(self, ctx):
        if ctx.guild.id in self.kwreply_blacklist:
            self.kwreply_blacklist.remove(ctx.guild.id)
        print(self.kwreply_blacklist)
        guild_name = self.bot.get_guild(ctx.guild.id)
        await ctx.send(f"已為**{guild_name}**開啟關鍵字回覆。")


def setup(bot):
    bot.add_cog(messageHandler(bot))
    print("Message handler loaded.")
