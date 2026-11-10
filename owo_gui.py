import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
import subprocess
import threading
import shutil
import sys
import os
import json

os.chdir(os.path.dirname(os.path.abspath(__file__)))

CONFIG_FILE = "data/owo_config.json"
EXAMPLE_CONFIG = "data/owo_config.example.json"

class OwOBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("OwO Bot Dashboard")
        self.root.geometry("680x575")
        
        # --- Top Controls & Status Frame ---
        self.top_frame = tk.Frame(root, pady=8, padx=10)
        self.top_frame.pack(fill=tk.X)
        
        self.start_btn = tk.Button(self.top_frame, text="Start Bot", fg="green", font=("Helvetica", 13, "bold"), command=self.start_bot)
        self.start_btn.pack(side=tk.LEFT, padx=(5, 10))
        
        self.stop_btn = tk.Button(self.top_frame, text="Stop Bot", fg="red", font=("Helvetica", 13, "bold"), command=self.stop_bot, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        self.status_lbl = tk.Label(self.top_frame, text="Status: Offline", fg="gray", font=("Helvetica", 12, "bold"))
        self.status_lbl.pack(side=tk.RIGHT, padx=10)
        
        # --- Config Inputs Frame (Token) ---
        self.config_frame = tk.Frame(root, pady=2, padx=15)
        self.config_frame.pack(fill=tk.X)
        
        self.token_var = tk.StringVar()
        self.channel_var_1 = tk.StringVar()
        self.channel_var_2 = tk.StringVar()
        self.channel_var_3 = tk.StringVar()
        self.show_token_var = tk.BooleanVar(value=False)
        
        # Row 1: Auth Token
        token_subframe = tk.Frame(self.config_frame)
        token_subframe.pack(fill=tk.X, pady=2)
        
        tk.Label(token_subframe, text="Auth Token:", font=("Helvetica", 11, "bold"), width=11, anchor="w").pack(side=tk.LEFT)
        self.token_entry = tk.Entry(token_subframe, textvariable=self.token_var, font=("Consolas", 10), show="*")
        self.token_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))
        
        self.toggle_token_btn = tk.Checkbutton(token_subframe, text="Show", variable=self.show_token_var, command=self.toggle_token_visibility)
        self.toggle_token_btn.pack(side=tk.RIGHT)
        
        # Row 2: Options
        options_subframe = tk.Frame(self.config_frame)
        options_subframe.pack(fill=tk.X, pady=2)
        self.typing_var = tk.BooleanVar(value=True)
        self.typing_cb = tk.Checkbutton(options_subframe, text="Simulate typing status ('User is typing...')", variable=self.typing_var)
        self.typing_cb.pack(side=tk.LEFT)
        
        initial_script_1 = "ob\nwait 16-20\nob\nwait 16-20\nob\nwait 16-20\nob\nwait 16-20"
        initial_script_2 = "wait 3\nwh\nwait 16-20\nwh\nwait 16-20\nwh\nwait 16-20"
        initial_script_3 = "wait 5\nOwO\nwait 10-15\nOwO\nwait 10-15\nOwO\nwait 10-15"
        
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(CONFIG_FILE) and os.path.exists(EXAMPLE_CONFIG):
            shutil.copy(EXAMPLE_CONFIG, CONFIG_FILE)
            
        try:
            with open(CONFIG_FILE, "r") as f:
                conf = json.load(f)
                self.token_var.set(str(conf.get("user_token", "")))
                
                ch1 = str(conf.get("owo_channel", ""))
                self.channel_var_1.set(ch1)
                self.channel_var_2.set(str(conf.get("owo_channel_2", "")) or ch1)
                self.channel_var_3.set(str(conf.get("owo_channel_3", "")) or ch1)
                self.typing_var.set(bool(conf.get("simulate_typing", True)))
                
                initial_script_1 = conf.get("owo_script", initial_script_1)
                initial_script_2 = conf.get("owo_script_2", initial_script_2)
                initial_script_3 = conf.get("owo_script_3", initial_script_3)
        except Exception:
            self.token_var.set("")
            self.channel_var_1.set("")
            self.channel_var_2.set("")
            self.channel_var_3.set("")
            
        self.settings_frame = tk.Frame(root, pady=5)
        self.settings_frame.pack(fill=tk.BOTH, expand=False)
        
        # Tabs for Scripts
        self.notebook = ttk.Notebook(self.settings_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=2)
        
        # --- Tab 1: Main Loop ---
        self.tab1 = tk.Frame(self.notebook, bg="#2b2b2b", padx=8, pady=6)
        self.notebook.add(self.tab1, text="Main Loop")
        
        tab1_header = tk.Frame(self.tab1, bg="#2b2b2b")
        tab1_header.pack(fill=tk.X, pady=(0, 4))
        tk.Label(tab1_header, text="Channel ID:", bg="#2b2b2b", fg="#ffffff", font=("Helvetica", 10, "bold")).pack(side=tk.LEFT)
        self.channel_entry_1 = tk.Entry(tab1_header, textvariable=self.channel_var_1, font=("Consolas", 10), width=28)
        self.channel_entry_1.pack(side=tk.LEFT, padx=(6, 10))
        
        self.script_area_1 = scrolledtext.ScrolledText(self.tab1, height=4, font=("Consolas", 11), bg="#222222", fg="#ffffff", borderwidth=0)
        self.script_area_1.pack(fill=tk.BOTH, expand=True)
        self.script_area_1.insert(tk.END, initial_script_1)
        
        # --- Tab 2: Secondary Loop ---
        self.tab2 = tk.Frame(self.notebook, bg="#2b2b2b", padx=8, pady=6)
        self.notebook.add(self.tab2, text="Secondary Loop")
        
        tab2_header = tk.Frame(self.tab2, bg="#2b2b2b")
        tab2_header.pack(fill=tk.X, pady=(0, 4))
        tk.Label(tab2_header, text="Channel ID:", bg="#2b2b2b", fg="#ffffff", font=("Helvetica", 10, "bold")).pack(side=tk.LEFT)
        self.channel_entry_2 = tk.Entry(tab2_header, textvariable=self.channel_var_2, font=("Consolas", 10), width=28)
        self.channel_entry_2.pack(side=tk.LEFT, padx=(6, 10))
        
        self.script_area_2 = scrolledtext.ScrolledText(self.tab2, height=4, font=("Consolas", 11), bg="#222222", fg="#ffffff", borderwidth=0)
        self.script_area_2.pack(fill=tk.BOTH, expand=True)
        self.script_area_2.insert(tk.END, initial_script_2)
        
        # --- Tab 3: Third Loop ---
        self.tab3 = tk.Frame(self.notebook, bg="#2b2b2b", padx=8, pady=6)
        self.notebook.add(self.tab3, text="Third Loop")
        
        tab3_header = tk.Frame(self.tab3, bg="#2b2b2b")
        tab3_header.pack(fill=tk.X, pady=(0, 4))
        tk.Label(tab3_header, text="Channel ID:", bg="#2b2b2b", fg="#ffffff", font=("Helvetica", 10, "bold")).pack(side=tk.LEFT)
        self.channel_entry_3 = tk.Entry(tab3_header, textvariable=self.channel_var_3, font=("Consolas", 10), width=28)
        self.channel_entry_3.pack(side=tk.LEFT, padx=(6, 10))
        
        self.script_area_3 = scrolledtext.ScrolledText(self.tab3, height=4, font=("Consolas", 11), bg="#222222", fg="#ffffff", borderwidth=0)
        self.script_area_3.pack(fill=tk.BOTH, expand=True)
        self.script_area_3.insert(tk.END, initial_script_3)
        
        # --- Bottom Log Area ---
        self.log_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Consolas", 11), bg="#1e1e1e", fg="#00ff00")
        self.log_area.pack(expand=True, fill=tk.BOTH, padx=10, pady=8)
        self.log_area.insert(tk.END, "Welcome to OwO Bot Dashboard!\nConfigure Main, Secondary, and Third Loop tabs above, then click 'Start Bot'...\n")
        self.log_area.configure(state='disabled')
        
        self.process = None
        self.thread = None
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def toggle_token_visibility(self):
        if self.show_token_var.get():
            self.token_entry.config(show="")
        else:
            self.token_entry.config(show="*")

    def log(self, message):
        self.log_area.configure(state='normal')
        self.log_area.insert(tk.END, message)
        self.log_area.see(tk.END)
        self.log_area.configure(state='disabled')

    def read_output(self):
        while self.process and self.process.poll() is None:
            line = self.process.stdout.readline()
            if line:
                self.root.after(0, self.log, line)
        
        if self.process:
            self.root.after(0, self.handle_process_exit)

    def handle_process_exit(self):
        self.log("\n[System] Bot stopped running.\n")
        self.status_lbl.config(text="Status: Offline", fg="gray")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.process = None

    def start_bot(self):
        if self.process is None:
            selected_token = self.token_var.get().strip()
            ch1 = self.channel_var_1.get().strip()
            ch2 = self.channel_var_2.get().strip()
            ch3 = self.channel_var_3.get().strip()
            
            if not selected_token:
                self.log("\n[Error] Please enter your Authorization Token before starting the bot.\n")
                return
                
            if not ch1 and not ch2 and not ch3:
                self.log("\n[Error] Please enter at least one Channel ID before starting the bot.\n")
                return
                
            script_content_1 = self.script_area_1.get("1.0", tk.END).strip()
            script_content_2 = self.script_area_2.get("1.0", tk.END).strip()
            script_content_3 = self.script_area_3.get("1.0", tk.END).strip()
                
            try:
                conf = {}
                if os.path.exists(CONFIG_FILE):
                    with open(CONFIG_FILE, "r") as f:
                        conf = json.load(f)
                conf["user_token"] = selected_token
                conf["owo_channel"] = ch1
                conf["owo_channel_2"] = ch2
                conf["owo_channel_3"] = ch3
                conf["owo_script"] = script_content_1
                conf["owo_script_2"] = script_content_2
                conf["owo_script_3"] = script_content_3
                conf["simulate_typing"] = self.typing_var.get()
                with open(CONFIG_FILE, "w") as f:
                    json.dump(conf, f, indent=3)
                self.log(f"\n[System] Saved configuration to owo_config.json.\n")
            except Exception as e:
                self.log(f"\n[Error] Could not save config: {e}\n")

            self.log("\n[System] Starting OwO Bot...\n")
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "owo_main.py")
            
            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"
            
            self.process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                cwd=os.path.dirname(script_path),
                env=env
            )
            
            self.status_lbl.config(text="Status: Running", fg="green")
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            
            self.thread = threading.Thread(target=self.read_output, daemon=True)
            self.thread.start()

    def stop_bot(self):
        if self.process:
            self.log("\n[System] Stopping OwO Bot...\n")
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
            
            self.handle_process_exit()

    def on_closing(self):
        self.stop_bot()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = OwOBotGUI(root)
    root.mainloop()

