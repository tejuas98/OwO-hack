import discord
from discord.ext import commands
import json
import asyncio
import sys
import os

# Set working directory to file's directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Load config
CONFIG_FILE = "data/owo_config.json"
EXAMPLE_CONFIG = "data/owo_config.example.json"

if not os.path.exists(CONFIG_FILE) and os.path.exists(EXAMPLE_CONFIG):
    import shutil
    shutil.copy(EXAMPLE_CONFIG, CONFIG_FILE)

try:
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
except Exception as e:
    print(f"[ERROR] Failed to load config: {e}")
    sys.exit(1)

TOKEN = config.get("user_token", "")
CHANNEL_ID_1 = config.get("owo_channel", "")
CHANNEL_ID_2 = config.get("owo_channel_2", "") or CHANNEL_ID_1
CHANNEL_ID_3 = config.get("owo_channel_3", "") or CHANNEL_ID_1
SIMULATE_TYPING = bool(config.get("simulate_typing", True))

SCRIPT_CONTENT_1 = config.get("owo_script", "")
SCRIPT_CONTENT_2 = config.get("owo_script_2", "")
SCRIPT_CONTENT_3 = config.get("owo_script_3", "OwO\nwait 10-15\nOwO\nwait 10-15\nOwO\nwait 10-15")

def parse_script(script_text):
    actions = []
    if not script_text:
        return actions
    for line in script_text.strip().split('\n'):
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('//'):
            continue
        
        line_lower = line.lower()
        if line_lower.startswith("wait"):
            val_str = line_lower.replace("wait", "").strip()
            val_clean = val_str.replace(" ", "")
            if "-" in val_clean:
                parts = val_clean.split("-")
                try:
                    low = float(parts[0])
                    high = float(parts[1])
                    if low > high:
                        low, high = high, low
                    actions.append({"type": "wait_range", "low": low, "high": high})
                    continue
                except ValueError:
                    pass
            try:
                delay = float(val_str)
                actions.append({"type": "wait", "value": delay})
            except ValueError:
                print(f"[WARNING] Invalid wait time in script: {line}")
        else:
            # Allows commands like 'ob', 'wh', 'OwO', 'owo b', 'owo h', etc.
            actions.append({"type": "command", "value": line})
    return actions

parsed_actions_1 = parse_script(SCRIPT_CONTENT_1)
parsed_actions_2 = parse_script(SCRIPT_CONTENT_2)
parsed_actions_3 = parse_script(SCRIPT_CONTENT_3)

if not TOKEN:
    print("[ERROR] Token is missing in owo_config.json")
    sys.exit(1)

def clean_channel_id(cid_val):
    if not cid_val:
        return None
    try:
        return int(str(cid_val).strip())
    except ValueError:
        return None

CH_1 = clean_channel_id(CHANNEL_ID_1)
CH_2 = clean_channel_id(CHANNEL_ID_2)
CH_3 = clean_channel_id(CHANNEL_ID_3)

if not CH_1 and not CH_2 and not CH_3:
    print("[ERROR] No valid Channel ID configured.")
    sys.exit(1)

class OwOBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="owo!", self_bot=True)
        self.spam_task_1 = None
        self.spam_task_2 = None
        self.spam_task_3 = None
        self.owo_bot_id = 408785106942164992  # Official OwO bot ID
        self.last_sent_time = 0.0
        self.send_lock = asyncio.Lock()

    async def on_ready(self):
        print(f"[INFO] Logged in as {self.user.name} ({self.user.id})")
        
        if not self.spam_task_1 and parsed_actions_1 and CH_1:
            print(f"[INFO] Main Loop assigned to channel: {CH_1}")
            self.spam_task_1 = self.loop.create_task(self.execute_loop("Main Loop", CH_1, parsed_actions_1))
        elif not parsed_actions_1:
            print("[INFO] Main Loop script is empty.")
            
        if not self.spam_task_2 and parsed_actions_2 and CH_2:
            print(f"[INFO] Secondary Loop assigned to channel: {CH_2}")
            self.spam_task_2 = self.loop.create_task(self.execute_loop("Secondary Loop", CH_2, parsed_actions_2))
        elif not parsed_actions_2:
            print("[INFO] Secondary Loop script is empty.")

        if not self.spam_task_3 and parsed_actions_3 and CH_3:
            print(f"[INFO] Third Loop assigned to channel: {CH_3}")
            self.spam_task_3 = self.loop.create_task(self.execute_loop("Third Loop", CH_3, parsed_actions_3))
        elif not parsed_actions_3:
            print("[INFO] Third Loop script is empty.")

    async def execute_loop(self, loop_name, channel_id, actions):
        await self.wait_until_ready()
        channel = self.get_channel(channel_id)
        if not channel:
            try:
                channel = await self.fetch_channel(channel_id)
            except Exception as e:
                print(f"[ERROR] Could not find channel {channel_id} for {loop_name}: {e}")
                return

        print(f"[INFO] {loop_name} started in channel: {channel_id}")

        while not self.is_closed():
            for action in actions:
                try:
                    if action["type"] == "wait":
                        print(f"[{loop_name}] Waiting {action['value']}s...")
                        sys.stdout.flush()
                        await asyncio.sleep(action["value"])
                    elif action["type"] == "wait_range":
                        import random
                        delay = round(random.uniform(action["low"], action["high"]), 1)
                        print(f"[{loop_name}] Waiting {delay}s (random {action['low']:g}-{action['high']:g}s)...")
                        sys.stdout.flush()
                        await asyncio.sleep(delay)
                    elif action["type"] == "command":
                        async with self.send_lock:
                            import time
                            import random
                            now = time.time()
                            elapsed = now - self.last_sent_time
                            required_gap = round(random.uniform(2.0, 4.0), 1)
                            if self.last_sent_time > 0 and elapsed < required_gap:
                                extra_wait = round(required_gap - elapsed, 1)
                                print(f"[{loop_name}] Spacing command ({extra_wait}s gap to prevent overlap)...")
                                sys.stdout.flush()
                                await asyncio.sleep(extra_wait)
                            
                            if SIMULATE_TYPING:
                                try:
                                    typing_delay = round(random.uniform(0.6, 1.4), 1)
                                    async with channel.typing():
                                        await asyncio.sleep(typing_delay)
                                except Exception:
                                    pass

                            await channel.send(action["value"])
                            self.last_sent_time = time.time()
                            print(f"[{loop_name}] Sent: {action['value']}")
                            sys.stdout.flush()
                except Exception as e:
                    print(f"[ERROR] [{loop_name}] Failed to execute '{action.get('value')}': {e}")
                    sys.stdout.flush()

    async def on_message(self, message):
        try:
            # Ignore our own messages
            if message.author.id == self.user.id:
                return

            active_channels = {cid for cid in [CH_1, CH_2, CH_3] if cid}
            is_in_active_channel = message.channel.id in active_channels
            is_dm = isinstance(message.channel, discord.DMChannel)

            # Check if the message is in our farming channels or DMs
            if is_in_active_channel or is_dm:
                content_lower = str(message.content).lower()
                for embed in message.embeds:
                    if embed.description:
                        content_lower += " " + str(embed.description).lower()
                    if embed.title:
                        content_lower += " " + str(embed.title).lower()
                
                ch_tag = getattr(message.channel, "name", "DM")
                print(f"[CHAT #{ch_tag}] {message.author.name}: {content_lower}")
                
                # OwO Bot heavily obfuscates its captchas by inserting invisible zero-width unicode characters
                # inside the words. We strip everything except a-z letters to match reliably.
                import re
                clean_content = re.sub(r'[^a-z]', '', content_lower)
                
                # If any message contains the clean captcha text, pause execution
                if "areyouarealhuman" in clean_content or "captcha" in clean_content or "verifythatyouarehuman" in clean_content or "linkbelowssoicancheck" in clean_content or "resultinaban" in clean_content:
                    print("\n" + "="*50)
                    print("[CRITICAL ALERT]")
                    print("CAPTCHA TEXT DETECTED IN CHANNEL OR DM!")
                    print("STOPPING BOT IMMEDIATELY TO PREVENT BAN.")
                    print("="*50 + "\n")
                    sys.stdout.flush()
                    
                    import threading
                    import subprocess
                    import time
                    
                    # 1. Start an infinite ringing background thread
                    stop_ringing = False
                    def ring_alarm():
                        while not stop_ringing:
                            os.system('afplay /System/Library/Sounds/Glass.aiff')
                            time.sleep(0.1)
                            
                    alarm_thread = threading.Thread(target=ring_alarm, daemon=True)
                    alarm_thread.start()
                    
                    # 2. Show a macOS native notification
                    os.system('osascript -e \'display notification "CAPTCHA DETECTED! Bot paused." with title "OwO Bot Alert" sound name "Glass"\'')
                    
                    # 3. Show a blocking popup dialog. The sound loops UNTIL user clicks button
                    subprocess.run([
                        'osascript', '-e',
                        'display alert "OwO Bot Alert" message "CAPTCHA DETECTED! Please verify immediately to prevent a ban." buttons {"Stop Ringing and Exit"} default button "Stop Ringing and Exit"'
                    ])
                    
                    # 4. Stop the ringing and exit
                    stop_ringing = True
                    time.sleep(1)
                    os._exit(0)
        except Exception as e:
            print(f"[ERROR] Failed to process message: {e}")

if __name__ == "__main__":
    bot = OwOBot()
    bot.run(TOKEN)

