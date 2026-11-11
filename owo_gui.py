import tkinter as tk
import subprocess
import threading
import shutil
import sys
import os
import json

os.chdir(os.path.dirname(os.path.abspath(__file__)))

CONFIG_FILE = "data/owo_config.json"
EXAMPLE_CONFIG = "data/owo_config.example.json"

# --- Discord Midnight AMOLED Theme Palette ---
COLOR_BG_ROOT = "#000000"         # Pitch Black (Discord Midnight AMOLED)
COLOR_BG_SURFACE = "#111214"      # Discord Dark Card Surface
COLOR_BG_INPUT = "#18191c"        # Input background
COLOR_BORDER = "#2b2d31"          # Discord subtle border
COLOR_BORDER_FOCUS = "#5865f2"    # Discord Blurple focus outline

COLOR_TEXT_PRIMARY = "#f2f3f5"    # Discord pure white
COLOR_TEXT_MUTED = "#949ba4"      # Discord muted gray
COLOR_BLURPLE = "#5865f2"         # Discord Blurple Accent
COLOR_BLURPLE_HOVER = "#4752c4"   # Hover Blurple
COLOR_RED = "#da373c"             # Discord Red (Stop)
COLOR_RED_HOVER = "#c53030"
COLOR_GREEN = "#23a55a"           # Discord Green (Running/Success)
COLOR_DISABLED_BG = "#1e1f22"
COLOR_DISABLED_FG = "#4e5058"

# Terminal Syntax Highlighting
COLOR_TAG_INFO = "#5865f2"        # Discord Blurple
COLOR_TAG_MAIN = "#57f287"        # Bright Emerald Green
COLOR_TAG_SEC = "#fee75c"         # Discord Yellow
COLOR_TAG_THIRD = "#eb459e"       # Discord Fuchsia
COLOR_TAG_CHAT = "#5865f2"        # Discord Blurple
COLOR_TAG_TYPING = "#00d26a"      # Mint / Typing Green
COLOR_TAG_WAIT = "#faa61a"        # Amber / Orange
COLOR_TAG_ALERT = "#ed4245"       # Discord Red Alert
COLOR_TAG_GEM = "#00e5ff"         # Diamond Cyan (Auto-Gem)
COLOR_TAG_DEFAULT = "#dbdee1"     # Clean soft white


class DiscordButton(tk.Label):
    """Sleek Discord pill button with hover feedback and enabled/disabled states."""
    def __init__(self, parent, text, bg, fg, hover_bg, command=None, padx=16, pady=6, font=("Helvetica", 11, "bold"), **kwargs):
        self.default_bg = bg
        self.default_fg = fg
        self.hover_bg = hover_bg
        self.cmd = command
        self.is_enabled = True
        super().__init__(parent, text=text, bg=bg, fg=fg, font=font, padx=padx, pady=pady, cursor="hand2", **kwargs)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

    def _on_enter(self, e):
        if self.is_enabled:
            self.configure(bg=self.hover_bg)

    def _on_leave(self, e):
        if self.is_enabled:
            self.configure(bg=self.default_bg)

    def _on_click(self, e):
        if self.is_enabled and self.cmd:
            self.cmd()

    def set_state(self, enabled):
        self.is_enabled = enabled
        if enabled:
            self.configure(bg=self.default_bg, fg=self.default_fg, cursor="hand2")
        else:
            self.configure(bg=COLOR_DISABLED_BG, fg=COLOR_DISABLED_FG, cursor="arrow")


