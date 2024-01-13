import os
import discord
from discord.ext import commands
import json
import random
import string
import os
from discord.ext.commands import has_guild_permissions
from datetime import datetime, timedelta, timezone
import asyncio
import warnings
import logging
from keep_alive import keep_alive
keep_alive()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS_DIR = os.path.join(BASE_DIR, 'accounts')

BOT_TOKEN = os.environ.get('BOT_TOKEN')

STATUS = discord.Status.idle
ACTIVITY = "The Orders"
ACTIVITY_TYPE = discord.ActivityType.watching
LTC_ADDRESS = "LfWgXamAwJkWeHFowxXu5ZY5YRD5xPXMUA"
BTC_ADDRESS = "No Bitcoin address has been set."
PAYPAL = "No PayPal has been set."

def generate_order_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def get_preorder_channel(guild):
    if str(guild.id) in preorder_channels:
        channel_id = preorder_channels[str(guild.id)]
        channel = guild.get_channel(channel_id)
        return channel
    return None

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

bot = commands.Bot(command_prefix=',', intents=intents)

preorder_channels = {}

try:
    with open('delivered_orders.json', 'r') as file:
        data = file.read()
        delivered_orders = json.loads(data) if data else {}
except (FileNotFoundError, json.JSONDecodeError):
    delivered_orders = {}

@bot.event
async def on_shutdown():
    print('Saving delivered orders...')
    with open('delivered_orders.json', 'w') as file:
        json.dump(delivered_orders, file, indent=4)
    print('Delivered orders saved successfully.')

@bot.event
async def on_ready():
    activity = discord.Activity(name=ACTIVITY, type=ACTIVITY_TYPE)
    await bot.change_presence(status=STATUS, activity=activity)
    print("Bot is ready!")

@bot.command(name='ltc')
@commands.has_guild_permissions(administrator=True)
async def ltc_command(ctx):
    await ctx.message.delete()
    await ctx.send(LTC_ADDRESS)

@bot.command(name='btc')
@commands.has_guild_permissions(administrator=True)
async def btc_command(ctx):
    await ctx.message.delete()
    await ctx.send(BTC_ADDRESS)

@bot.command(name='pp')
@commands.has_guild_permissions(administrator=True)
async def ltc_command(ctx):
    await ctx.message.delete()
    await ctx.send(PAYPAL)

@bot.command(name='preorder', help='Preorder a product')
@commands.has_guild_permissions(administrator=True)
async def preorder_command(ctx, products: str, price: float, quantity: int):
    await ctx.message.delete()
    preorder_details = {}  

    order_id = generate_order_id()

    preorder_details['products'] = products
    preorder_details['price'] = price
    preorder_details['quantity'] = quantity

    order_data = {
        'order_id': order_id,
        'author_id': ctx.author.id,
        'preorder_details': preorder_details,
        'status': 'Not Delivered',
        'color': discord.Color.red().value,
    }

    try:
        with open('orders.json', 'r') as file:
            orders = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        orders = []

    orders.append(order_data)

    with open('orders.json', 'w') as file:
        json.dump(orders, file, indent=4)

    preorder_channel = get_preorder_channel(ctx.guild)

    if preorder_channel:
        embed = discord.Embed(title="Preorder Details", color=discord.Color.red())
        embed.add_field(name="Products", value=preorder_details['products'], inline=False)
        embed.add_field(name="Price", value=preorder_details['price'], inline=False)
        embed.add_field(name="Quantity", value=preorder_details['quantity'], inline=False)
        embed.add_field(name="Order Status", value="Not Delivered", inline=False)
        embed.set_footer(text=f"Order ID: {order_id}")

        message = await preorder_channel.send(embed=embed)
        
        order_data['message_id'] = message.id
        with open('orders.json', 'w') as file:
            json.dump(orders, file, indent=4)

        await ctx.send(f"Preorder details sent to {preorder_channel.mention}. Order ID: {order_id}")
    else:
        await ctx.send("Error: Preorder channel not found. Please set up the preorder channel first.")

