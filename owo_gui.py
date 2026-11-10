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

# --- Modern Dark Theme Palette (Discord & Obsidian inspired) ---
COLOR_BG_ROOT = "#18191c"         # Deep background
COLOR_BG_HEADER = "#1e1f22"       # Nav header background
COLOR_BG_CARD = "#232428"         # Container card background
COLOR_BG_INPUT = "#111214"        # Dark input & editor background
COLOR_BORDER = "#313338"          # Subtle card border
COLOR_BORDER_FOCUS = "#5865f2"    # Focus outline
COLOR_TEXT_WHITE = "#f2f3f5"      # Bright primary text
COLOR_TEXT_MUTED = "#949ba4"      # Muted secondary text
COLOR_PRIMARY = "#5865f2"         # Blurple accent
COLOR_PRIMARY_HOVER = "#4752c4"
COLOR_SUCCESS = "#23a55a"         # Vibrant Emerald
COLOR_SUCCESS_HOVER = "#1f9250"
COLOR_DANGER = "#da373c"          # Crimson Red
COLOR_DANGER_HOVER = "#c53030"
COLOR_DISABLED_BG = "#2b2d31"
COLOR_DISABLED_FG = "#6d6f78"

# Terminal Syntax Colors
COLOR_TAG_INFO = "#38bdf8"        # Sky Blue
COLOR_TAG_MAIN = "#4ade80"        # Mint Green
COLOR_TAG_SEC = "#fbbf24"         # Amber Gold
COLOR_TAG_THIRD = "#c084fc"       # Purple/Violet
COLOR_TAG_CHAT = "#818cf8"        # Indigo
COLOR_TAG_TYPING = "#fef08a"      # Soft Yellow
COLOR_TAG_SENT = "#22c55e"        # Bright Green
COLOR_TAG_SPACING = "#fb923c"     # Orange
COLOR_TAG_ALERT = "#ef4444"       # Red
COLOR_TAG_DEFAULT = "#cbd5e1"     # Soft White/Grey


class ModernButton(tk.Label):
    """Custom flat clickable pill button with hover and active states."""
    def __init__(self, parent, text, bg, fg, hover_bg, command=None, padx=14, pady=5, font=("Helvetica", 10, "bold"), **kwargs):
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


class ModernToggle(tk.Frame):
    """Sleek toggle switch using dot indicators."""
    def __init__(self, parent, text, initial=True, active_color=COLOR_SUCCESS, command=None):
        super().__init__(parent, bg=parent["bg"])
        self.value = initial
        self.active_color = active_color
        self.cmd = command
        
        self.indicator = tk.Label(self, text="●" if initial else "○", fg=active_color if initial else COLOR_TEXT_MUTED, bg=parent["bg"], font=("Helvetica", 12, "bold"), cursor="hand2")
        self.indicator.pack(side=tk.LEFT, padx=(0, 5))
        
        self.label = tk.Label(self, text=text, fg=COLOR_TEXT_WHITE if initial else COLOR_TEXT_MUTED, bg=parent["bg"], font=("Helvetica", 10, "bold"), cursor="hand2")
        self.label.pack(side=tk.LEFT)
        
        self.indicator.bind("<Button-1>", self._toggle)
        self.label.bind("<Button-1>", self._toggle)

    def _toggle(self, e=None):
        self.value = not self.value
        self.update_display()
        if self.cmd:
            self.cmd(self.value)

    def get(self):
        return self.value

    def set(self, val):
        self.value = bool(val)
        self.update_display()

    def update_display(self):
        if self.value:
            self.indicator.configure(text="●", fg=self.active_color)
            self.label.configure(fg=COLOR_TEXT_WHITE)
        else:
            self.indicator.configure(text="○", fg=COLOR_TEXT_MUTED)
            self.label.configure(fg=COLOR_TEXT_MUTED)


