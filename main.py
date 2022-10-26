import discord
from discord.ext import commands
import requests
import asyncio
import os
from pycoingecko import CoinGeckoAPI
import json
from io import BytesIO
from PIL import Image

# https://github.com/Pycord-Development/pycord
# https://github.com/man-c/pycoingecko

cg = CoinGeckoAPI()

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
bot.remove_command('help')


async def check_symbol(new_symbol):
    data = cg.get_price(ids=new_symbol, vs_currencies='usd')
    return bool(data)


async def cur_price(symbol):
    data = cg.get_price(ids=symbol, vs_currencies='usd')
    return data[symbol]['usd']


async def updt_status():
    with open('config.json') as f:
        d = json.load(f)
        symbol = d["symbol"]
    data = cg.get_coins_markets(ids=symbol, vs_currency='usd')
    price = data[0]['current_price']
    change = round(data[0]['price_change_percentage_24h'], 2)

    if change > 0 or change == 0:
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching,
                                                            name=f"${price} ▲ {change}%"))
    elif change < 0:
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching,
                                                            name=f"${price} ▼ {change}%"))
    await asyncio.sleep(120)
    await updt_status()


async def updt_bot(ctx, new_symbol):
    with open("config.json", "r") as jsonFile:
        data = json.load(jsonFile)
    data["symbol"] = new_symbol
    with open("config.json", "w") as jsonFile:
        json.dump(data, jsonFile)

    data = cg.get_coins_markets(ids=new_symbol, vs_currency='usd')
    image_url = data[0]["image"]
    avatar = requests.get(image_url)
    img = Image.open(BytesIO(avatar.content), mode="r")
    b = BytesIO()
    img.save(b, format='PNG')
    b_value = b.getvalue()
    await bot.user.edit(avatar=b_value)
    await ctx.guild.get_member(bot.user.id).edit(nick=new_symbol)


@bot.slash_command()
async def track(ctx, new_symbol: str = None):
    if not ctx.user.guild_permissions.administrator:
        await ctx.response.send_message("You are not authorized to run this command.", ephemeral=True)
    else:
        new_symbol = new_symbol.lower()
        if not await check_symbol(new_symbol):
            embed = discord.Embed(
                description=f"We couldn't find {new_symbol}!\n"
                            f"Make sure to type correctly.",
                color=discord.colour.Color.red(),
                title=f'<a:failed:972495382116462632> | Coin not found!'
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        await updt_bot(ctx, new_symbol)
        embed = discord.Embed(
            description=f"Now tracking: {new_symbol}\n"
                        f"Current price is ${await cur_price(new_symbol)}",
            color=discord.colour.Color.green(),
            title=f'<a:Verified2:972498838587842583> | Changed tracked crypto!'
        )
        await ctx.respond(embed=embed)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    await updt_status()

bot.run(os.environ["DISCORD_BOT_TOKEN"])