class DiscordCheckbox(tk.Frame):
    """Discord styled checkmark box with smooth toggle."""
    def __init__(self, parent, text, variable, command=None, bg=COLOR_BG_ROOT):
        super().__init__(parent, bg=bg)
        self.var = variable
        self.cmd = command
        self.bg_color = bg

        self.box = tk.Label(self, text="✓" if self.var.get() else "  ", font=("Helvetica", 9, "bold"),
                            bg=COLOR_BLURPLE if self.var.get() else "#18191c",
                            fg="#ffffff" if self.var.get() else "#18191c",
                            width=2, relief="flat", highlightthickness=1,
                            highlightbackground=COLOR_BLURPLE if self.var.get() else "#4e5058", cursor="hand2")
        self.box.pack(side=tk.LEFT, padx=(0, 7), pady=2)

        self.lbl = tk.Label(self, text=text, fg=COLOR_TEXT_PRIMARY, bg=bg, font=("Helvetica", 10), cursor="hand2")
        self.lbl.pack(side=tk.LEFT)

        self.box.bind("<Button-1>", self._toggle)
        self.lbl.bind("<Button-1>", self._toggle)

    def _toggle(self, e=None):
        self.var.set(not self.var.get())
        self.update_display()
        if self.cmd:
            self.cmd()

    def update_display(self):
        val = self.var.get()
        if val:
            self.box.configure(text="✓", bg=COLOR_BLURPLE, fg="#ffffff", highlightbackground=COLOR_BLURPLE)
        else:
            self.box.configure(text="  ", bg="#18191c", fg="#18191c", highlightbackground="#4e5058")


class DiscordTabButton(tk.Label):
    """Pill tab button for selecting execution loops."""
    def __init__(self, parent, text, tab_id, on_select, font=("Helvetica", 10, "bold")):
        self.tab_id = tab_id
        self.on_select = on_select
        self.is_active = False
        super().__init__(parent, text=text, bg="#18191c", fg=COLOR_TEXT_MUTED, font=font, padx=14, pady=5, cursor="hand2")
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

    def _on_enter(self, e):
        if not self.is_active:
            self.configure(bg="#232428", fg="#dbdee1")

    def _on_leave(self, e):
        if not self.is_active:
            self.configure(bg="#18191c", fg=COLOR_TEXT_MUTED)

    def _on_click(self, e):
        self.on_select(self.tab_id)

    def set_active(self, active):
        self.is_active = active
        if active:
            self.configure(bg=COLOR_BLURPLE, fg="#ffffff")
        else:
            self.configure(bg="#18191c", fg=COLOR_TEXT_MUTED)


class AutoScrollbar(tk.Scrollbar):
    """Scrollbar that automatically appears only when content overflows."""
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.pack_forget()
        else:
            if not self.winfo_ismapped():
                self.pack(side=tk.RIGHT, fill=tk.Y)
        super().set(lo, hi)


class OwOBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("OwO Bot Dashboard")
        self.root.geometry("730x600")
        self.root.minsize(680, 520)
        self.root.configure(bg=COLOR_BG_ROOT)

        # Variables
        self.token_var = tk.StringVar()
        self.channel_var_1 = tk.StringVar()
        self.channel_var_2 = tk.StringVar()
        self.channel_var_3 = tk.StringVar()
        self.show_token_var = tk.BooleanVar(value=False)
        self.loop_1_enable_var = tk.BooleanVar(value=True)
        self.loop_2_enable_var = tk.BooleanVar(value=True)
        self.loop_3_enable_var = tk.BooleanVar(value=True)
        self.typing_var = tk.BooleanVar(value=True)
        self.auto_gems_var = tk.BooleanVar(value=True)
        self.gem_command_var = tk.StringVar(value="owo use 52 66 73")
        self.current_tab = 1
        self._suppress_tab_save = False

        # Default fallback scripts
        self.script_data_1 = "ob\nwait 16-20\nob\nwait 16-20\nob\nwait 16-20"
        self.script_data_2 = "wait 3\nwh\nwait 16-20\nwh\nwait 16-20\nwh\nwait 16-20"
        self.script_data_3 = "wait 5\nOwO\nwait 10-15\nOwO\nwait 10-15\nOwO\nwait 10-15"

        self.load_config()

        # ==========================================
        # 1. Top Controls Frame (Pill Buttons & Status)
        # ==========================================
        self.top_frame = tk.Frame(root, bg=COLOR_BG_ROOT, padx=14, pady=10)
        self.top_frame.pack(fill=tk.X)

        self.start_btn = DiscordButton(self.top_frame, text="▶  Start Bot", bg=COLOR_BLURPLE, fg="#ffffff",
                                       hover_bg=COLOR_BLURPLE_HOVER, command=self.start_bot)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.stop_btn = DiscordButton(self.top_frame, text="■  Stop Bot", bg=COLOR_RED, fg="#ffffff",
                                      hover_bg=COLOR_RED_HOVER, command=self.stop_bot)
        self.stop_btn.pack(side=tk.LEFT)
        self.stop_btn.set_state(False)

        self.status_lbl = tk.Label(self.top_frame, text="○ Offline", fg=COLOR_TEXT_MUTED, bg=COLOR_BG_ROOT, font=("Helvetica", 11, "bold"))
        self.status_lbl.pack(side=tk.RIGHT, padx=5)

        # ==========================================
        # 2. Config Header (Auth Token & Options)
        # ==========================================
        self.config_frame = tk.Frame(root, bg=COLOR_BG_ROOT, padx=14, pady=2)
        self.config_frame.pack(fill=tk.X)

        # Row 1: Auth Token Entry
        token_row = tk.Frame(self.config_frame, bg=COLOR_BG_ROOT)
        token_row.pack(fill=tk.X, pady=(0, 6))

        tk.Label(token_row, text="Auth Token:", fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_ROOT,
                 font=("Helvetica", 10, "bold"), width=11, anchor="w").pack(side=tk.LEFT)

        self.token_entry = tk.Entry(token_row, textvariable=self.token_var, font=("Menlo", 10), show="•",
                                    bg=COLOR_BG_INPUT, fg=COLOR_TEXT_PRIMARY, insertbackground=COLOR_BLURPLE,
                                    relief="flat", highlightthickness=1, highlightbackground=COLOR_BORDER, highlightcolor=COLOR_BLURPLE)
        self.token_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 10), ipady=3)

        self.show_token_cb = DiscordCheckbox(token_row, text="Show", variable=self.show_token_var, command=self.toggle_token_visibility)
        self.show_token_cb.pack(side=tk.RIGHT)

        # Row 2: Options (Human Typing & Auto-Gems Every 25 Hunts)
        options_row = tk.Frame(self.config_frame, bg=COLOR_BG_ROOT)
        options_row.pack(fill=tk.X, pady=(0, 8))

        self.typing_cb = DiscordCheckbox(options_row, text="Simulate typing status", variable=self.typing_var)
        self.typing_cb.pack(side=tk.LEFT, padx=(0, 14))

        self.auto_gems_cb = DiscordCheckbox(options_row, text="Auto-use gems every 25 hunts", variable=self.auto_gems_var)
        self.auto_gems_cb.pack(side=tk.LEFT, padx=(0, 8))

        tk.Label(options_row, text="Gems:", fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_ROOT,
                 font=("Helvetica", 9, "bold")).pack(side=tk.LEFT, padx=(0, 4))

        self.gem_cmd_entry = tk.Entry(options_row, textvariable=self.gem_command_var, font=("Menlo", 9),
                                      bg=COLOR_BG_INPUT, fg="#00e5ff", insertbackground=COLOR_BLURPLE,
                                      relief="flat", highlightthickness=1, highlightbackground=COLOR_BORDER,
                                      highlightcolor=COLOR_BLURPLE, width=17)
        self.gem_cmd_entry.pack(side=tk.LEFT, ipady=2)

        # ==========================================
        # 3. Discord Tab Bar
        # ==========================================
        self.tab_bar = tk.Frame(root, bg=COLOR_BG_ROOT, padx=14)
        self.tab_bar.pack(fill=tk.X)

        self.tab_btn_1 = DiscordTabButton(self.tab_bar, text="Main Loop", tab_id=1, on_select=self.switch_tab)
        self.tab_btn_1.pack(side=tk.LEFT, padx=(0, 4))

        self.tab_btn_2 = DiscordTabButton(self.tab_bar, text="Secondary Loop", tab_id=2, on_select=self.switch_tab)
        self.tab_btn_2.pack(side=tk.LEFT, padx=(0, 4))

        self.tab_btn_3 = DiscordTabButton(self.tab_bar, text="Third Loop", tab_id=3, on_select=self.switch_tab)
        self.tab_btn_3.pack(side=tk.LEFT)

        # ==========================================
        # 4. Tab Card Container
        # ==========================================
        self.tab_card = tk.Frame(root, bg=COLOR_BG_SURFACE, padx=12, pady=10, highlightthickness=1, highlightbackground=COLOR_BORDER)
        self.tab_card.pack(fill=tk.X, padx=14, pady=(0, 10))

        # Tab Header Line: [✓] Enable Loop + Channel ID: [ entry ]
        self.card_header = tk.Frame(self.tab_card, bg=COLOR_BG_SURFACE)
        self.card_header.pack(fill=tk.X, pady=(0, 8))

        self.loop_enable_cb = DiscordCheckbox(self.card_header, text="Enable Loop", variable=self.loop_1_enable_var,
                                              command=self.on_enable_toggled, bg=COLOR_BG_SURFACE)
        self.loop_enable_cb.pack(side=tk.LEFT)

        tk.Label(self.card_header, text="Channel ID:", fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_SURFACE,
                 font=("Helvetica", 10, "bold")).pack(side=tk.LEFT, padx=(22, 6))

        self.current_channel_var = tk.StringVar(value=self.channel_var_1.get())
        self.current_channel_var.trace_add("write", self.on_channel_modified)

        self.channel_entry = tk.Entry(self.card_header, textvariable=self.current_channel_var, font=("Menlo", 10),
                                      bg=COLOR_BG_INPUT, fg="#57f287", insertbackground=COLOR_BLURPLE,
                                      relief="flat", highlightthickness=1, highlightbackground=COLOR_BORDER, highlightcolor=COLOR_BLURPLE)
        self.channel_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)

        # Tab Script Area
        self.script_border = tk.Frame(self.tab_card, bg=COLOR_BORDER, padx=1, pady=1)
        self.script_border.pack(fill=tk.X)

        self.script_txt = tk.Text(self.script_border, height=5, font=("Menlo", 10), bg="#000000", fg=COLOR_TEXT_PRIMARY,
                                  insertbackground=COLOR_BLURPLE, relief="flat", bd=0, padx=8, pady=6)
        self.script_txt.pack(fill=tk.BOTH, expand=True)

        # ==========================================
        # 5. Live Console Log Box
        # ==========================================
        self.console_hdr = tk.Frame(root, bg=COLOR_BG_ROOT, padx=14)
        self.console_hdr.pack(fill=tk.X, pady=(0, 2))

        tk.Label(self.console_hdr, text="Live Output & Channel Telemetry", fg=COLOR_TEXT_MUTED, bg=COLOR_BG_ROOT,
                 font=("Helvetica", 9, "bold")).pack(side=tk.LEFT)

        self.console_frame = tk.Frame(root, bg=COLOR_BORDER, padx=1, pady=1)
        self.console_frame.pack(fill=tk.BOTH, expand=True, padx=14, pady=(0, 12))

        self.log_area = tk.Text(self.console_frame, font=("Menlo", 9), bg="#000000", fg=COLOR_TAG_DEFAULT,
                                insertbackground=COLOR_BLURPLE, relief="flat", bd=0, padx=8, pady=8)
        self.scrollbar = AutoScrollbar(self.console_frame, orient="vertical", command=self.log_area.yview,
                                      bg="#111214", troughcolor="#000000", activebackground=COLOR_BLURPLE,
                                      highlightthickness=0, bd=0, width=10)
        self.log_area.configure(yscrollcommand=self.scrollbar.set)

        self.log_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Setup Tag Styling for Syntax Highlighting
        self.log_area.tag_configure("info", foreground=COLOR_TAG_INFO)
        self.log_area.tag_configure("main", foreground=COLOR_TAG_MAIN)
        self.log_area.tag_configure("sec", foreground=COLOR_TAG_SEC)
        self.log_area.tag_configure("third", foreground=COLOR_TAG_THIRD)
        self.log_area.tag_configure("typing", foreground=COLOR_TAG_TYPING)
        self.log_area.tag_configure("wait", foreground=COLOR_TAG_WAIT)
        self.log_area.tag_configure("chat", foreground=COLOR_TAG_CHAT)
        self.log_area.tag_configure("gem", foreground=COLOR_TAG_GEM)
        self.log_area.tag_configure("alert", foreground=COLOR_TAG_ALERT)
        self.log_area.tag_configure("default", foreground=COLOR_TAG_DEFAULT)

        self.log_area.insert(tk.END, "Welcome to OwO Bot Dashboard!\nConfigure Main, Secondary, and Third Loop tabs above, then click 'Start Bot'...\n", "info")
        self.log_area.configure(state="disabled")

        # Set Initial Active Tab without saving over config
        self.switch_tab(1, save_previous=False)

        self.process = None
        self.thread = None
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def load_config(self):
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
                self.auto_gems_var.set(bool(conf.get("auto_use_gems", True)))
                self.gem_command_var.set(str(conf.get("gem_command", "owo use 52 66 73")))
                self.loop_1_enable_var.set(bool(conf.get("loop_1_enabled", True)))
                self.loop_2_enable_var.set(bool(conf.get("loop_2_enabled", True)))
                self.loop_3_enable_var.set(bool(conf.get("loop_3_enabled", True)))

                self.script_data_1 = conf.get("owo_script", self.script_data_1)
                self.script_data_2 = conf.get("owo_script_2", self.script_data_2)
                self.script_data_3 = conf.get("owo_script_3", self.script_data_3)
        except Exception:
            pass

    def save_current_tab_state(self):
        if self._suppress_tab_save:
            return
        content = self.script_txt.get("1.0", tk.END).strip()
        ch_val = self.current_channel_var.get().strip()
        if self.current_tab == 1:
            if content:
                self.script_data_1 = content
            self.channel_var_1.set(ch_val)
        elif self.current_tab == 2:
            if content:
                self.script_data_2 = content
            self.channel_var_2.set(ch_val)
        elif self.current_tab == 3:
            if content:
                self.script_data_3 = content
            self.channel_var_3.set(ch_val)

    def switch_tab(self, tab_id, save_previous=True):
        if save_previous:
            self.save_current_tab_state()
        self.current_tab = tab_id

        # Update Tab Button Highlights
        self.tab_btn_1.set_active(tab_id == 1)
        self.tab_btn_2.set_active(tab_id == 2)
        self.tab_btn_3.set_active(tab_id == 3)

        # Load content for the active tab
        self._suppress_tab_save = True
        self.script_txt.delete("1.0", tk.END)
        if tab_id == 1:
            self.loop_enable_cb.var = self.loop_1_enable_var
            self.loop_enable_cb.update_display()
            self.current_channel_var.set(self.channel_var_1.get())
            self.script_txt.insert(tk.END, self.script_data_1)
        elif tab_id == 2:
            self.loop_enable_cb.var = self.loop_2_enable_var
            self.loop_enable_cb.update_display()
            self.current_channel_var.set(self.channel_var_2.get())
            self.script_txt.insert(tk.END, self.script_data_2)
        elif tab_id == 3:
            self.loop_enable_cb.var = self.loop_3_enable_var
            self.loop_enable_cb.update_display()
            self.current_channel_var.set(self.channel_var_3.get())
            self.script_txt.insert(tk.END, self.script_data_3)
        self._suppress_tab_save = False

    def on_channel_modified(self, *args):
        if self._suppress_tab_save:
            return
        val = self.current_channel_var.get().strip()
        if self.current_tab == 1:
            self.channel_var_1.set(val)
        elif self.current_tab == 2:
            self.channel_var_2.set(val)
        elif self.current_tab == 3:
            self.channel_var_3.set(val)

    def on_enable_toggled(self):
        pass

    def toggle_token_visibility(self):
        if self.show_token_var.get():
            self.token_entry.config(show="")
        else:
            self.token_entry.config(show="•")

    def log(self, message):
        self.log_area.configure(state="normal")
        tag = "default"
        msg_lower = message.lower()
        if "[info]" in msg_lower:
            tag = "info"
        elif "[main loop] sent:" in msg_lower or "[main loop] logged in" in msg_lower:
            tag = "main"
        elif "[secondary loop] sent:" in msg_lower:
            tag = "sec"
        elif "[third loop] sent:" in msg_lower:
            tag = "third"
        elif "typing (" in msg_lower or "typing..." in msg_lower:
            tag = "typing"
        elif "waiting" in msg_lower or "spacing command" in msg_lower or "gap to prevent" in msg_lower:
            tag = "wait"
        elif "[chat" in msg_lower:
            tag = "chat"
        elif "[auto-gem]" in msg_lower or "used gems" in msg_lower:
            tag = "gem"
        elif "[error]" in msg_lower or "alert" in msg_lower or "captcha" in msg_lower:
            tag = "alert"

        self.log_area.insert(tk.END, message, tag)
        self.log_area.see(tk.END)
        self.log_area.configure(state="disabled")

    def read_output(self):
        while self.process and self.process.poll() is None:
            line = self.process.stdout.readline()
            if line:
                self.root.after(0, self.log, line)
        if self.process:
            self.root.after(0, self.handle_process_exit)

    def handle_process_exit(self):
        self.log("[System] Bot stopped running.\n")
        self.status_lbl.config(text="○ Offline", fg=COLOR_TEXT_MUTED)
        self.start_btn.set_state(True)
        self.stop_btn.set_state(False)
        self.process = None

    def start_bot(self):
        if self.process is None:
            self.save_current_tab_state()

            selected_token = self.token_var.get().strip()
            ch1 = self.channel_var_1.get().strip()
            ch2 = self.channel_var_2.get().strip()
            ch3 = self.channel_var_3.get().strip()

            if not selected_token:
                self.log("[Error] Please enter your Authorization Token before starting.\n")
                return

            en1 = self.loop_1_enable_var.get()
            en2 = self.loop_2_enable_var.get()
            en3 = self.loop_3_enable_var.get()

            if not en1 and not en2 and not en3:
                self.log("[Error] Please enable at least one loop before starting.\n")
                return

            if en1 and not ch1:
                self.log("[Error] Main Loop is enabled but Channel ID is empty.\n")
                return
            if en2 and not ch2:
                self.log("[Error] Secondary Loop is enabled but Channel ID is empty.\n")
                return
            if en3 and not ch3:
                self.log("[Error] Third Loop is enabled but Channel ID is empty.\n")
                return

            try:
                conf = {}
                if os.path.exists(CONFIG_FILE):
                    with open(CONFIG_FILE, "r") as f:
                        conf = json.load(f)
                conf["user_token"] = selected_token
                conf["owo_channel"] = ch1
                conf["owo_channel_2"] = ch2
                conf["owo_channel_3"] = ch3
                conf["owo_script"] = self.script_data_1
                conf["owo_script_2"] = self.script_data_2
                conf["owo_script_3"] = self.script_data_3
                conf["simulate_typing"] = self.typing_var.get()
                conf["auto_use_gems"] = self.auto_gems_var.get()
                conf["gem_command"] = self.gem_command_var.get().strip() or "owo use 52 66 73"
                conf["gem_interval"] = 25
                conf["loop_1_enabled"] = en1
                conf["loop_2_enabled"] = en2
                conf["loop_3_enabled"] = en3
                with open(CONFIG_FILE, "w") as f:
                    json.dump(conf, f, indent=3)
                self.log("[System] Saved configuration to owo_config.json.\n")
            except Exception as e:
                self.log(f"[Error] Could not save config: {e}\n")

            self.log("[System] Starting OwO Bot...\n")
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

            self.status_lbl.config(text="● Running", fg=COLOR_GREEN)
            self.start_btn.set_state(False)
            self.stop_btn.set_state(True)

            self.thread = threading.Thread(target=self.read_output, daemon=True)
            self.thread.start()

    def stop_bot(self):
        if self.process:
            self.log("[System] Stopping OwO Bot...\n")
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