class SegmentedTabs(tk.Frame):
    """Pill-style segmented tab controller."""
    def __init__(self, parent, tabs, on_tab_change):
        super().__init__(parent, bg=COLOR_BG_CARD)
        self.on_tab_change = on_tab_change
        self.active_tab = tabs[0]
        self.tab_buttons = {}
        
        bar = tk.Frame(self, bg=COLOR_BG_INPUT, padx=2, pady=2, highlightthickness=1, highlightbackground=COLOR_BORDER)
        bar.pack()
        
        for name in tabs:
            btn = tk.Label(bar, text=name, bg=COLOR_PRIMARY if name == self.active_tab else COLOR_BG_INPUT,
                           fg=COLOR_TEXT_WHITE if name == self.active_tab else COLOR_TEXT_MUTED,
                           font=("Helvetica", 10, "bold"), padx=14, pady=4, cursor="hand2")
            btn.pack(side=tk.LEFT, padx=1)
            btn.bind("<Button-1>", lambda e, n=name: self.select_tab(n))
            self.tab_buttons[name] = btn

    def select_tab(self, name):
        self.active_tab = name
        for t_name, btn in self.tab_buttons.items():
            if t_name == name:
                btn.configure(bg=COLOR_PRIMARY, fg=COLOR_TEXT_WHITE)
            else:
                btn.configure(bg=COLOR_BG_INPUT, fg=COLOR_TEXT_MUTED)
        self.on_tab_change(name)


class OwOBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("OwO Bot Dashboard")
        self.root.geometry("700x630")
        self.root.configure(bg=COLOR_BG_ROOT)
        
        self.process = None
        self.thread = None
        
        self.token_var = tk.StringVar()
        self.channel_var_1 = tk.StringVar()
        self.channel_var_2 = tk.StringVar()
        self.channel_var_3 = tk.StringVar()
        self.show_token = False
        
        self.setup_ui()
        self.load_config()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_ui(self):
        # =========================================================================
        # 1. Top Navigation Bar
        # =========================================================================
        self.nav_bar = tk.Frame(self.root, bg=COLOR_BG_HEADER, padx=16, pady=10, highlightthickness=1, highlightbackground=COLOR_BORDER)
        self.nav_bar.pack(fill=tk.X)
        
        title_box = tk.Frame(self.nav_bar, bg=COLOR_BG_HEADER)
        title_box.pack(side=tk.LEFT)
        
        tk.Label(title_box, text="OwO Automator", bg=COLOR_BG_HEADER, fg=COLOR_TEXT_WHITE, font=("Helvetica", 13, "bold")).pack(side=tk.LEFT)
        tk.Label(title_box, text=" v2.2 ", bg=COLOR_BORDER, fg=COLOR_TEXT_MUTED, font=("Helvetica", 9, "bold")).pack(side=tk.LEFT, padx=(8, 12))
        
        self.status_indicator = tk.Label(title_box, text="○ Offline", bg=COLOR_BG_HEADER, fg=COLOR_TEXT_MUTED, font=("Helvetica", 10, "bold"))
        self.status_indicator.pack(side=tk.LEFT)
        
        controls_box = tk.Frame(self.nav_bar, bg=COLOR_BG_HEADER)
        controls_box.pack(side=tk.RIGHT)
        
        self.start_btn = ModernButton(controls_box, text="Start Bot", bg=COLOR_SUCCESS, fg=COLOR_TEXT_WHITE, hover_bg=COLOR_SUCCESS_HOVER, command=self.start_bot)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 8))
        
        self.stop_btn = ModernButton(controls_box, text="Stop Bot", bg=COLOR_DANGER, fg=COLOR_TEXT_WHITE, hover_bg=COLOR_DANGER_HOVER, command=self.stop_bot)
        self.stop_btn.pack(side=tk.LEFT)
        self.stop_btn.set_state(False)

        # =========================================================================
        # 2. Main Content Container
        # =========================================================================
        self.content_frame = tk.Frame(self.root, bg=COLOR_BG_ROOT, padx=14, pady=10)
        self.content_frame.pack(fill=tk.BOTH, expand=True)

        # -------------------------------------------------------------------------
        # Card A: Authentication & Global Config Card
        # -------------------------------------------------------------------------
        self.auth_card = tk.Frame(self.content_frame, bg=COLOR_BG_CARD, padx=12, pady=10, highlightthickness=1, highlightbackground=COLOR_BORDER)
        self.auth_card.pack(fill=tk.X, pady=(0, 10))
        
        # Row 1: Auth Token
        token_row = tk.Frame(self.auth_card, bg=COLOR_BG_CARD)
        token_row.pack(fill=tk.X, pady=(0, 6))
        
        tk.Label(token_row, text="Auth Token:", font=("Helvetica", 10, "bold"), fg=COLOR_TEXT_WHITE, bg=COLOR_BG_CARD, width=11, anchor="w").pack(side=tk.LEFT)
        
        self.token_entry = tk.Entry(
            token_row,
            textvariable=self.token_var,
            font=("Consolas", 10),
            show="*",
            bg=COLOR_BG_INPUT,
            fg=COLOR_TEXT_WHITE,
            insertbackground=COLOR_PRIMARY,
            borderwidth=0,
            highlightthickness=1,
            highlightbackground=COLOR_BORDER,
            highlightcolor=COLOR_BORDER_FOCUS
        )
        self.token_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 8), ipady=3)
        
        self.show_token_btn = ModernButton(token_row, text="Show", bg=COLOR_BORDER, fg=COLOR_TEXT_WHITE, hover_bg="#3f4147", command=self.toggle_token_visibility, padx=10, pady=2, font=("Helvetica", 9, "bold"))
        self.show_token_btn.pack(side=tk.RIGHT)

        # Row 2: Options
        options_row = tk.Frame(self.auth_card, bg=COLOR_BG_CARD)
        options_row.pack(fill=tk.X)
        
        self.typing_toggle = ModernToggle(options_row, text="Simulate typing status ('User is typing...')", initial=True, active_color=COLOR_SUCCESS)
        self.typing_toggle.pack(side=tk.LEFT)

        # -------------------------------------------------------------------------
        # Card B: Multi-Loop Execution Card (Tabs + Editor)
        # -------------------------------------------------------------------------
        self.loop_card = tk.Frame(self.content_frame, bg=COLOR_BG_CARD, padx=12, pady=10, highlightthickness=1, highlightbackground=COLOR_BORDER)
        self.loop_card.pack(fill=tk.X, pady=(0, 10))
        
        # Tabs bar header
        tabs_header = tk.Frame(self.loop_card, bg=COLOR_BG_CARD)
        tabs_header.pack(fill=tk.X, pady=(0, 8))
        
        self.tabs_controller = SegmentedTabs(tabs_header, ["Main Loop", "Secondary Loop", "Third Loop"], self.switch_loop_tab)
        self.tabs_controller.pack(side=tk.LEFT)

        # Tab 1 Panel
        self.panel_1 = tk.Frame(self.loop_card, bg=COLOR_BG_CARD)
        self.loop_1_toggle = ModernToggle(self.panel_1, text="Enable Loop", initial=True, active_color=COLOR_SUCCESS)
        self.loop_1_toggle.pack(side=tk.LEFT, padx=(0, 15))
        tk.Label(self.panel_1, text="Channel ID:", bg=COLOR_BG_CARD, fg=COLOR_TEXT_WHITE, font=("Helvetica", 10, "bold")).pack(side=tk.LEFT)
        self.channel_entry_1 = tk.Entry(self.panel_1, textvariable=self.channel_var_1, font=("Consolas", 10), width=24, bg=COLOR_BG_INPUT, fg=COLOR_TEXT_WHITE, insertbackground=COLOR_PRIMARY, borderwidth=0, highlightthickness=1, highlightbackground=COLOR_BORDER, highlightcolor=COLOR_BORDER_FOCUS)
        self.channel_entry_1.pack(side=tk.LEFT, padx=(6, 0), ipady=2)
        
        # Tab 2 Panel
        self.panel_2 = tk.Frame(self.loop_card, bg=COLOR_BG_CARD)
        self.loop_2_toggle = ModernToggle(self.panel_2, text="Enable Loop", initial=True, active_color=COLOR_SUCCESS)
        self.loop_2_toggle.pack(side=tk.LEFT, padx=(0, 15))
        tk.Label(self.panel_2, text="Channel ID:", bg=COLOR_BG_CARD, fg=COLOR_TEXT_WHITE, font=("Helvetica", 10, "bold")).pack(side=tk.LEFT)
        self.channel_entry_2 = tk.Entry(self.panel_2, textvariable=self.channel_var_2, font=("Consolas", 10), width=24, bg=COLOR_BG_INPUT, fg=COLOR_TEXT_WHITE, insertbackground=COLOR_PRIMARY, borderwidth=0, highlightthickness=1, highlightbackground=COLOR_BORDER, highlightcolor=COLOR_BORDER_FOCUS)
        self.channel_entry_2.pack(side=tk.LEFT, padx=(6, 0), ipady=2)
        
        # Tab 3 Panel
        self.panel_3 = tk.Frame(self.loop_card, bg=COLOR_BG_CARD)
        self.loop_3_toggle = ModernToggle(self.panel_3, text="Enable Loop", initial=True, active_color=COLOR_SUCCESS)
        self.loop_3_toggle.pack(side=tk.LEFT, padx=(0, 15))
        tk.Label(self.panel_3, text="Channel ID:", bg=COLOR_BG_CARD, fg=COLOR_TEXT_WHITE, font=("Helvetica", 10, "bold")).pack(side=tk.LEFT)
        self.channel_entry_3 = tk.Entry(self.panel_3, textvariable=self.channel_var_3, font=("Consolas", 10), width=24, bg=COLOR_BG_INPUT, fg=COLOR_TEXT_WHITE, insertbackground=COLOR_PRIMARY, borderwidth=0, highlightthickness=1, highlightbackground=COLOR_BORDER, highlightcolor=COLOR_BORDER_FOCUS)
        self.channel_entry_3.pack(side=tk.LEFT, padx=(6, 0), ipady=2)

        # Editor Area Header
        self.editor_header_frame = tk.Frame(self.loop_card, bg=COLOR_BG_CARD)
        self.editor_header_frame.pack(fill=tk.X, pady=(4, 4))
        self.panel_1.pack(in_=self.editor_header_frame, fill=tk.X)

        # Text Script Areas
        self.script_area_1 = tk.Text(self.loop_card, height=4, font=("Menlo", 10), bg=COLOR_BG_INPUT, fg=COLOR_TEXT_WHITE, insertbackground=COLOR_PRIMARY, borderwidth=0, highlightthickness=1, highlightbackground=COLOR_BORDER, highlightcolor=COLOR_BORDER_FOCUS, padx=8, pady=6)
        self.script_area_2 = tk.Text(self.loop_card, height=4, font=("Menlo", 10), bg=COLOR_BG_INPUT, fg=COLOR_TEXT_WHITE, insertbackground=COLOR_PRIMARY, borderwidth=0, highlightthickness=1, highlightbackground=COLOR_BORDER, highlightcolor=COLOR_BORDER_FOCUS, padx=8, pady=6)
        self.script_area_3 = tk.Text(self.loop_card, height=4, font=("Menlo", 10), bg=COLOR_BG_INPUT, fg=COLOR_TEXT_WHITE, insertbackground=COLOR_PRIMARY, borderwidth=0, highlightthickness=1, highlightbackground=COLOR_BORDER, highlightcolor=COLOR_BORDER_FOCUS, padx=8, pady=6)

        self.script_area_1.pack(fill=tk.BOTH, expand=True)

        # -------------------------------------------------------------------------
        # Card C: Live Terminal Output Card
        # -------------------------------------------------------------------------
        self.log_card = tk.Frame(self.content_frame, bg=COLOR_BG_INPUT, highlightthickness=1, highlightbackground=COLOR_BORDER)
        self.log_card.pack(fill=tk.BOTH, expand=True)
        
        log_header = tk.Frame(self.log_card, bg=COLOR_BG_HEADER, padx=10, pady=4)
        log_header.pack(fill=tk.X)
        
        tk.Label(log_header, text="Live Console Output", bg=COLOR_BG_HEADER, fg=COLOR_TEXT_MUTED, font=("Helvetica", 9, "bold")).pack(side=tk.LEFT)
        
        clear_btn = ModernButton(log_header, text="Clear", bg=COLOR_BORDER, fg=COLOR_TEXT_MUTED, hover_bg="#3f4147", command=self.clear_log, padx=8, pady=1, font=("Helvetica", 8, "bold"))
        clear_btn.pack(side=tk.RIGHT)
        
        self.log_area = tk.Text(
            self.log_card,
            wrap=tk.WORD,
            font=("Menlo", 10),
            bg=COLOR_BG_INPUT,
            fg=COLOR_TAG_DEFAULT,
            borderwidth=0,
            highlightthickness=0,
            padx=10,
            pady=8
        )
        self.log_area.pack(expand=True, fill=tk.BOTH)
        
        # Configure syntax tags
        self.log_area.tag_config("info", foreground=COLOR_TAG_INFO)
        self.log_area.tag_config("main", foreground=COLOR_TAG_MAIN)
        self.log_area.tag_config("sec", foreground=COLOR_TAG_SEC)
        self.log_area.tag_config("third", foreground=COLOR_TAG_THIRD)
        self.log_area.tag_config("chat", foreground=COLOR_TAG_CHAT)
        self.log_area.tag_config("typing", foreground=COLOR_TAG_TYPING)
        self.log_area.tag_config("sent", foreground=COLOR_TAG_SENT)
        self.log_area.tag_config("spacing", foreground=COLOR_TAG_SPACING)
        self.log_area.tag_config("alert", foreground=COLOR_TAG_ALERT)
        self.log_area.tag_config("muted", foreground=COLOR_TEXT_MUTED)
        
        self.log("[System] OwO Automator initialized. Configure settings and click 'Start Bot'.\n")

    def switch_loop_tab(self, tab_name):
        self.panel_1.pack_forget()
        self.panel_2.pack_forget()
        self.panel_3.pack_forget()
        self.script_area_1.pack_forget()
        self.script_area_2.pack_forget()
        self.script_area_3.pack_forget()

        if tab_name == "Main Loop":
            self.panel_1.pack(in_=self.editor_header_frame, fill=tk.X)
            self.script_area_1.pack(fill=tk.BOTH, expand=True)
        elif tab_name == "Secondary Loop":
            self.panel_2.pack(in_=self.editor_header_frame, fill=tk.X)
            self.script_area_2.pack(fill=tk.BOTH, expand=True)
        elif tab_name == "Third Loop":
            self.panel_3.pack(in_=self.editor_header_frame, fill=tk.X)
            self.script_area_3.pack(fill=tk.BOTH, expand=True)

    def toggle_token_visibility(self):
        self.show_token = not self.show_token
        if self.show_token:
            self.token_entry.config(show="")
            self.show_token_btn.configure(text="Hide")
        else:
            self.token_entry.config(show="*")
            self.show_token_btn.configure(text="Show")

    def clear_log(self):
        self.log_area.configure(state='normal')
        self.log_area.delete("1.0", tk.END)
        self.log_area.configure(state='disabled')

    def log(self, text):
        self.log_area.configure(state='normal')
        for line in text.splitlines(keepends=True):
            tags = []
            if "[CRITICAL ALERT]" in line or "CAPTCHA" in line or "[Error]" in line:
                tags.append("alert")
            elif "[Main Loop]" in line:
                tags.append("main")
            elif "[Secondary Loop]" in line:
                tags.append("sec")
            elif "[Third Loop]" in line:
                tags.append("third")
            elif "[INFO]" in line or "[System]" in line:
                tags.append("info")
            elif "[CHAT" in line:
                tags.append("chat")
            elif "Typing" in line:
                tags.append("typing")
            elif "Sent:" in line:
                tags.append("sent")
            elif "Spacing" in line:
                tags.append("spacing")
            
            self.log_area.insert(tk.END, line, tuple(tags))
        self.log_area.see(tk.END)
        self.log_area.configure(state='disabled')

    def load_config(self):
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
                
                self.typing_toggle.set(bool(conf.get("simulate_typing", True)))
                self.loop_1_toggle.set(bool(conf.get("loop_1_enabled", True)))
                self.loop_2_toggle.set(bool(conf.get("loop_2_enabled", True)))
                self.loop_3_toggle.set(bool(conf.get("loop_3_enabled", True)))
                
                initial_script_1 = conf.get("owo_script", initial_script_1)
                initial_script_2 = conf.get("owo_script_2", initial_script_2)
                initial_script_3 = conf.get("owo_script_3", initial_script_3)
        except Exception:
            pass
            
        self.script_area_1.insert(tk.END, initial_script_1)
        self.script_area_2.insert(tk.END, initial_script_2)
        self.script_area_3.insert(tk.END, initial_script_3)

    def read_output(self):
        while self.process and self.process.poll() is None:
            line = self.process.stdout.readline()
            if line:
                self.root.after(0, self.log, line)
        if self.process:
            self.root.after(0, self.handle_process_exit)

    def handle_process_exit(self):
        self.log("\n[System] Bot stopped running.\n")
        self.status_indicator.configure(text="○ Offline", fg=COLOR_TEXT_MUTED)
        self.start_btn.set_state(True)
        self.stop_btn.set_state(False)
        self.process = None

    def start_bot(self):
        if self.process is None:
            selected_token = self.token_var.get().strip()
            ch1 = self.channel_var_1.get().strip()
            ch2 = self.channel_var_2.get().strip()
            ch3 = self.channel_var_3.get().strip()
            
            if not selected_token:
                self.log("\n[Error] Please enter your Authorization Token before starting.\n")
                return
                
            en1 = self.loop_1_toggle.get()
            en2 = self.loop_2_toggle.get()
            en3 = self.loop_3_toggle.get()

            if not en1 and not en2 and not en3:
                self.log("\n[Error] Please enable at least one loop before starting.\n")
                return

            if en1 and not ch1:
                self.log("\n[Error] Main Loop is enabled but Channel ID is empty.\n")
                return
            if en2 and not ch2:
                self.log("\n[Error] Secondary Loop is enabled but Channel ID is empty.\n")
                return
            if en3 and not ch3:
                self.log("\n[Error] Third Loop is enabled but Channel ID is empty.\n")
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
                conf["simulate_typing"] = self.typing_toggle.get()
                conf["loop_1_enabled"] = en1
                conf["loop_2_enabled"] = en2
                conf["loop_3_enabled"] = en3
                with open(CONFIG_FILE, "w") as f:
                    json.dump(conf, f, indent=3)
                self.log(f"[System] Configuration saved.\n")
            except Exception as e:
                self.log(f"[Error] Could not save config: {e}\n")

            self.log("[System] Launching bot worker...\n")
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
            
            self.status_indicator.configure(text="● Running", fg=COLOR_SUCCESS)
            self.start_btn.set_state(False)
            self.stop_btn.set_state(True)
            
            self.thread = threading.Thread(target=self.read_output, daemon=True)
            self.thread.start()

    def stop_bot(self):
        if self.process:
            self.log("[System] Stopping bot worker...\n")
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
