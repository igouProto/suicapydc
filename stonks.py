from discord.ext import commands
import discord
import yfinance as yf
import re  # for regex matching for code
import datetime

class Stonks(commands.Cog):

    @commands.command(name='stonks', aliases=['st'])
    async def _stonks(self, ctx, code: str = None):
        tw_stock_code_pattern = "[0-9]{4}"
        await ctx.trigger_typing()
        if code:
            if re.match(tw_stock_code_pattern, code):
                code += ".TW"
            print(code)
            try:
                stonk = yf.Ticker(code)
                name = stonk.info["longName"] if "longName" in stonk.info else stonk.info["name"]
                price = stonk.info["regularMarketPrice"]
                prev_close = stonk.info["previousClose"]
                high = stonk.info["dayHigh"]
                low = stonk.info["dayLow"]

                color_up = 0xff2600
                color_down = 0x00f900

                diff = abs(price - prev_close)
                diff_percent = 100 * (diff / prev_close)
                indicator = ['-', '▼']
                title = "📉  NOT STONKS"
                color = color_down

                if price > prev_close:  # if it STONKS
                    color = color_up
                    indicator = ['+', '▲']
                    title = "📈  STONKS"

                price_disp = f"{price: .2f} ({indicator[0]}{abs(diff): .2f}, {indicator[1]}{diff_percent: .2f}%)"

                embed = discord.Embed(title=f"{price_disp}", description=f"{name}", color=color)
                embed.set_author(name=f"{title}")
                embed.add_field(name="上次收盤", value=f"{prev_close}", inline=True)
                embed.add_field(name="最高", value=f"{high}", inline=True)
                embed.add_field(name="最低", value=f"{low}", inline=True)
                embed.set_footer(text="免責聲明：作者不會玩股票，只是想練習接別人的API。")
                await ctx.send(embed=embed)
            except:
                await ctx.send('窩找不到 :(')


def setup(bot):
    bot.add_cog(Stonks(bot))
    print("STONKS loaded.")