@bot.command(name='pchannel', help='Set preorder channel')
@commands.has_guild_permissions(administrator=True)
async def set_preorder_channel(ctx, channel: discord.TextChannel):
    await ctx.message.delete()
    guild_id = ctx.guild.id

    if channel:
        preorder_channels[str(guild_id)] = channel.id

        with open('preorder_channels.json', 'w') as file:
            json.dump(preorder_channels, file, indent=4)

        await ctx.send(f"Preorder channel set to {channel.mention}.")
    else:
        await ctx.send("Error: Channel not found or not specified correctly.")

@bot.command(name='corder', help='Complete an order')
@commands.has_guild_permissions(administrator=True)
async def complete_order(ctx, order_id: str):
    await ctx.message.delete()
    try:
        with open('orders.json', 'r') as file:
            orders = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        await ctx.send("Error: Orders file not found or is not valid JSON.")
        return
    
    for order in orders:
        if order['order_id'] == order_id:
            if 'message_id' in order:
                message_id = order['message_id']
                try:
                    message = await ctx.channel.fetch_message(message_id)

                    embed = message.embeds[0]

                    for index, field in enumerate(embed.fields):
                        if field.name == "Order Status":
                            embed.remove_field(index)
                            break

                    embed.add_field(name="Order Status", value="Delivered", inline=False)

                    embed.color = discord.Color.green()

                    orders.remove(order)

                    with open('orders.json', 'w') as file:
                        json.dump(orders, file, indent=4)

                    await message.edit(embed=embed)
                    await ctx.send(f"Order #{order_id} marked as delivered and removed from orders.")
                except discord.NotFound:
                    await ctx.send(f"Error: Message not found for order ID {order_id}.")
            else:
                await ctx.send(f"Error: No message ID found for order ID {order_id}.")
            return

    await ctx.send(f"Error: Order ID {order_id} not found.")

@bot.command(name='stock', help='Display the number of accounts')
async def stock_command(ctx):
    accounts_file_path = os.path.join(ACCOUNTS_DIR, f'{service.lower()}.txt')

    try:
        files = os.listdir(ACCOUNTS_DIR)
        file_path = os.path.join(ACCOUNTS_DIR, file_name)

    except FileNotFoundError:
        await ctx.send("Error: 'accounts' folder not found.")
        return

    if not files:
        await ctx.send("No accounts found.")
        return

    embed = discord.Embed(title='Stock Information', color=discord.Color.blue())

    for file_name in files:
        file_path = os.path.join(accounts_folder, file_name)
        if os.path.isfile(file_path):
            service_name = os.path.splitext(file_name)[0].capitalize()
            with open(file_path, 'r') as file:
                accounts = file.readlines()
                accounts_count = len(accounts)
                embed.add_field(name=service_name, value=str(accounts_count), inline=False)

    await ctx.send(embed=embed)

@bot.command(name='get', help='Get account(s) from stock')
async def get_command(ctx, service: str, *, indices: str):
    indices = [int(index.strip()) - 1 for index in indices.split(',')]
    accounts_file_path = os.path.join(BASE_DIR, f'{service.lower()}.txt')

    try:
        with open(accounts_file_path, 'r') as file:
            accounts = file.readlines()
    except FileNotFoundError:
        await ctx.send(f"Error: '{service.lower()}.txt' not found.")
        return

    if not accounts:
        await ctx.send(f"No accounts found for {service}.")
        return

    selected_accounts = [accounts[i] for i in indices if 0 <= i < len(accounts)]

    if not selected_accounts:
        await ctx.send("Invalid indices provided.")
        return

    # Send selected accounts via DM
    dm_channel = await ctx.author.create_dm()
    message = "\n".join(selected_accounts)
    await dm_channel.send(f"Here are your {service} account(s):\n{message}")

    # Remove selected accounts from the file
    remaining_accounts = [account for i, account in enumerate(accounts) if i not in indices]
    with open(accounts_file_path, 'w') as file:
        file.writelines(remaining_accounts)

    await ctx.send(f"Sent {len(selected_accounts)} {service} account(s) to your DM and removed them from stock.")

logging.basicConfig(level=logging.INFO)
print(BOT_TOKEN)
bot.run(BOT_TOKEN)
