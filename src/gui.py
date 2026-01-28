import tkinter as tk
from tkinter import ttk, filedialog, simpledialog
import threading
import keyboard
from pynput import keyboard as pynput_keyboard
from pynput import mouse as pynput_mouse
from tkinter import messagebox
import sys
import ctypes
import mss
import numpy as np
import win32api
import win32con
import json
import os
import time
from datetime import datetime
                                                          

try:
    from PIL import Image, ImageDraw, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

                          
try:
    from src.themes import ThemeManager
    from src.fishing import FishingBot
    from src.layout_manager import LayoutManager
except ImportError:
    from themes import ThemeManager
    from fishing import FishingBot
    from layout_manager import LayoutManager

class ToolTip:
    """Simple tooltip class for hover explanations"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.on_enter)
        self.widget.bind("<Leave>", self.on_leave)
    
    def on_enter(self, event=None):
        if self.tooltip_window or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + 20
        
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_attributes('-topmost', True)                                
        tw.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(tw, text=self.text, justify='left',
                        background="#ffffe0", relief='solid', borderwidth=1,
                        font=("Arial", 9), wraplength=300, padx=5, pady=3)
        label.pack()
    
    def on_leave(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

class CollapsibleFrame:
    """Modern collapsible frame widget with sleek styling"""
    def __init__(self, parent, title, row, columnspan=4):
        self.parent = parent
        self.title = title
        self.row = row
        self.columnspan = columnspan
        self.is_expanded = True
        
                                            
        self.container = ttk.Frame(parent)
        self.container.grid(row=row, column=0, columnspan=columnspan, sticky='ew', pady=(8, 0), padx=10)
        
                                                       
        self.header_frame = ttk.Frame(self.container)
        self.header_frame.pack(fill='x', pady=(0, 2))
        self.header_frame.columnconfigure(0, weight=1)                     
        
                                                                                         
        self.title_label = ttk.Label(self.header_frame, text=title, 
                                   style='SectionTitle.TLabel')
        self.title_label.grid(row=0, column=0, sticky='w', padx=(10, 0), pady=5)
        
                                                
        self.toggle_btn = ttk.Button(self.header_frame, text='−', width=3, 
                                   command=self.toggle, style='TButton')
        self.toggle_btn.grid(row=0, column=1, sticky='e', padx=(0, 10), pady=2)
        
                                              
        separator = ttk.Frame(self.container, height=1)
        separator.pack(fill='x', pady=(0, 8))
        
                                    
        self.content_frame = ttk.Frame(self.container)
        self.content_frame.pack(fill='both', expand=True, padx=15, pady=(0, 10))
        
                                                      
        parent.grid_rowconfigure(row, weight=0)
        self.container.columnconfigure(0, weight=1)
        
    def toggle(self):
        """Toggle the visibility of the content frame with smooth animation"""
        if self.is_expanded:
            self.content_frame.pack_forget()
            self.toggle_btn.config(text='+')
            self.is_expanded = False
        else:
            self.content_frame.pack(fill='both', expand=True, padx=15, pady=(0, 10))
            self.toggle_btn.config(text='−')
            self.is_expanded = True
    
    def get_content_frame(self):
        """Return the content frame for adding widgets"""
        return self.content_frame

class HotkeyGUI:
    def __init__(self, root):
        self.root = root
        self.root.title('GPO Autofish v3.0')
        self.root.attributes('-topmost', True)
        
                         
        try:
            if PIL_AVAILABLE and os.path.exists("images/icon.webp"):
                icon_image = Image.open("images/icon.webp")
                icon_image = icon_image.resize((32, 32), Image.Resampling.LANCZOS)
                icon_photo = ImageTk.PhotoImage(icon_image)
                self.root.iconphoto(True, icon_photo)
        except Exception as e:
            print(f"Could not set window icon: {e}")
        
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_loop_active = False

        self.main_loop_thread = None
        self.recording_hotkey = None

        self.real_area = None
        self.is_clicking = False
        self.kp = 0.1
        self.kd = 0.5
        self.previous_error = 0
        self.scan_timeout = 15.0
        self.wait_after_loss = 1.0
        self.dpi_scale = self.get_dpi_scale()

        self.hotkeys = {'toggle_loop': 'f1', 'toggle_layout': 'f2', 'exit': 'f3', 'toggle_minimize': 'f4'}
        print(f"🔧 Hotkeys initialized: {self.hotkeys}")
        self.purchase_counter = 0
        self.purchase_delay_after_key = 2.0
        self.purchase_click_delay = 1.0
        self.purchase_after_type_delay = 1.0
        self.fish_count = 0                                     
        self.devil_fruits_caught = []                                   
        self.bait_purchased = 0                                          
        
                                  
        self.webhook_url = ""
        self.webhook_enabled = False
        self.webhook_interval = 10                              
        self.webhook_counter = 0                           
        
                                               
        self.fish_progress_webhook_enabled = True
        self.devil_fruit_webhook_enabled = True
        self.fruit_spawn_webhook_enabled = True
        self.purchase_webhook_enabled = True
        self.recovery_webhook_enabled = True
        self.bait_webhook_enabled = True
        
                                         
        self.auto_bait_enabled = False
        self.top_bait_coords = None
        self.top_bait_coords_2 = None                     
        
                                
        self.fruit_storage_enabled = False
        self.fruit_storage_key = '2'                           
        self.fruit_storage_key_2 = '3'                            
        self.rod_key = '1'                   
        self.fruit_coords = {}                                          
        
                                                                 
        self.update_manager = None
        
                              
        self.silent_mode = False                          
        self.verbose_logging = False                                  
        
                                                       
        self.last_activity_time = time.time()
        self.last_fish_time = time.time()
        self.recovery_enabled = True
        self.smart_check_interval = 15.0                          
        self.last_smart_check = time.time()
        self.recovery_count = 0
        self.last_recovery_time = 0
        
                                                    
        self.current_state = "idle"                                                                      
        self.state_start_time = time.time()
        self.state_details = {}                               
        self.stuck_actions = []                                    
        
                                                 
        self.max_state_duration = {
            "fishing": 50.0,                                                
            "purchasing": 60.0,                             
            "casting": 15.0,                      
            "menu_opening": 10.0,                               
            "typing": 8.0,                                  
            "clicking": 5.0,                           
            "idle": 45.0,                           
            "initial_setup": 120.0                                             
        }
        
                          
        self.dev_mode = False                                        
        
                                                 
        self._loading_settings = True
        
                          
        self.start_time = None
        self.pause_time = None
        self.total_paused_time = 0
        self.is_paused = False
        
                                                     
        import sys
        if 'pythonw' in sys.executable.lower():
            self.silent_mode = True
        
                            
        self.dark_theme = True                         
        self.current_theme = "red"                            

        self.collapsible_sections = {}
        self.theme_window = None
        
                                                                               
        self.amount_var = None
        self.loops_var = None
        self.auto_purchase_var = None
        self.auto_purchase_amount = 100
        self.loops_per_purchase = 1
        
                                  
        self.theme_manager = ThemeManager(self)
        
                                   
        self.layout_manager = LayoutManager(self)
        
                                    
        try:
            from src.webhook import WebhookManager
        except ImportError:
            from webhook import WebhookManager
        self.webhook_manager = WebhookManager(self)
        
                                    
        try:
            from src.overlay import OverlayManager
        except ImportError:
            from overlay import OverlayManager
        self.overlay_manager = OverlayManager(self)
        
                                
        try:
            from src.ocr_manager import OCRManager
        except ImportError:
            from ocr_manager import OCRManager
        self.ocr_manager = OCRManager(self)                      
        
                                                                                 
        self.ocr_performance_mode = "fast"
        if hasattr(self.ocr_manager, 'set_performance_mode'):
            self.ocr_manager.set_performance_mode(self.ocr_performance_mode)
        
                                    
        try:
            from src.zoom_controller import ZoomController
        except ImportError:
            from zoom_controller import ZoomController
        self.zoom_controller = ZoomController(self)
        
                                 
        try:
            from src.bait_manager import BaitManager
        except ImportError:
            from bait_manager import BaitManager
        self.bait_manager = BaitManager(self)
        
                                
        self.fishing_bot = FishingBot(self)
        
                           
        self.presets_dir = "presets"
        if not os.path.exists(self.presets_dir):
            os.makedirs(self.presets_dir)
        
                                                     
        self.load_basic_settings()
        
        self.create_widgets()
        
                                                             
        self.load_ui_settings()
        
                                                              
        self.refresh_button_labels()
        
                                               
        self.setup_console_redirect()
        
        self.apply_theme()
        self.register_hotkeys()
        
                                                   
        self.schedule_periodic_update()
        
                                                       
        window_width = getattr(self, 'window_width', 800)
        window_height = getattr(self, 'window_height', 700)
        self.root.geometry(f'{window_width}x{window_height}')
        self.root.resizable(True, True)
        self.root.update_idletasks()
        self.root.minsize(600, 650)                            
        
                                               
        self.root.bind('<Configure>', self.on_window_resize)
        

        
                                                     
        try:
            try:
                from src.updater import UpdateManager
            except ImportError:
                from updater import UpdateManager
            self.update_manager = UpdateManager(self)
            print("✅ Simple UpdateManager initialized")
        except Exception as e:
            print(f"❌ Failed to initialize UpdateManager: {e}")
            self.update_manager = None
    
    def create_scrollable_frame(self):
        """Create a modern scrollable frame using tkinter Canvas and Scrollbar"""
                               
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
                                                             
        theme_colors = self.theme_manager.themes[self.current_theme]["colors"]
        self.canvas = tk.Canvas(self.main_container, highlightthickness=0, bg=theme_colors["bg"])
        self.scrollbar = ttk.Scrollbar(self.main_container, orient="vertical", command=self.canvas.yview)
        
                                     
        self.main_frame = ttk.Frame(self.canvas, padding='10')
        
                             
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
                                   
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
                                 
        self.canvas_window = self.canvas.create_window((0, 0), window=self.main_frame, anchor="nw")
        
                                          
        self.main_frame.bind('<Configure>', self._on_frame_configure)
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
    def _on_frame_configure(self, event):
        """Reset the scroll region to encompass the inner frame"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
                                                            
        self._update_scrollbar_visibility()
        
    def _on_canvas_configure(self, event):
        """Configure the canvas window to match the canvas width"""
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)
                                      
        self._update_scrollbar_visibility()
    
    def _update_scrollbar_visibility(self):
        """Show or hide scrollbar based on content size"""
        try:
                                       
            bbox = self.canvas.bbox("all")
            if bbox:
                content_height = bbox[3] - bbox[1]
                canvas_height = self.canvas.winfo_height()
                
                                                                      
                if content_height > canvas_height:
                    self.scrollbar.pack(side="right", fill="y")
                else:
                    self.scrollbar.pack_forget()
        except:
            pass
        
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def log(self, message, level="info"):
        """Smart logging that respects silent mode"""
        if self.silent_mode and level == "verbose":
            return
        if not self.silent_mode or level in ["error", "important"]:
            print(message)

    def get_dpi_scale(self):
        """Get the DPI scaling factor for the current display"""            
        try:
            dpi = self.root.winfo_fpixels('1i')
            scale = dpi / 96.0
            return scale
        except:
            return 1.0

    def _safe_get_int(self, var, default=0):
        """Safely get integer value from Tkinter variable, handling empty strings"""
        try:
            return var.get()
        except (tk.TclError, ValueError, AttributeError):
            return default

    def create_widgets(self):
                                                          
        self.create_scrollable_frame()
        self.main_frame.columnconfigure(0, weight=1)
        
        current_row = 0
        
                                                      
        header_frame = ttk.Frame(self.main_frame)
        header_frame.grid(row=current_row, column=0, sticky='ew', pady=(0, 15))
        header_frame.columnconfigure(0, weight=1)
        
                         
        try:
            if PIL_AVAILABLE and os.path.exists("images/icon.webp"):
                logo_image = Image.open("images/icon.webp")
                logo_image = logo_image.resize((48, 48), Image.Resampling.LANCZOS)
                logo_photo = ImageTk.PhotoImage(logo_image)
                logo_label = ttk.Label(header_frame, image=logo_photo)
                logo_label.image = logo_photo
                logo_label.grid(row=0, column=0, pady=(0, 8))
        except Exception as e:
            print(f"Could not load header logo: {e}")
        
                                 
        title_container = ttk.Frame(header_frame)
        title_container.grid(row=1, column=0)
        
        title = ttk.Label(title_container, text='GPO Autofish', style='Title.TLabel')
        title.pack(side=tk.LEFT, padx=(0, 10))
        
                  
        v3_badge = ttk.Label(title_container, text='v3.0', 
                            style='Badge.TLabel')
        v3_badge.pack(side=tk.LEFT)
        
                  
        credits = ttk.Label(header_frame, text='By Ariel', 
                           style='Subtitle.TLabel')
        credits.grid(row=2, column=0, pady=(5, 10))
        
                              
        toolbar = ttk.Frame(header_frame)
        toolbar.grid(row=3, column=0, pady=(10, 0))
        
        self.settings_btn = ttk.Button(toolbar, text='⚙️ Settings', 
                                      command=self.open_settings_window, style='TButton')
        self.settings_btn.pack(side=tk.LEFT, padx=5)
        ToolTip(self.settings_btn, "Open timing and advanced settings")
        
        self.update_btn = ttk.Button(toolbar, text='🔄 Update', 
                                    command=self.check_for_updates, style='TButton')
        self.update_btn.pack(side=tk.LEFT, padx=5)
        ToolTip(self.update_btn, "Check for and install updates")
        
        self.themes_btn = ttk.Button(toolbar, text='🎨 Themes', 
                                     command=self.open_theme_window, style='TButton')
        self.themes_btn.pack(side=tk.LEFT, padx=5)
        ToolTip(self.themes_btn, "Customize appearance themes")
        
        current_row += 1
        
                                                       
        status_bar = ttk.Frame(self.main_frame)
        status_bar.grid(row=current_row, column=0, sticky='ew', pady=(0, 15))
        status_bar.columnconfigure((0, 1), weight=1)
        
                                             
        self.loop_status = ttk.Label(status_bar, text='● Main Loop: OFF', style='StatusOff.TLabel')
        self.loop_status.grid(row=0, column=0, padx=5, pady=5)
        
        self.overlay_status = ttk.Label(status_bar, text='● Overlay: OFF', style='StatusOff.TLabel')
        self.overlay_status.grid(row=0, column=1, padx=5, pady=5)
        
        current_row += 1
        
                                                             
                                                      
        self.main_frame.rowconfigure(current_row, weight=1)
        self.create_modern_tabs(current_row)
        current_row += 1
        
                                            
        self.create_footer(current_row)
        current_row += 1
    
    def create_modern_tabs(self, row):
        """Create modern tabbed interface with responsive buttons"""
                                    
        tab_container = ttk.Frame(self.main_frame)
        tab_container.grid(row=row, column=0, sticky='nsew', pady=(0, 0), padx=10)
        tab_container.columnconfigure(0, weight=1)
        tab_container.rowconfigure(0, weight=0)
        tab_container.rowconfigure(1, weight=1)
        
                                                                      
        self.tab_buttons_frame = ttk.Frame(tab_container)
        self.tab_buttons_frame.grid(row=0, column=0, sticky='ew')
        
                                             
        self.tab_buttons_frame.columnconfigure(0, weight=1, uniform='tabs')
        self.tab_buttons_frame.columnconfigure(1, weight=1, uniform='tabs')
        self.tab_buttons_frame.columnconfigure(2, weight=1, uniform='tabs')
        
                                      
        self.tab_content_frame = ttk.Frame(tab_container)
        self.tab_content_frame.grid(row=1, column=0, sticky='nsew')
        self.tab_content_frame.columnconfigure(0, weight=1)
        self.tab_content_frame.rowconfigure(0, weight=1)
        
                           
        self.overview_tab = ttk.Frame(self.tab_content_frame)
        self.setup_tab = ttk.Frame(self.tab_content_frame)
        self.features_tab = ttk.Frame(self.tab_content_frame)
        
                            
        self.tab_buttons = {}
        self.active_tab = None
        
        tab_names = ['Overview', 'Setup', 'Features']
        tab_frames = [self.overview_tab, self.setup_tab, self.features_tab]
        
        for i, (name, frame) in enumerate(zip(tab_names, tab_frames)):
            btn = ttk.Button(self.tab_buttons_frame, text=name, 
                           command=lambda f=frame, n=name: self.switch_tab(f, n),
                           style='Tab.TButton')
            btn.grid(row=0, column=i, sticky='ew', padx=1, pady=1)
            self.tab_buttons[name] = btn
        
                       
        self.create_overview_tab()
        self.create_setup_tab()
        self.create_features_tab()
        
                        
        self.switch_tab(self.overview_tab, 'Overview')
    
    def switch_tab(self, frame, name):
        """Switch to a different tab"""
                       
        for tab in [self.overview_tab, self.setup_tab, self.features_tab]:
            tab.grid_remove()
        
                           
        frame.grid(row=0, column=0, sticky='nsew')
        self.active_tab = name
        
                              
        theme_colors = self.theme_manager.themes[self.current_theme]["colors"]
        for btn_name, btn in self.tab_buttons.items():
            if btn_name == name:
                btn.configure(style='TabActive.TButton')
            else:
                btn.configure(style='Tab.TButton')
    
    def create_overview_tab(self):
        """Overview tab with dashboard and controls"""
                                                    
        canvas = tk.Canvas(self.overview_tab, highlightthickness=0, height=500)
        scrollbar = ttk.Scrollbar(self.overview_tab, orient="vertical", command=canvas.yview)
        content = ttk.Frame(canvas, padding=20)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas_window = canvas.create_window((0, 0), window=content, anchor="nw")
        
        content.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(canvas_window, width=e.width))
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        
        content.columnconfigure(0, weight=1)
        
                              
        control_section = ttk.LabelFrame(content, text="🎮 Quick Controls", padding=15)
        control_section.grid(row=0, column=0, sticky='ew', pady=(0, 15))
        control_section.columnconfigure(0, weight=1)
        
                               
        self.start_stop_btn = ttk.Button(control_section, text='▶️ START FISHING', 
                                        command=self.toggle_main_loop, 
                                        style='Accent.TButton')
        self.start_stop_btn.grid(row=0, column=0, sticky='ew', pady=(0, 15))
        
                            
        reminder = ttk.Label(control_section, 
                            text='⚠️ Make sure Roblox is focused when you press START or F1!',
                            style='StatusOff.TLabel',
                            anchor='center')
        reminder.grid(row=1, column=0, pady=(0, 15))
        
                                         
        keybind_frame = ttk.Frame(control_section)
        keybind_frame.grid(row=2, column=0, sticky='ew')
        keybind_frame.columnconfigure((0, 1), weight=1)
        
                            
        left_keys = ttk.Frame(keybind_frame)
        left_keys.grid(row=0, column=0, sticky='ew', padx=(0, 5))
        
        ttk.Label(left_keys, text='⌨️ Hotkeys:', style='SectionTitle.TLabel').pack(anchor='w', pady=(0, 5))
        ttk.Label(left_keys, text='F1 - Start/Stop Fishing', style='Description.TLabel').pack(anchor='w', pady=2)
        ttk.Label(left_keys, text='F2 - Toggle Overlay', style='Description.TLabel').pack(anchor='w', pady=2)
        
                             
        right_keys = ttk.Frame(keybind_frame)
        right_keys.grid(row=0, column=1, sticky='ew', padx=(5, 0))
        
        ttk.Label(right_keys, text='', style='SectionTitle.TLabel').pack(anchor='w', pady=(0, 5))           
        ttk.Label(right_keys, text='F3 - Emergency Exit', style='Description.TLabel').pack(anchor='w', pady=2)
        ttk.Label(right_keys, text='F4 - Minimize Window', style='Description.TLabel').pack(anchor='w', pady=2)
        
                         
        stats_section = ttk.LabelFrame(content, text="📈 Statistics", padding=15)
        stats_section.grid(row=1, column=0, sticky='ew', pady=(0, 15))
        stats_section.columnconfigure((0, 1), weight=1)
        
                    
        self.total_fish_stat = ttk.Label(stats_section, text='Total Fish Caught\n0', 
                                        style='StatCard.TLabel', anchor='center')
        self.total_fish_stat.grid(row=0, column=0, sticky='ew', padx=5, pady=5)
        
        self.fruits_caught_stat = ttk.Label(stats_section, text='Devil Fruits Found\n0', 
                                           style='StatCard.TLabel', anchor='center')
        self.fruits_caught_stat.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        
        self.session_time_stat = ttk.Label(stats_section, text='Session Time\n00:00:00', 
                                          style='StatCard.TLabel', anchor='center')
        self.session_time_stat.grid(row=1, column=0, sticky='ew', padx=5, pady=5)
        
        self.bait_used_stat = ttk.Label(stats_section, text='Bait Purchased\n0', 
                                       style='StatCard.TLabel', anchor='center')
        self.bait_used_stat.grid(row=1, column=1, sticky='ew', padx=5, pady=5)
        
                       
        activity_section = ttk.LabelFrame(content, text="�️ Developer Log", padding=15)
        activity_section.grid(row=2, column=0, sticky='ew', pady=(0, 15))
        
                                 
        activity_header = ttk.Frame(activity_section)
        activity_header.pack(fill='x', pady=(0, 5))
        
        ttk.Label(activity_header, text="Dev Log - All Console Output", 
                 font=('Segoe UI', 9, 'bold')).pack(side='left')
        
                          
        self.copy_logs_btn = ttk.Button(activity_header, text="📋", width=3,
                                       command=self.copy_activity_logs)
        self.copy_logs_btn.pack(side='right')
        ToolTip(self.copy_logs_btn, "Copy all dev logs to clipboard")
        
                                     
        activity_frame = ttk.Frame(activity_section)
        activity_frame.pack(fill='both', expand=True)
        
        activity_scroll = ttk.Scrollbar(activity_frame)
        activity_scroll.pack(side='right', fill='y')
        
        self.activity_log = tk.Text(activity_frame, height=8, wrap='word',
                                    yscrollcommand=activity_scroll.set,
                                    font=('Consolas', 9),
                                    relief='solid', borderwidth=1,
                                    padx=5, pady=5)
        self.activity_log.pack(side='left', fill='both', expand=True)
        activity_scroll.config(command=self.activity_log.yview)
        
                                                  
        self.activity_log.tag_config('timestamp', foreground='#888888', font=('Consolas', 8))
        self.activity_log.tag_config('info', foreground='#2196F3')
        self.activity_log.tag_config('success', foreground='#4CAF50')
        self.activity_log.tag_config('warning', foreground='#FF9800')
        self.activity_log.tag_config('error', foreground='#F44336')
        
                         
        self.add_activity("🎣 Bot ready! Click START to begin fishing.")
        self.add_activity("📝 All system events will be logged here.")    
    def create_setup_tab(self):
        """Setup tab with step-by-step wizard"""
                          
        canvas = tk.Canvas(self.setup_tab, highlightthickness=0, height=500)
        scrollbar = ttk.Scrollbar(self.setup_tab, orient="vertical", command=canvas.yview)
        content = ttk.Frame(canvas, padding=20)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas_window = canvas.create_window((0, 0), window=content, anchor="nw")
        
        content.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(canvas_window, width=e.width))
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        
        content.columnconfigure(0, weight=1)
        
                               
        step1 = ttk.LabelFrame(content, text="Step 1: Set Cast Location", padding=15)
        step1.grid(row=0, column=0, sticky='ew', pady=(0, 15))
        
        ttk.Label(step1, text="Click the button then click where you want to cast your rod",
                 style='Description.TLabel').pack(anchor='w', pady=(0, 10))
        
                                                   
        if not hasattr(self, 'fishing_location'):
            self.fishing_location = None
        
                                                      
        cast_btn_text = f'🎯 Cast Location: {self.fishing_location}' if self.fishing_location else '🎯 Set Cast Location'
        self.fishing_location_btn = ttk.Button(step1, text=cast_btn_text, 
                                              command=lambda: self.capture_mouse_click('fishing_location'),
                                              style='Accent.TButton')
        self.fishing_location_btn.pack(fill='x', pady=5)
        
                                          
        status_text = f'✅ Set: {self.fishing_location}' if self.fishing_location else '❌ Not Set'
        status_style = 'StatusOn.TLabel' if self.fishing_location else 'StatusOff.TLabel'
        self.fishing_location_status = ttk.Label(step1, text=status_text, style=status_style)
        self.fishing_location_status.pack(anchor='w', pady=5)
        
                              
        step2 = ttk.LabelFrame(content, text="Step 2: Configure Layouts", padding=15)
        step2.grid(row=1, column=0, sticky='ew', pady=(0, 15))
        
        ttk.Label(step2, text="Position overlays over fishing bar and loot drops",
                 style='Description.TLabel').pack(anchor='w', pady=(0, 15))
        
                                                 
        steps = [
            ("1", "Press F2", "Open overlay editor to position detection areas"),
            ("2", "Align Layouts", "Position Bar Layout (blue) and Drop Layout (green) overlays"),
            ("3", "Close F2", "Press F2 again to save and exit overlay editor")
        ]
        
        for number, title, description in steps:
                                     
            step_container = ttk.Frame(step2)
            step_container.pack(fill='x', pady=5)
            
                            
            header = ttk.Frame(step_container)
            header.pack(fill='x')
            
            ttk.Label(header, text=f"{number}.", 
                     style='Subtitle.TLabel', font=('Segoe UI', 10, 'bold')).pack(side='left', padx=(0, 5))
            
            ttk.Label(header, text=title, 
                     style='Subtitle.TLabel', font=('Segoe UI', 10, 'bold')).pack(side='left')
            
                         
            ttk.Label(step_container, text=description,
                     style='Description.TLabel', font=('Segoe UI', 9)).pack(anchor='w', padx=(20, 0))
        
                              
        warning_frame = ttk.Frame(step2)
        warning_frame.pack(fill='x', pady=(15, 0))
        
        ttk.Label(warning_frame, text="⚠️ IMPORTANT WARNING:",
                 foreground='#ff4444', font=('Segoe UI', 9, 'bold')).pack(anchor='w')
        
        ttk.Label(warning_frame, text="• DO NOT start the macro while F2 overlay editor is active!",
                 foreground='#ff6666', font=('Segoe UI', 9)).pack(anchor='w', padx=(20, 0), pady=(3, 0))
        
        ttk.Label(warning_frame, text="• Always close F2 first to save your layout positions",
                 foreground='#ff6666', font=('Segoe UI', 9)).pack(anchor='w', padx=(20, 0), pady=(2, 0))
        
                            
        step3 = ttk.LabelFrame(content, text="Step 3: Auto-Setup Options", padding=15)
        step3.grid(row=2, column=0, sticky='ew', pady=(0, 15))
        
        self.create_compact_startup_section(step3)
        
                            
        step4 = ttk.LabelFrame(content, text="Step 4: Test Your Setup", padding=15)
        step4.grid(row=3, column=0, sticky='ew', pady=(0, 15))
        
        ttk.Label(step4, text="Run a quick test to verify everything works",
                 style='Description.TLabel').pack(anchor='w', pady=(0, 10))
        
        ttk.Button(step4, text='✓ Test Fishing', 
                  command=self.test_setup,
                  style='TButton').pack(fill='x', pady=5)
        
                     
        guide = ttk.LabelFrame(content, text="📖 Setup Guide", padding=15)
        guide.grid(row=4, column=0, sticky='ew', pady=(0, 15))
        
        guide_text = """Quick Setup Guide:

1. Set your fishing location (where to cast)
2. Position the blue bar overlay over fishing bar (Press F2 to toggle)
3. Position the drop overlay over loot notification area
4. Enable auto-setup features if desired
5. Make sure Roblox window is FOCUSED
6. Press F1 or click START in Overview tab!

Important: The bot needs Roblox to be the active window when you start!

Tip: Use F2 to quickly toggle overlays while positioning them."""
        
        ttk.Label(guide, text=guide_text, style='Description.TLabel', 
                 justify='left').pack(anchor='w')
    
    def create_features_tab(self):
        """Features tab with all bot features"""
                          
        canvas = tk.Canvas(self.features_tab, highlightthickness=0, height=500)
        scrollbar = ttk.Scrollbar(self.features_tab, orient="vertical", command=canvas.yview)
        content = ttk.Frame(canvas, padding=20)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas_window = canvas.create_window((0, 0), window=content, anchor="nw")
        
        content.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(canvas_window, width=e.width))
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        
        content.columnconfigure(0, weight=1)
        
                           
        self.create_auto_bait_feature_card(content, 0)
        
                               
        self.create_fruit_storage_feature_card(content, 1)
        
                               
        self.create_auto_purchase_feature_card(content, 2)
        
                                 
        self.create_webhook_feature_card(content, 3)
    
                                                                                                  
    
    def create_footer(self, row):
        """Create footer with Discord and status"""
        footer = ttk.Frame(self.main_frame)
        footer.grid(row=row, column=0, sticky='ew', pady=(15, 10), padx=10)
        footer.columnconfigure(0, weight=1)
        
                                           
        discord_frame = ttk.LabelFrame(footer, text="💬 Community & Support", padding=15)
        discord_frame.pack(fill='x', pady=(0, 10))
        discord_frame.columnconfigure(0, weight=1)
        
        ttk.Label(discord_frame, text='Join our Discord server for help, updates, and community support!', 
                 style='Description.TLabel',
                 anchor='center').grid(row=0, column=0, pady=(0, 10))
        
        discord_btn = ttk.Button(discord_frame, text='🌐 Join Discord Server', 
                               command=lambda: self.open_discord_link('https://discord.gg/unPZxXAtfb'),
                               style='Accent.TButton')
        discord_btn.grid(row=1, column=0, sticky='ew', pady=5)
        
                        
        self.status_msg = ttk.Label(footer, text='Ready to fish!', 
                                   style='Status.TLabel')
        self.status_msg.pack(pady=5)

    def create_fishing_location_section(self, start_row):
        """Create the fishing location section (non-collapsible like settings)"""
                                                     
        theme_colors = self.theme_manager.themes[self.current_theme]["colors"]
        
                            
        fishing_frame = tk.LabelFrame(self.main_frame, text="🎣 Fishing Location", 
                                     bg=theme_colors["bg"], fg=theme_colors["accent"],
                                     font=('Segoe UI', 11, 'bold'), padx=20, pady=15)
        fishing_frame.grid(row=start_row, column=0, sticky='ew', pady=(0, 20), padx=10)
        
                                                
        if not hasattr(self, 'fishing_location'):
            self.fishing_location = None
            
                                 
        location_label = tk.Label(fishing_frame, text="Cast Location:", 
                                 bg=theme_colors["bg"], fg=theme_colors["fg"])
        location_label.grid(row=0, column=0, sticky='w', pady=5)
        
                                                      
        button_text = f"🎯 Location: {self.fishing_location}" if self.fishing_location else "🎯 Set Fishing Location"
        
        self.fishing_location_button = tk.Button(fishing_frame, text=button_text,
                                               bg=theme_colors["button_bg"], fg=theme_colors["fg"],
                                               command=lambda: self.capture_mouse_click('fishing_location'),
                                               width=25, relief='flat')
        self.fishing_location_button.grid(row=0, column=1, sticky='w', padx=(10, 0), pady=5)
        
                   
        info_label = tk.Label(fishing_frame, 
                             text="Click to set where you want to cast your fishing rod", 
                             bg=theme_colors["bg"], fg=theme_colors["fg"],
                             font=('Segoe UI', 8))
        info_label.grid(row=1, column=0, columnspan=2, sticky='w', pady=(5, 0))
        
        fishing_frame.columnconfigure(1, weight=1)

    def update_fishing_location_colors(self):
        """Update fishing location section colors when theme changes"""
        try:
            theme_colors = self.theme_manager.themes[self.current_theme]["colors"]
            
                                                                             
            for child in self.main_frame.winfo_children():
                if isinstance(child, tk.LabelFrame) and "Fishing Location" in child.cget("text"):
                                         
                    child.configure(bg=theme_colors["bg"], fg=theme_colors["accent"])
                    
                                              
                    for widget in child.winfo_children():
                        if isinstance(widget, tk.Label):
                            widget.configure(bg=theme_colors["bg"], fg=theme_colors["fg"])
                        elif isinstance(widget, tk.Button):
                            widget.configure(bg=theme_colors["button_bg"], fg=theme_colors["fg"])
                    break
        except Exception as e:
            print(f"Error updating fishing location colors: {e}")
    
                                                         
    
    def create_auto_bait_feature_card(self, parent, row):
        """Create auto bait feature card"""
        card = ttk.LabelFrame(parent, text="🎣 Auto Bait Management", padding=15)
        card.grid(row=row, column=0, sticky='ew', pady=(0, 15))
        
        ttk.Label(card, text="Automatically clicks bait at the top when you run out",
                 style='Description.TLabel').pack(anchor='w', pady=(0, 10))
        
        self.auto_bait_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(card, text="Enable Auto Bait", variable=self.auto_bait_var,
                       command=self.toggle_auto_bait).pack(anchor='w', pady=5)
        
                            
        btn_frame = ttk.Frame(card)
        btn_frame.pack(fill='x', pady=5)
        btn_frame.columnconfigure((0, 1), weight=1)
        
        self.top_bait_btn = ttk.Button(btn_frame, text='Set Top Bait 1', 
                                      command=lambda: self.capture_mouse_click('top_bait'),
                                      style='TButton')
        self.top_bait_btn.grid(row=0, column=0, sticky='ew', padx=(0, 5))
        ToolTip(self.top_bait_btn, "Click on your top bait selection in the inventory")
        
        self.top_bait_2_btn = ttk.Button(btn_frame, text='Set Top Bait 2', 
                                        command=lambda: self.capture_mouse_click('top_bait_2'),
                                        style='TButton')
        self.top_bait_2_btn.grid(row=0, column=1, sticky='ew', padx=(5, 0))
        ToolTip(self.top_bait_2_btn, "Click on your bait AGAIN (backup for hover detection)")
        
        self.top_bait_status = ttk.Label(card, text='Both points must be set', style='Description.TLabel')
        self.top_bait_status.pack(anchor='w', pady=5)
    
    def create_fruit_storage_feature_card(self, parent, row):
        """Create fruit storage feature card"""
        card = ttk.LabelFrame(parent, text="🍎 Devil Fruit Storage", padding=15)
        card.grid(row=row, column=0, sticky='ew', pady=(0, 15))
        
        ttk.Label(card, text="Automatically store devil fruits when caught",
                 style='Description.TLabel').pack(anchor='w', pady=(0, 10))
        
        self.fruit_storage_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(card, text="Enable Fruit Storage", variable=self.fruit_storage_var,
                       command=self.toggle_fruit_storage).pack(anchor='w', pady=5)
        
                        
        key_frame = ttk.Frame(card)
        key_frame.pack(fill='x', pady=10)
        key_frame.columnconfigure((1, 3, 5), weight=1)
        
        ttk.Label(key_frame, text="Rod Key:").grid(row=0, column=0, sticky='w', padx=(0, 5))
        self.rod_key_entry = ttk.Entry(key_frame, width=5)
        self.rod_key_entry.insert(0, '1')
        self.rod_key_entry.grid(row=0, column=1, sticky='w', padx=(0, 15))
        self.rod_key_entry.bind('<FocusOut>', lambda e: self.save_inventory_keys())
        
        ttk.Label(key_frame, text="Fruit Key 1:").grid(row=0, column=2, sticky='w', padx=(0, 5))
        self.fruit_key_entry = ttk.Entry(key_frame, width=5)
        self.fruit_key_entry.insert(0, '2')
        self.fruit_key_entry.grid(row=0, column=3, sticky='w', padx=(0, 15))
        self.fruit_key_entry.bind('<FocusOut>', lambda e: self.save_inventory_keys())
        
        ttk.Label(key_frame, text="Fruit Key 2:").grid(row=0, column=4, sticky='w', padx=(0, 5))
        self.fruit_key_2_entry = ttk.Entry(key_frame, width=5)
        self.fruit_key_2_entry.insert(0, '3')
        self.fruit_key_2_entry.grid(row=0, column=5, sticky='w')
        self.fruit_key_2_entry.bind('<FocusOut>', lambda e: self.save_inventory_keys())
        
                     
        guide_text = """HOW TO USE:
1. Pick up a devil fruit in-game
2. Click 'Set Fruit Point 1' → Click the 'Store' button in-game
3. Click 'Set Fruit Point 2' → Click the 'Store' button AGAIN (backup)
4. Enable 'Auto Bait' feature to set bait selection point

⚠️ REQUIREMENTS:
• Keys must match your in-game inventory slots
• Keep ONLY rod in first slot! Clear rest of inventory bar!"""
        
                                        
        btn_frame = ttk.Frame(card)
        btn_frame.pack(fill='x', pady=5)
        btn_frame.columnconfigure((0, 1), weight=1)
        
        self.fruit_point_btn = ttk.Button(btn_frame, text='Set Fruit Point 1', 
                                         command=lambda: self.capture_mouse_click('fruit_point'),
                                         style='TButton')
        self.fruit_point_btn.grid(row=0, column=0, sticky='ew', padx=(0, 5))
        ToolTip(self.fruit_point_btn, "Click on the 'Store' button when you pick up a devil fruit")
        
        self.fruit_point_2_btn = ttk.Button(btn_frame, text='Set Fruit Point 2', 
                                           command=lambda: self.capture_mouse_click('fruit_point_2'),
                                           style='TButton')
        self.fruit_point_2_btn.grid(row=0, column=1, sticky='ew', padx=(5, 0))
        ToolTip(self.fruit_point_2_btn, "Click on the 'Store' button AGAIN (backup for hover detection)")
        
                         
        status_frame = ttk.Frame(card)
        status_frame.pack(fill='x', pady=5)
        
        self.fruit_storage_status = ttk.Label(status_frame, text='Both points must be set', 
                                             style='Description.TLabel')
        self.fruit_storage_status.pack(side='left')
        
        help_btn = ttk.Button(status_frame, text='? Setup Guide', width=15)
        help_btn.pack(side='right')
        ToolTip(help_btn, guide_text)
    
    def create_auto_purchase_feature_card(self, parent, row):
        """Create auto purchase feature card"""
        card = ttk.LabelFrame(parent, text="🛒 Auto Purchase Bait", padding=15)
        card.grid(row=row, column=0, sticky='ew', pady=(0, 15))
        
        ttk.Label(card, text="Automatically buy bait every X fish caught",
                 style='Description.TLabel').pack(anchor='w', pady=(0, 10))
        
        self.auto_purchase_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(card, text="Enable Auto Purchase", variable=self.auto_purchase_var,
                       command=self.toggle_auto_purchase).pack(anchor='w', pady=5)
        
                           
        interval_frame = ttk.Frame(card)
        interval_frame.pack(fill='x', pady=10)
        
        ttk.Label(interval_frame, text="Buy bait every:").pack(side='left', padx=(0, 10))
                                                               
        interval_default = getattr(self, 'purchase_interval_value', 0)
        self.purchase_interval = tk.IntVar(value=interval_default)
        purchase_entry = ttk.Entry(interval_frame, textvariable=self.purchase_interval, width=8)
        purchase_entry.pack(side='left', padx=(0, 5))
        purchase_entry.bind('<FocusOut>', lambda e: self.auto_save_settings())
        ttk.Label(interval_frame, text="fish").pack(side='left')
        
                                
        guide_text = """Auto Purchase Setup Guide:

Point 1: Click YES/BUY button (same area as confirm)
Point 2: Click amount input field (also works for '...' area)
Point 3: Click Cancel button

⚠️ IMPORTANT:
DON'T click on the fish seller NPC!
The macro automatically presses 'E' to open the shop."""
        
        points_header = ttk.Frame(card)
        points_header.pack(fill='x', pady=(10, 5))
        
        points_label = ttk.Label(points_header, text="Set 3 purchase points in order:",
                                style='Description.TLabel')
        points_label.pack(side='left')
        
        help_btn = ttk.Button(points_header, text='?', width=3)
        help_btn.pack(side='right')
        ToolTip(help_btn, guide_text)
        
        self.point_buttons = {}
                                                            
        if not hasattr(self, 'point_coords'):
            self.point_coords = {}
        
        point_tooltips = [
            "Click the YES/BUY button in the purchase dialog",
            "Click the amount input field or '...' area",
            "Click the Cancel button to exit the shop"
        ]
        
        for i in range(1, 4):
            btn = ttk.Button(card, text=f'Set Point {i}', 
                           command=lambda idx=i: self.capture_purchase_point(idx),
                           style='TButton')
            btn.pack(fill='x', pady=2)
            self.point_buttons[i] = btn
            ToolTip(btn, point_tooltips[i-1])
    
    def create_webhook_feature_card(self, parent, row):
        """Create webhook feature card"""
        card = ttk.LabelFrame(parent, text="🔔 Discord Webhooks", padding=15)
        card.grid(row=row, column=0, sticky='ew', pady=(0, 15))
        
        ttk.Label(card, text="Get notifications in Discord",
                 style='Description.TLabel').pack(anchor='w', pady=(0, 10))
        
        self.webhook_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(card, text="Enable Webhooks", variable=self.webhook_var,
                       command=self.toggle_webhook).pack(anchor='w', pady=5)
        
                     
        ttk.Label(card, text="Webhook URL:").pack(anchor='w', pady=(10, 5))
        self.webhook_entry = ttk.Entry(card)
        self.webhook_entry.pack(fill='x', pady=5)
        self.webhook_entry.bind('<FocusOut>', lambda e: self.save_webhook_url())
        
                         
        interval_frame = ttk.Frame(card)
        interval_frame.pack(fill='x', pady=10)
        
        ttk.Label(interval_frame, text="Update every:").pack(side='left', padx=(0, 10))
        self.webhook_interval_var = tk.IntVar(value=10)
        self.webhook_interval_var.trace_add('write', lambda *args: self.auto_save_settings())
        ttk.Entry(interval_frame, textvariable=self.webhook_interval_var, width=8).pack(side='left', padx=(0, 5))
        ttk.Label(interval_frame, text="fish").pack(side='left')
        
                              
        ttk.Label(card, text="Notification Types:", style='Description.TLabel').pack(anchor='w', pady=(10, 5))
        
        self.fish_progress_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(card, text="🐟 Fish Progress Updates", 
                       variable=self.fish_progress_var).pack(anchor='w', pady=2)
        
        self.fruit_catch_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(card, text="🍎 Devil Fruit Catches", 
                       variable=self.fruit_catch_var).pack(anchor='w', pady=2)
        
                                                       
                                                          
                                                             
                                                                                
        
        self.purchase_notif_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(card, text="🛒 Auto Purchase Alerts", 
                       variable=self.purchase_notif_var).pack(anchor='w', pady=2)
    
    def create_compact_startup_section(self, parent):
        """Compact startup section for setup tab"""
                                                                       
        zoom_default = getattr(self, 'auto_zoom_enabled', False)
        self.zoom_var = tk.BooleanVar(value=zoom_default)
        zoom_check = ttk.Checkbutton(parent, text="🔍 Auto Zoom (zooms out then back in)",
                       variable=self.zoom_var, command=self._on_zoom_var_change)
        zoom_check.pack(anchor='w', pady=5)
        
        mouse_pos_default = getattr(self, 'auto_mouse_position_enabled', False)
        self.mouse_pos_var = tk.BooleanVar(value=mouse_pos_default)
        mouse_check = ttk.Checkbutton(parent, text="🖱️ Auto Mouse Position (moves to fishing spot)",
                       variable=self.mouse_pos_var, command=self._on_mouse_pos_var_change)
        mouse_check.pack(anchor='w', pady=5)
    
    def create_compact_hotkeys_section(self, parent):
        """Compact hotkeys section for settings tab"""
        hotkeys_info = [
            ("F1", "Start/Stop Fishing"),
            ("F2", "Toggle Overlay"),
            ("F3", "Emergency Exit"),
            ("F4", "Minimize to Taskbar")
        ]
        
        for key, description in hotkeys_info:
            row = ttk.Frame(parent)
            row.pack(fill='x', pady=5)
            
            ttk.Label(row, text=f"{key}:", font=('Segoe UI', 10, 'bold'),
                     width=8).pack(side='left')
            ttk.Label(row, text=description, style='Description.TLabel').pack(side='left', padx=(10, 0))

    def _sync_zoom_vars(self):
        """Sync zoom_var (Step 3) with auto_zoom_var (Settings) and update auto_zoom_enabled"""
        try:
            if getattr(self, '_loading_settings', False):
                return
                
            zoom_value = self.zoom_var.get()
            
                                    
            if hasattr(self, 'auto_zoom_var'):
                self.auto_zoom_var.set(zoom_value)
            
                                          
            self.auto_zoom_enabled = zoom_value
            
                                     
            self.auto_save_settings()
        except Exception as e:
            pass

    def _sync_auto_zoom_var(self):
        """Sync auto_zoom_var (Settings) with zoom_var (Step 3) and update auto_zoom_enabled"""
        try:
            if getattr(self, '_loading_settings', False):
                return
                
            zoom_value = self.auto_zoom_var.get()
            
                                        
            if hasattr(self, 'zoom_var'):
                self.zoom_var.set(zoom_value)
            
                                          
            self.auto_zoom_enabled = zoom_value
            
                                     
            self.auto_save_settings()
        except Exception as e:
            pass

    def _sync_auto_mouse_position_var(self):
        """Sync auto_mouse_position_var (Settings) with mouse_pos_var (Step 3) and update auto_mouse_position_enabled"""
        try:
            if getattr(self, '_loading_settings', False):
                return
                
            mouse_value = self.auto_mouse_position_var.get()
            
                                        
            if hasattr(self, 'mouse_pos_var'):
                self.mouse_pos_var.set(mouse_value)
            
                                          
            self.auto_mouse_position_enabled = mouse_value
            
                                     
            self.auto_save_settings()
        except Exception as e:
            pass

    def _on_zoom_var_change(self):
        """Handle zoom_var checkbox click (Step 3)"""
        try:
            loading_flag = getattr(self, '_loading_settings', False)
            zoom_value = self.zoom_var.get()
            print(f"🔍 ZOOM CLICK: _loading_settings={loading_flag}, zoom_value={zoom_value}")
            
            if loading_flag:
                print(f"⏸️ BLOCKED: _loading_settings is True, skipping save")
                return
                
            print(f"✅ ZOOM SAVE PROCEEDING: Setting auto_zoom_enabled={zoom_value}")
            
                                    
            if hasattr(self, 'auto_zoom_var'):
                self.auto_zoom_var.set(zoom_value)
            
                                          
            self.auto_zoom_enabled = zoom_value
            
                                     
            print(f"📞 Calling auto_save_settings() for zoom")
            self.auto_save_settings()
        except Exception as e:
            print(f"❌ Error in _on_zoom_var_change: {e}")
            pass

    def _on_mouse_pos_var_change(self):
        """Handle mouse_pos_var checkbox click (Step 3)"""
        try:
            loading_flag = getattr(self, '_loading_settings', False)
            mouse_value = self.mouse_pos_var.get()
            import traceback
            caller = traceback.extract_stack()[-2].name
            print(f"🖱️ MOUSE POS CHANGE TRIGGERED (from {caller}): _loading_settings={loading_flag}, mouse_value={mouse_value}")
            
            if loading_flag:
                print(f"⏸️ BLOCKED: _loading_settings is True, skipping save")
                return
                
            print(f"✅ MOUSE POS SAVE PROCEEDING: Setting auto_mouse_position_enabled={mouse_value}")
            
            if hasattr(self, 'auto_mouse_position_var'):
                self.auto_mouse_position_var.set(mouse_value)
                
            self.auto_mouse_position_enabled = mouse_value
            
            print(f"📞 Calling auto_save_settings() for mouse_pos")
            self.auto_save_settings()
        except Exception as e:
            print(f"❌ Error in _on_mouse_pos_var_change: {e}")
            pass
    
    def create_compact_hotkeys_section(self, parent):
        """Compact hotkeys section for settings tab"""
        hotkeys_info = [
            ("F1", "Start/Stop Fishing"),
            ("F2", "Toggle Overlay"),
            ("F3", "Emergency Exit"),
            ("F4", "Minimize to Taskbar")
        ]
        
        for key, description in hotkeys_info:
            row = ttk.Frame(parent)
            row.pack(fill='x', pady=5)
            
            ttk.Label(row, text=f"{key}:", font=('Segoe UI', 10, 'bold'),
                     width=8).pack(side='left')
            ttk.Label(row, text=description, style='Description.TLabel').pack(side='left', padx=(10, 0))
    
    def add_activity(self, message):
        """Add message to activity log with enhanced styling"""
        if hasattr(self, 'activity_log'):
            timestamp = datetime.now().strftime("%H:%M:%S")
            
                                                
            self.activity_log.insert('end', f"[{timestamp}] ", 'timestamp')
            
                                                            
            style = None
            if any(emoji in message for emoji in ['✅', '✔️', '🎉', '🎊']):
                style = 'success'
            elif any(emoji in message for emoji in ['⚠️', '⏸️', '🔄']):
                style = 'warning'
            elif any(emoji in message for emoji in ['❌', '⛔', '🚫']):
                style = 'error'
            elif any(emoji in message for emoji in ['ℹ️', '📊', '🔔']):
                style = 'info'
            
                                                     
            self.activity_log.insert('end', f"{message}\n", style)
            self.activity_log.see('end')
    
    def copy_activity_logs(self):
        """Copy all activity logs to clipboard with markdown formatting"""
        try:
                                            
            log_content = self.activity_log.get('1.0', 'end-1c')
            
                                         
            formatted_logs = f"```\n{log_content}\n```"
            
                               
            self.root.clipboard_clear()
            self.root.clipboard_append(formatted_logs)
            self.root.update()                               
            
                             
            original_text = self.copy_logs_btn.config('text')[-1]
            self.copy_logs_btn.config(text="✓")
            self.root.after(1000, lambda: self.copy_logs_btn.config(text=original_text))
            
            self.status_msg.config(text="📋 Logs copied to clipboard!", foreground='green')
            
        except Exception as e:
            self.status_msg.config(text=f"❌ Failed to copy logs: {e}", foreground='red')
    
    def toggle_main_loop(self):
        """Toggle the main fishing loop"""
        if self.main_loop_active:
            self.stop_main_loop()
            self.start_stop_btn.config(text='▶️ START FISHING')
            self.add_activity("⏸️ Bot stopped")
        else:
            self.start_main_loop()
            self.start_stop_btn.config(text='⏹️ STOP FISHING')
            self.add_activity("▶️ Bot started")
    
    def test_setup(self):
        """Test the setup configuration"""
        self.add_activity("🧪 Testing setup...")
                             
        messagebox.showinfo("Test", "Setup test functionality - to be implemented")
    
    def open_discord_link(self, url):
        """Open Discord server link"""
        import webbrowser
        webbrowser.open(url)
    
                                                   
    
    def toggle_auto_bait(self):
        """Toggle auto bait feature"""
        self.auto_bait_enabled = self.auto_bait_var.get()
        status = "enabled" if self.auto_bait_enabled else "disabled"
        self.add_activity(f"🎣 Auto Bait {status}")
        self.auto_save_settings()
    
    def save_inventory_keys(self):
        """Save inventory keys from entry fields"""
        try:
            if hasattr(self, 'rod_key_entry'):
                self.rod_key = self.rod_key_entry.get()
            if hasattr(self, 'fruit_key_entry'):
                self.fruit_storage_key = self.fruit_key_entry.get()
            if hasattr(self, 'fruit_key_2_entry'):
                self.fruit_storage_key_2 = self.fruit_key_2_entry.get()
            self.auto_save_settings()
        except Exception as e:
            print(f"Error saving inventory keys: {e}")
    
    def save_webhook_url(self):
        """Save webhook URL from entry field"""
        try:
            if hasattr(self, 'webhook_entry'):
                self.webhook_url = self.webhook_entry.get()
            self.auto_save_settings()
        except Exception as e:
            print(f"Error saving webhook URL: {e}")
    
    def toggle_fruit_storage(self):
        """Toggle fruit storage feature"""
        self.fruit_storage_enabled = self.fruit_storage_var.get()
        
                                       
        if hasattr(self, 'fruit_key_entry'):
            self.fruit_storage_key = self.fruit_key_entry.get()
        if hasattr(self, 'fruit_key_2_entry'):
            self.fruit_storage_key_2 = self.fruit_key_2_entry.get()
        if hasattr(self, 'rod_key_entry'):
            self.rod_key = self.rod_key_entry.get()
        
        status = "enabled" if self.fruit_storage_enabled else "disabled"
        self.add_activity(f"🍎 Fruit Storage {status}")
        self.auto_save_settings()
    
    def toggle_auto_purchase(self):
        """Toggle auto purchase feature"""
        enabled = self.auto_purchase_var.get()
        
                                 
        try:
            interval = self.purchase_interval.get()
            if interval > 0:
                self.loops_per_purchase = interval
        except:
            pass
        
        status = "enabled" if enabled else "disabled"
        self.add_activity(f"🛒 Auto Purchase {status}")
        self.auto_save_settings()
    
    def toggle_webhook(self):
        """Toggle webhook feature"""
        self.webhook_enabled = self.webhook_var.get()
        
                                              
        if hasattr(self, 'webhook_entry'):
            self.webhook_url = self.webhook_entry.get()
        if hasattr(self, 'webhook_interval_var'):
            try:
                self.webhook_interval = self.webhook_interval_var.get()
            except:
                pass
        
                                     
        if hasattr(self, 'fish_progress_var'):
            self.fish_progress_webhook_enabled = self.fish_progress_var.get()
        if hasattr(self, 'fruit_catch_var'):
            self.devil_fruit_webhook_enabled = self.fruit_catch_var.get()
        if hasattr(self, 'fruit_spawn_var'):
            self.fruit_spawn_webhook_enabled = self.fruit_spawn_var.get()
        if hasattr(self, 'purchase_notif_var'):
            self.purchase_webhook_enabled = self.purchase_notif_var.get()
        
        status = "enabled" if self.webhook_enabled else "disabled"
        self.add_activity(f"🔔 Discord Webhooks {status}")
        self.auto_save_settings()
    
    def start_main_loop(self):
        """Wrapper to call pause_fishing.py start method"""
                                               
        if hasattr(self, 'pause_fishing'):
            self.resume_fishing()
        else:
                                              
            self.main_loop_active = True
            self.add_activity("▶️ Bot started")
    
    def stop_main_loop(self):
        """Stop the main fishing loop"""
        self.main_loop_active = False
        self.loop_status.config(text='● Main Loop: OFF', style='StatusOff.TLabel')
        self.add_activity("⏹️ Bot stopped")
    
    def toggle_layout_overlay(self):
        """Toggle the layout overlay"""
        if hasattr(self, 'overlay_manager'):
                                       
                                                                     
            self.add_activity("👁️ Toggled overlay")
    
    def minimize_to_taskbar(self):
        """Minimize window to taskbar"""
        self.root.iconify()
        self.add_activity("🔽 Minimized to taskbar")

    def update_status(self, message, status_type='info', icon='ℹ️'):
        """Update the status message with color coding"""
        try:
            theme_colors = self.theme_manager.themes[self.current_theme]["colors"]
            color_map = {
                'info': theme_colors["accent"],
                'success': theme_colors["success"],
                'error': theme_colors["error"],
                'warning': theme_colors["warning"]
            }
            color = color_map.get(status_type, theme_colors["fg"])
            self.status_msg.config(text=f'{icon} {message}', foreground=color)
        except Exception:
                                            
            self.status_msg.config(text=f'{icon} {message}', foreground='blue')

    def capture_mouse_click(self, idx):
        """Start a listener to capture the next mouse click and store its coordinates."""            
        try:
                                          
            if isinstance(idx, int):
                                                     
                self.status_msg.config(text=f'Click anywhere to set Point {idx}...', foreground='blue')
            elif idx == 'fruit_point':
                self.status_msg.config(text='Click anywhere to set Fruit Point...', foreground='blue')
            elif idx == 'fruit_point_2':
                self.status_msg.config(text='Click anywhere to set Fruit Point 2 (backup)...', foreground='blue')
            elif idx == 'bait_point':
                self.status_msg.config(text='Click anywhere to set Bait Point...', foreground='blue')
            elif idx == 'fishing_location':
                self.status_msg.config(text='Click anywhere to set Fishing Location...', foreground='blue')

            def _on_click(x, y, button, pressed):
                if pressed:
                    if isinstance(idx, int):
                                                       
                        self.point_coords[idx] = (x, y)
                        try:
                            self.root.after(0, lambda: self.update_point_button(idx))
                            self.root.after(0, lambda: self.status_msg.config(text=f'Point {idx} set: ({x}, {y})', foreground='green'))
                        except Exception:
                            pass
                    elif idx == 'fruit_point':
                                             
                        if not hasattr(self, 'fruit_coords'):
                            self.fruit_coords = {}
                        self.fruit_coords['fruit_point'] = (x, y)
                        try:
                                                        
                            if hasattr(self, 'fruit_point_btn'):
                                self.root.after(0, lambda coords=(x, y): self.fruit_point_btn.config(text=f'✓ Fruit 1: ({coords[0]}, {coords[1]})'))
                                                                  
                            if hasattr(self, 'fruit_point_button'):
                                self.root.after(0, lambda coords=(x, y): self.fruit_point_button.config(text=f'Fruit Point: {coords}'))
                            self.root.after(0, lambda coords=(x, y): self.status_msg.config(text=f'Fruit Point 1 (Store button) set: ({coords[0]}, {coords[1]})', foreground='green'))
                        except Exception:
                            pass
                    elif idx == 'fruit_point_2':
                                                        
                        if not hasattr(self, 'fruit_coords'):
                            self.fruit_coords = {}
                        self.fruit_coords['fruit_point_2'] = (x, y)
                        try:
                                                        
                            if hasattr(self, 'fruit_point_2_btn'):
                                self.root.after(0, lambda coords=(x, y): self.fruit_point_2_btn.config(text=f'✓ Fruit 2 (Backup): ({coords[0]}, {coords[1]})'))
                                                                  
                            if hasattr(self, 'fruit_point_2_button'):
                                self.root.after(0, lambda coords=(x, y): self.fruit_point_2_button.config(text=f'Fruit Point 2: {coords}'))
                            self.root.after(0, lambda coords=(x, y): self.status_msg.config(text=f'Fruit Point 2 (Backup Store button) set: ({coords[0]}, {coords[1]})', foreground='green'))
                        except Exception:
                            pass
                    elif idx == 'top_bait':
                                                  
                        self.top_bait_coords = (x, y)
                        try:
                                                        
                            if hasattr(self, 'top_bait_btn'):
                                self.root.after(0, lambda coords=(x, y): self.top_bait_btn.config(text=f'✓ Bait 1: ({coords[0]}, {coords[1]})'))
                                                                  
                            if hasattr(self, 'top_bait_button'):
                                self.root.after(0, lambda coords=(x, y): self.top_bait_button.config(text=f'✓ Top Bait: ({coords[0]}, {coords[1]})'))
                            self.root.after(0, lambda coords=(x, y): self.status_msg.config(text=f'Top Bait 1 set: ({coords[0]}, {coords[1]}) - Used for auto-bait & fruit storage', foreground='green'))
                        except Exception:
                            pass
                    elif idx == 'top_bait_2':
                                               
                        self.top_bait_coords_2 = (x, y)
                        try:
                                                        
                            if hasattr(self, 'top_bait_2_btn'):
                                self.root.after(0, lambda coords=(x, y): self.top_bait_2_btn.config(text=f'✓ Bait 2 (Backup): ({coords[0]}, {coords[1]})'))
                            self.root.after(0, lambda coords=(x, y): self.status_msg.config(text=f'Top Bait 2 (Backup) set: ({coords[0]}, {coords[1]})', foreground='green'))
                        except Exception:
                            pass
                    elif idx == 'fishing_location':
                                                
                        self.fishing_location = (x, y)
                        try:
                                                                           
                            self.root.after(0, lambda coords=(x, y): self.fishing_location_btn.config(text=f'🎯 Cast Location: {coords}'))
                            self.root.after(0, lambda coords=(x, y): self.fishing_location_status.config(text=f'✅ Set: {coords}', style='StatusOn.TLabel'))
                            self.root.after(0, lambda coords=(x, y): self.status_msg.config(text=f'Cast Location set: {coords}', foreground='green'))
                                                                          
                            if hasattr(self, 'fishing_location_button'):
                                self.root.after(0, lambda coords=(x, y): self.fishing_location_button.config(text=f'🎯 Location: {coords}'))
                        except Exception as e:
                            print(f"Error updating fishing location: {e}")
                            pass
                    
                    try:
                        self.root.after(0, lambda: self.auto_save_settings())                               
                        self.root.after(100, lambda: self.status_msg.config(text='💾 Settings auto-saved', foreground='green'))
                    except Exception as e:
                        print(f"❌ Error auto-saving after point set: {e}")
                        self.root.after(0, lambda: self.status_msg.config(text=f'❌ Save failed: {e}', foreground='red'))
                        pass
                    return False                                   
            
            listener = pynput_mouse.Listener(on_click=_on_click)
            listener.start()
        except Exception as e:
            try:
                self.status_msg.config(text=f'Error capturing point: {e}', foreground='red')
            except Exception:
                return None

    def update_point_button(self, idx):
        coords = self.point_coords.get(idx)
        if coords and idx in self.point_buttons:
            self.point_buttons[idx].config(text=f'Point {idx}: {coords}')
        return None
    
    def capture_purchase_point(self, idx):
        """Wrapper for capturing purchase points (for v3 UI compatibility)"""
        self.capture_mouse_click(idx)

    def capture_key_press(self, key_type):
        """Capture key press for fruit storage or rod selection"""
        try:
            if key_type == 'fruit':
                self.status_msg.config(text='Press a key (1-9) for Fruit Storage...', foreground='blue')
            elif key_type == 'rod':
                self.status_msg.config(text='Press a key (1-9) for Rod Selection...', foreground='blue')

            def _on_key(key):
                try:
                                                      
                    key_char = key.char if hasattr(key, 'char') and key.char else None
                    
                                          
                    if key_char and key_char in '123456789':
                        if key_type == 'fruit':
                            self.fruit_storage_key = key_char
                            try:
                                self.root.after(0, lambda: self.fruit_key_button.config(text=f'Key {key_char} ✓'))
                                self.root.after(0, lambda: self.status_msg.config(text=f'Fruit key set: {key_char}', foreground='green'))
                            except Exception:
                                pass
                        elif key_type == 'rod':
                            self.rod_key = key_char
                            try:
                                self.root.after(0, lambda: self.rod_key_button.config(text=f'Key {key_char} ✓'))
                                self.root.after(0, lambda: self.status_msg.config(text=f'Rod key set: {key_char}', foreground='green'))
                            except Exception:
                                pass
                        
                        try:
                            self.root.after(0, lambda: self.auto_save_settings())
                        except Exception:
                            pass
                        return False                 
                except Exception:
                    pass
            
            listener = pynput_keyboard.Listener(on_press=_on_key)
            listener.start()
        except Exception as e:
            try:
                self.status_msg.config(text=f'Error capturing key: {e}', foreground='red')
            except Exception:
                return None

    def set_bait_point(self, bait_type):
        """Set bait coordinate points"""
        if bait_type == 'top_bait':
                                                                    
            if not hasattr(self, 'top_bait_coords'):
                self.top_bait_coords = None
            
            try:
                self.status_msg.config(text='Click to set top bait position...', foreground='blue')
                
                def _on_click(x, y, button, pressed):
                    if pressed:
                        self.top_bait_coords = (x, y)
                        print(f"✅ Top bait position set at ({x}, {y})")
                        
                                            
                        try:
                            self.root.after(0, lambda: self.top_bait_button.config(text=f'Top Bait: ({x}, {y})'))
                            self.root.after(0, lambda: self.status_msg.config(text=f'Top bait position set: ({x}, {y})', foreground='green'))
                        except Exception:
                            pass
                        
                                            
                        try:
                            self.root.after(0, lambda: self.auto_save_settings())
                        except Exception:
                            pass
                        
                        return False                 
                
                listener = pynput_mouse.Listener(on_click=_on_click)
                listener.start()
            except Exception as e:
                try:
                    self.status_msg.config(text=f'Error setting bait point: {e}', foreground='red')
                except Exception:
                    pass



    def _click_at(self, coords):
        """Move cursor to coords and perform a left click (Windows 10/11 compatible)."""
        try:
            x, y = (int(coords[0]), int(coords[1]))
                                                                  
            screen_width = win32api.GetSystemMetrics(0)
            screen_height = win32api.GetSystemMetrics(1)
            nx = int(x * 65535 / screen_width)
            ny = int(y * 65535 / screen_height)
            
                                                       
            win32api.mouse_event(win32con.MOUSEEVENTF_ABSOLUTE | win32con.MOUSEEVENTF_MOVE, nx, ny, 0, 0)
            threading.Event().wait(0.05)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            threading.Event().wait(0.05)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        except Exception as e:
            print(f'Error clicking at {coords}: {e}')

    def _right_click_at(self, coords):
        """Move cursor to coords and perform a right click (Windows 10/11 compatible)."""
        try:
            x, y = (int(coords[0]), int(coords[1]))
                                                                  
            screen_width = win32api.GetSystemMetrics(0)
            screen_height = win32api.GetSystemMetrics(1)
            nx = int(x * 65535 / screen_width)
            ny = int(y * 65535 / screen_height)
            
                                                       
            win32api.mouse_event(win32con.MOUSEEVENTF_ABSOLUTE | win32con.MOUSEEVENTF_MOVE, nx, ny, 0, 0)
            threading.Event().wait(0.05)
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
            threading.Event().wait(0.05)
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
        except Exception as e:
            print(f'Error right-clicking at {coords}: {e}')

    def perform_auto_purchase_sequence(self):
        """Perform the auto-purchase sequence using saved points and amount.

Sequence (per user spec):
- press 'e', wait
- click point1, wait
- click point2, wait
- type amount, wait
- click point1, wait
- click point3, wait
- click point2, wait
- right-click point4 to close menu
"""
        from datetime import datetime
        pts = self.point_coords
        if not pts or not pts.get(1) or not pts.get(2) or not pts.get(3) or not pts.get(4):
            print('Auto purchase aborted: points not fully set (need points 1-4).')
            return
        
                                                            
        if not self.main_loop_active:
            print('Auto purchase aborted: main loop stopped.')
            return
        
        amount = str(self.auto_purchase_amount)
        
                                                    
        self.set_recovery_state("menu_opening", {"action": "pressing_e_key", "amount": amount})
        self.log('Holding E key for 3 seconds...', "verbose")
        keyboard.press('e')
        threading.Event().wait(3.0)
        keyboard.release('e')
        threading.Event().wait(self.purchase_delay_after_key)
        
        if not self.main_loop_active:
            return
        
                                           
        self.set_recovery_state("clicking", {"action": "click_point_1", "point": pts[1]})
        self.log(f'Clicking Point 1: {pts[1]}', "verbose")
        self._click_at(pts[1])
        threading.Event().wait(self.purchase_click_delay)
        
        if not self.main_loop_active:
            return
        
                                           
        self.set_recovery_state("clicking", {"action": "click_point_2", "point": pts[2]})
        self.log(f'Clicking Point 2: {pts[2]}', "verbose")
        self._click_at(pts[2])
        threading.Event().wait(self.purchase_click_delay)
        
        if not self.main_loop_active:
            return
        
                                                                      
        self.log(f'Double-clicking Point 2 to focus: {pts[2]}', "verbose")
        self._click_at(pts[2])
        threading.Event().wait(0.1)
        
        if not self.main_loop_active:
            return
        
                                         
        self.set_recovery_state("typing", {"action": "typing_amount", "amount": amount})
        self.log(f'Typing amount: {amount}', "verbose")
                     
        keyboard.write(amount)
                                                  
        threading.Event().wait(self.purchase_after_type_delay + 0.5)
        
        if not self.main_loop_active:
            return
        
                                                 
        self.set_recovery_state("clicking", {"action": "click_point_1_confirm", "point": pts[1]})
        print(f'Clicking Point 1: {pts[1]}')
        self._click_at(pts[1])
        threading.Event().wait(self.purchase_click_delay)
        
        if not self.main_loop_active:
            return
        
                                           
        self.set_recovery_state("clicking", {"action": "click_point_3", "point": pts[3]})
        print(f'Clicking Point 3: {pts[3]}')
        self._click_at(pts[3])
        threading.Event().wait(self.purchase_click_delay)
        
        if not self.main_loop_active:
            return
        
                                           
        self.set_recovery_state("clicking", {"action": "click_point_2_final", "point": pts[2]})
        print(f'Clicking Point 2: {pts[2]}')
        self._click_at(pts[2])
        threading.Event().wait(self.purchase_click_delay)
        
        if not self.main_loop_active:
            return
        
                                                 
        self.set_recovery_state("clicking", {"action": "right_click_point_4", "point": pts[4]})
        print(f'Right-clicking Point 4: {pts[4]}')
        self._right_click_at(pts[4])
        threading.Event().wait(self.purchase_click_delay)
        
                                                     
        self.webhook_manager.send_purchase(amount)
        
        print()
    


    def start_rebind(self, action):
        """Start recording a new hotkey"""            
        self.recording_hotkey = action
        self.status_msg.config(text=f'Press a key to rebind \'{action}\'...', foreground='blue')
        self.loop_rebind_btn.config(state='disabled')
        self.layout_rebind_btn.config(state='disabled')                                 
        self.exit_rebind_btn.config(state='disabled')
        self.minimize_rebind_btn.config(state='disabled')
        listener = pynput_keyboard.Listener(on_press=self.on_key_press)
        listener.start()

    def on_key_press(self, key):
        """Handle key press during rebinding"""
        if self.recording_hotkey:
            try:
                if hasattr(key, 'char') and key.char:
                    key_str = key.char.lower()
                elif hasattr(key, 'name'):
                    key_str = key.name.lower()
                else:
                    key_str = str(key).split('.')[-1].lower()
                
                self.hotkeys[self.recording_hotkey] = key_str
                
                                  
                if self.recording_hotkey == 'toggle_loop':
                    self.loop_key_label.config(text=key_str.upper())
                elif self.recording_hotkey == 'toggle_layout':
                    self.layout_key_label.config(text=key_str.upper())
                elif self.recording_hotkey == 'exit':
                    self.exit_key_label.config(text=key_str.upper())
                elif self.recording_hotkey == 'toggle_minimize':
                    self.minimize_key_label.config(text=key_str.upper())
                
                self.recording_hotkey = None
                self.loop_rebind_btn.config(state='normal')
                self.layout_rebind_btn.config(state='normal')
                self.exit_rebind_btn.config(state='normal')
                self.minimize_rebind_btn.config(state='normal')
                self.status_msg.config(text=f'Hotkey set to {key_str.upper()}', foreground='green')
                self.register_hotkeys()
                return False                     
            except Exception as e:
                self.status_msg.config(text=f'Error setting hotkey: {e}', foreground='red')
                self.recording_hotkey = None
                self.loop_rebind_btn.config(state='normal')
                self.layout_rebind_btn.config(state='normal')
                self.exit_rebind_btn.config(state='normal')
                self.minimize_rebind_btn.config(state='normal')
                return False
        return False

    def register_hotkeys(self):
        """Register all hotkeys"""            
        try:
            keyboard.unhook_all()
            keyboard.add_hotkey(self.hotkeys['toggle_loop'], self.toggle_main_loop)
            keyboard.add_hotkey(self.hotkeys['toggle_layout'], self.toggle_layout)
            keyboard.add_hotkey(self.hotkeys['exit'], self.exit_app)
            keyboard.add_hotkey(self.hotkeys['toggle_minimize'], self.toggle_minimize_hotkey)
            print(f"✅ Hotkeys registered: {self.hotkeys}")
        except Exception as e:
            print(f'❌ Error registering hotkeys: {e}')
    
    def toggle_layout(self):
        """Toggle dual overlay mode via F2 hotkey"""
        if not hasattr(self, 'dual_overlay_active'):
            self.dual_overlay_active = False
        
        self.dual_overlay_active = not self.dual_overlay_active
        
        if self.dual_overlay_active:
                                
            self.show_dual_overlays()
            print("🔄 Dual overlay mode: ON (showing both bar and drop overlays)")
        else:
                                
            self.hide_dual_overlays()
            print("🔄 Dual overlay mode: OFF")
    
    def show_dual_overlays(self):
        """Show both bar and drop overlays simultaneously"""
        if not hasattr(self, 'overlay_manager_bar'):
            try:
                from src.overlay import OverlayManager
            except ImportError:
                from overlay import OverlayManager
            self.overlay_manager_bar = OverlayManager(self, fixed_layout='bar')
            self.overlay_manager_drop = OverlayManager(self, fixed_layout='drop')
        
                              
        self.overlay_manager_bar.create()
        self.overlay_manager_drop.create()
        
        self.overlay_status.config(text='● Overlay: ON', style='StatusOn.TLabel')
    
    def hide_dual_overlays(self):
        """Hide both overlays"""
        if hasattr(self, 'overlay_manager_bar') and self.overlay_manager_bar.window:
            self.overlay_manager_bar.destroy()
        if hasattr(self, 'overlay_manager_drop') and self.overlay_manager_drop.window:
            self.overlay_manager_drop.destroy()
        
        self.overlay_status.config(text='○ Overlay: OFF', style='StatusOff.TLabel')
    
    
    def update_layout_display(self):
        """Update GUI to show current layout"""
        layout_info = self.layout_manager.get_layout_info()
        layout_name = layout_info['name']
        
                                                           
    
    def toggle_minimize_hotkey(self):
        """Toggle between minimized and normal window via F4 hotkey"""
        print(f"🔧 F4 pressed - window state: {self.root.state()}")
        if self.root.state() == 'iconic':
            print("🔧 Restoring from taskbar")
            self.root.deiconify()
            self.root.lift()
        else:
            print("🔧 Minimizing to taskbar")
            self.root.iconify()
    



    def toggle_main_loop(self):
        """Toggle between Start/Pause/Resume with smart detection"""
        print(f"🔧 Toggle called - main_loop_active: {self.main_loop_active}, is_paused: {self.is_paused}")
        
        if not self.main_loop_active and not self.is_paused:
                            
            print("🔧 Calling start_fishing() - fresh start")
            self.start_fishing()
        elif self.main_loop_active and not self.is_paused:
                                          
            print("🔧 Calling pause_fishing() - pausing active loop")
            self.pause_fishing()
        elif not self.main_loop_active and self.is_paused:
                                          
            print("🔧 Calling resume_fishing() - resuming paused loop")
            self.resume_fishing()
        else:
            print(f"🔧 Unexpected state - main_loop_active: {self.main_loop_active}, is_paused: {self.is_paused}")
    
    def start_fishing(self):
        """Start fishing from scratch"""
                                               
        if getattr(self, 'auto_purchase_var', None) and self.auto_purchase_var.get():
            pts = getattr(self, 'point_coords', {})
            missing = [i for i in [1, 2, 3] if not pts.get(i)]
            if missing:
                messagebox.showwarning('Auto Purchase: Points missing', f'Please set Point(s) {missing} before starting Auto Purchase.')
                return
        
                                          
        self.main_loop_active = True
        self.is_paused = False
        self.start_time = time.time()
        self.total_paused_time = 0
        self.reset_fish_counter()
        
                   
        self.loop_status.config(text='● Main Loop: ACTIVE', style='StatusOn.TLabel')
        
                                    
        self.update_bait_status_display()
        
                                                                             
        self.main_loop_thread = threading.Thread(target=lambda: self.fishing_bot.run_main_loop(skip_initial_setup=False), daemon=True)
        self.main_loop_thread.start()
        
                             
        self.update_runtime_timer()
        
        self.log('🎣 Started fishing!', "important")
    
    def pause_fishing(self):
        """Pause the current fishing session"""
        self.main_loop_active = False
        self.is_paused = True
        self.pause_time = time.time()
        
                                   
        if self.is_clicking:
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            self.is_clicking = False
        
                   
        self.loop_status.config(text='● Main Loop: PAUSED', style='StatusOff.TLabel')
        
        self.log('⏸️ Fishing paused', "important")
    
    def resume_fishing(self):
        """Resume fishing with smart detection"""
                               
        if self.pause_time:
            self.total_paused_time += time.time() - self.pause_time
            self.pause_time = None
        
        self.main_loop_active = True
        self.is_paused = False
        
                                                                      
        if hasattr(self, 'fishing_bot'):
            self.fishing_bot.last_fruit_spawn_time = 0
            print("🔄 Fruit spawn detection reset - checking for spawns immediately")
        
                   
        self.loop_status.config(text='● Main Loop: ACTIVE', style='StatusOn.TLabel')
        
                                             
        self.main_loop_thread = threading.Thread(target=self.smart_resume_loop, daemon=True)
        self.main_loop_thread.start()
        
                              
        self.update_runtime_timer()
        
        self.log('▶️ Fishing resumed with smart detection', "important")
    
    def smart_resume_loop(self):
        """Resume loop with smart detection of current state"""
        import mss
        import numpy as np
        
                                                             
        target_color = (85, 170, 255)
        
        with mss.mss() as sct:
                                                    
            current_area = self.layout_manager.get_layout_area(self.layout_manager.current_layout)
            if not current_area:
                current_area = {'x': 700, 'y': 400, 'width': 200, 'height': 100}                    
            x = current_area['x']
            y = current_area['y']
            width = current_area['width']
            height = current_area['height']
            monitor = {'left': x, 'top': y, 'width': width, 'height': height}
            screenshot = sct.grab(monitor)
            img = np.array(screenshot)
            
                                       
            blue_found = False
            for row_idx in range(height):
                for col_idx in range(width):
                    b, g, r = img[row_idx, col_idx, 0:3]
                    if r == target_color[0] and g == target_color[1] and b == target_color[2]:
                        blue_found = True
                        break
                if blue_found:
                    break
        
        if blue_found:
            self.log('🎯 Blue fishing bar detected - resuming from current state', "important")
                                                                             
            self.fishing_bot.run_main_loop(skip_initial_setup=True)
        else:
            self.log('🎣 No fishing bar detected - starting fresh', "important")
                                                                     
            self.fishing_bot.run_main_loop(skip_initial_setup=False)

    def increment_fish_counter(self):
        """Increment fish counter and update display"""
        self.fish_count += 1
        self.webhook_counter += 1
        
                                  
        self.last_fish_time = time.time()
        self.last_activity_time = time.time()
        
        try:
            self.root.after(0, lambda: self.fish_counter_label.config(text=f'🐟 Fish: {self.fish_count}'))
        except Exception:
            pass
        self.log(f'🐟 Fish caught: {self.fish_count}', "important")
        
                                    
        self.update_bait_status_display()
        
                          
        self.root.after(0, lambda: self.update_stats_display())
        
                                         
        if self.webhook_enabled and self.webhook_counter >= self.webhook_interval:
            if self.fish_progress_webhook_enabled and self.webhook_manager:
                self.webhook_manager.send_fishing_progress()
            self.webhook_counter = 0

    def reset_fish_counter(self):
        """Reset fish counter when main loop starts"""
        self.fish_count = 0
        self.webhook_counter = 0
        try:
            self.root.after(0, lambda: self.fish_counter_label.config(text=f'🐟 Fish: {self.fish_count}'))
        except Exception:
            pass
    




    def update_stats_display(self):
        """Update the stats display labels with current values"""
        try:
            if not hasattr(self, 'total_fish_stat'):
                return
                
                                    
            self.total_fish_stat.config(text=f'Total Fish Caught\n{self.fish_count}')
            
                                        
            devil_fruits = len(getattr(self, 'devil_fruits_caught', []))
            self.fruits_caught_stat.config(text=f'Devil Fruits Found\n{devil_fruits}')
            
                                   
            if self.start_time:
                if self.is_paused:
                    elapsed = (self.pause_time - self.start_time) - self.total_paused_time
                else:
                    current_time = time.time()
                    elapsed = (current_time - self.start_time) - self.total_paused_time
                
                hours = int(elapsed) // 3600
                minutes = (int(elapsed) % 3600) // 60
                seconds = int(elapsed) % 60
                time_str = f'{hours:02d}:{minutes:02d}:{seconds:02d}'
            else:
                time_str = '00:00:00'
            
            self.session_time_stat.config(text=f'Session Time\n{time_str}')
            
                                       
            bait_purchased = getattr(self, 'bait_purchased', 0)
            self.bait_used_stat.config(text=f'Bait Purchased\n{bait_purchased}')
        except Exception as e:
            pass

    def schedule_periodic_update(self):
        """Schedule the periodic stats update to run every second"""
        try:
            self.periodic_update()
        except Exception as e:
            pass
    
    def periodic_update(self):
        """Update stats every second to keep session time fresh"""
        try:
            if self.main_loop_active and self.start_time:
                self.update_stats_display()
        except Exception as e:
            pass
        finally:
                                         
            self.root.after(1000, self.periodic_update)
    
    def update_bait_status_display(self):
        """Update bait status display"""
                                                       
        pass

    def check_and_purchase(self):
        """Check if we need to auto-purchase and run sequence if needed"""            
        if getattr(self, 'auto_purchase_var', None) and self.auto_purchase_var.get():
            self.purchase_counter += 1
            loops_needed = int(getattr(self, 'loops_per_purchase', 1)) if getattr(self, 'loops_per_purchase', None) is not None else 1
            print(f'🔄 Purchase counter: {self.purchase_counter}/{loops_needed}')
            if self.purchase_counter >= max(1, loops_needed):
                try:
                    self.perform_auto_purchase_sequence()
                    self.purchase_counter = 0
                except Exception as e:
                    print(f'❌ AUTO-PURCHASE ERROR: {e}')

    def cast_line(self):
        """Perform the casting action: hold click for 1 second then release"""
        self.log('Casting line...', "verbose")
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        threading.Event().wait(1.0)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        self.is_clicking = False
        
                                  
        self.last_activity_time = time.time()
        
        self.log('Line cast', "verbose")

    def main_loop(self):
        """Main loop that runs when activated - delegates to fishing bot"""
        self.fishing_bot.run_main_loop()
    

    
    def set_recovery_state(self, state, details=None):
        """Update current state for smart recovery tracking"""
        self.current_state = state
        self.state_start_time = time.time()
        self.last_activity_time = time.time()
        self.state_details = details or {}
        
                                 
        if self.dev_mode or self.verbose_logging:
            detail_str = f" - {details}" if details else ""
            self.log(f'🔄 State: {state}{detail_str}', "verbose")
    

    
    def update_runtime_timer(self):
        """Update the runtime display"""
        if not self.main_loop_active and not self.is_paused:
            return
            
        if self.start_time:
            current_time = time.time()
            if self.is_paused and self.pause_time:
                                                           
                elapsed = (self.pause_time - self.start_time) - self.total_paused_time
            else:
                                                                   
                elapsed = (current_time - self.start_time) - self.total_paused_time
            
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)
            
            runtime_text = f'⏱️ Runtime: {hours:02d}:{minutes:02d}:{seconds:02d}'
            
            try:
                self.root.after(0, lambda: self.runtime_label.config(text=runtime_text))
            except Exception:
                pass
        
                                              
        if self.main_loop_active or self.is_paused:
            self.root.after(1000, self.update_runtime_timer)




    def exit_app(self):
        """Exit the application"""
        print('Exiting application...')
        self.main_loop_active = False
        
                                        
        try:
            self.auto_save_settings()
        except Exception as e:
            print(f"Error saving settings: {e}")



                                             
        if hasattr(self, 'overlay_manager_bar') and self.overlay_manager_bar.window:
            try:
                self.overlay_manager_bar.destroy()
            except Exception:
                pass
        if hasattr(self, 'overlay_manager_drop') and self.overlay_manager_drop.window:
            try:
                self.overlay_manager_drop.destroy()
            except Exception:
                pass

                                    
        try:
            keyboard.unhook_all()
        except Exception:
            pass

                                  
        try:
            self.root.quit()                 
            self.root.destroy()                  
        except Exception as e:
            print(f"Error destroying window: {e}")
        
                    
        import os
        os._exit(0)

    def create_auto_purchase_section(self, start_row):
        """Create the auto purchase collapsible section"""
        section = CollapsibleFrame(self.main_frame, "🛒 Auto Purchase Settings", start_row)
        self.collapsible_sections['auto_purchase'] = section
        frame = section.get_content_frame()
        
                                       
        frame.columnconfigure((0, 1, 2, 3), weight=1)
        
                              
        row = 0
        ttk.Label(frame, text='Active:').grid(row=row, column=0, sticky='e', pady=5, padx=(0, 10))
        self.auto_purchase_var = tk.BooleanVar(value=False)
        auto_check = ttk.Checkbutton(frame, variable=self.auto_purchase_var, text='Enabled')
        auto_check.grid(row=row, column=1, pady=5, sticky='w')
        help_btn = ttk.Button(frame, text='?', width=3)
        help_btn.grid(row=row, column=2, padx=(10, 0), pady=5)
        ToolTip(help_btn, "Automatically buy bait after catching fish. Requires setting Points 1-3.")
                                                 
        self.auto_purchase_var.trace_add('write', lambda *args: self.auto_save_settings())
        row += 1
        
                         
        ttk.Label(frame, text='Amount:').grid(row=row, column=0, sticky='e', pady=5, padx=(0, 10))
        self.amount_var = tk.IntVar(value=10)
        amount_spinbox = ttk.Spinbox(frame, from_=0, to=1000000, increment=1, textvariable=self.amount_var, width=10)
        amount_spinbox.grid(row=row, column=1, pady=5, sticky='w')
                                       
        self.amount_var.trace_add('write', lambda *args: self.auto_save_settings())
        help_btn = ttk.Button(frame, text='?', width=3)
        help_btn.grid(row=row, column=2, padx=(10, 0), pady=5)
        ToolTip(help_btn, "How much bait to buy each time (e.g., 10 = buy 10 bait)")
        def update_amount(*args):
            try:
                self.auto_purchase_amount = self.amount_var.get()
            except (tk.TclError, ValueError):
                pass                                  
        self.amount_var.trace_add('write', update_amount)
        try:
            self.auto_purchase_amount = self.amount_var.get()
        except (tk.TclError, ValueError):
            self.auto_purchase_amount = 10
        row += 1
        
                            
        ttk.Label(frame, text='Loops per Purchase:').grid(row=row, column=0, sticky='e', pady=5, padx=(0, 10))
        self.loops_var = tk.IntVar(value=10)
        loops_spinbox = ttk.Spinbox(frame, from_=1, to=1000000, increment=1, textvariable=self.loops_var, width=10)
        loops_spinbox.grid(row=row, column=1, pady=5, sticky='w')
        help_btn = ttk.Button(frame, text='?', width=3)
        help_btn.grid(row=row, column=2, padx=(10, 0), pady=5)
        ToolTip(help_btn, "Buy bait every X fish caught (e.g., 10 = buy bait after every 10 fish)")
        def update_loops(*args):
            try:
                self.loops_per_purchase = self.loops_var.get()
            except (tk.TclError, ValueError):
                pass                                  
        self.loops_var.trace_add('write', update_loops)
                                                   
        self.loops_var.trace_add('write', lambda *args: self.auto_save_settings())
        try:
            self.loops_per_purchase = self.loops_var.get()
        except (tk.TclError, ValueError):
            self.loops_per_purchase = 10
        row += 1
        
                                         
        self.point_buttons = {}
                                                                                  
        if not hasattr(self, 'point_coords'):
            self.point_coords = {1: None, 2: None, 3: None}
        
        for i in range(1, 4):
            ttk.Label(frame, text=f'Point {i}:').grid(row=row, column=0, sticky='e', pady=5, padx=(0, 10))
            self.point_buttons[i] = ttk.Button(frame, text=f'Point {i}', command=lambda idx=i: self.capture_mouse_click(idx))
            self.point_buttons[i].grid(row=row, column=1, pady=5, sticky='w')
            help_btn = ttk.Button(frame, text='?', width=3)
            help_btn.grid(row=row, column=2, padx=(10, 0), pady=5)
            
            tooltips = {
                1: "Click to set: yes/buy button (same area)",
                2: "Click to set: Input amount area (also ... area)", 
                3: "Click to set: Close button"
            }
            ToolTip(help_btn, tooltips[i])
            row += 1

    def create_auto_bait_section(self, start_row):
        """Create the simplified auto bait section"""
        section = CollapsibleFrame(self.main_frame, "🎣 Auto Bait Selection", start_row)
        self.collapsible_sections['auto_bait'] = section
        frame = section.get_content_frame()
        
                                                    
        frame.grid_columnconfigure(1, weight=1)
        
        row = 0
        
                                    
        ttk.Label(frame, text='Active:').grid(row=row, column=0, sticky='e', pady=5, padx=(0, 10))
        self.auto_bait_var = tk.BooleanVar(value=getattr(self, 'auto_bait_enabled', False))
        bait_check = ttk.Checkbutton(frame, variable=self.auto_bait_var, text='Enabled')
        bait_check.grid(row=row, column=1, pady=5, sticky='w')
        help_btn = ttk.Button(frame, text='?', width=3)
        help_btn.grid(row=row, column=2, padx=(10, 0), pady=5)
        ToolTip(help_btn, "Automatically select top bait before every rod throw")
        self.auto_bait_var.trace_add('write', lambda *args: (setattr(self, 'auto_bait_enabled', self.auto_bait_var.get()), self.auto_save_settings()))
        row += 1
        
                                  
        ttk.Label(frame, text='Top Bait Location:').grid(row=row, column=0, sticky='e', pady=5, padx=(0, 10))
        self.top_bait_button = ttk.Button(frame, text='Set Top Bait Position', 
                                        command=lambda: self.set_bait_point('top_bait'))
        self.top_bait_button.grid(row=row, column=1, pady=5, sticky='w')
        help_btn = ttk.Button(frame, text='?', width=3)
        help_btn.grid(row=row, column=2, padx=(10, 0), pady=5)
        ToolTip(help_btn, "Click to set the position of the top bait in the menu")
        row += 1
        
                      
        instructions = ttk.Label(frame, text='Instructions:', font=('TkDefaultFont', 9, 'bold'))
        instructions.grid(row=row, column=0, columnspan=3, pady=(10, 2), sticky='w')
        row += 1
        
        instruction_text = ("1. Set the top bait position (where the best bait appears)\n"
                          "2. System will click this position before every rod throw\n"
                          "3. Works with any bait type - always selects top available\n"
                          "4. Auto purchase continues to work independently")
        ttk.Label(frame, text=instruction_text, 
                 font=('TkDefaultFont', 8), foreground='gray').grid(row=row, column=0, columnspan=3, pady=2, sticky='w')
        


    def create_fruit_storage_section(self, start_row):
        """Create the fruit storage collapsible section"""
        section = CollapsibleFrame(self.main_frame, "🍎 Fruit Storage Settings", start_row)
        self.collapsible_sections['fruit_storage'] = section
        frame = section.get_content_frame()
        
                                                          
        frame.columnconfigure((0, 1, 2, 3), weight=1)
        
        row = 0
        
                                        
        ttk.Label(frame, text='Active:').grid(row=row, column=0, sticky='e', pady=5, padx=(0, 10))
        self.fruit_storage_var = tk.BooleanVar(value=getattr(self, 'fruit_storage_enabled', False))
        fruit_check = ttk.Checkbutton(frame, variable=self.fruit_storage_var, text='Enabled')
        fruit_check.grid(row=row, column=1, pady=5, sticky='w')
        help_btn = ttk.Button(frame, text='?', width=3)
        help_btn.grid(row=row, column=2, padx=(10, 0), pady=5)
        ToolTip(help_btn, "Automatically store fruits in inventory slot after fishing")
        self.fruit_storage_var.trace_add('write', lambda *args: (setattr(self, 'fruit_storage_enabled', self.fruit_storage_var.get()), self.auto_save_settings()))
        row += 1
        
                             
        ttk.Label(frame, text='Fruit Key 1:').grid(row=row, column=0, sticky='e', pady=5, padx=(0, 10))
        self.fruit_key_var = tk.IntVar(value=int(getattr(self, 'fruit_storage_key', '2')))
        fruit_key_spinbox = ttk.Spinbox(frame, from_=1, to=9, increment=1, textvariable=self.fruit_key_var, width=10)
        fruit_key_spinbox.grid(row=row, column=1, pady=5, sticky='w')
        help_btn = ttk.Button(frame, text='?', width=3)
        help_btn.grid(row=row, column=2, padx=(10, 0), pady=5)
        ToolTip(help_btn, "Select which key (1-9) to press for first fruit storage")
        self.fruit_key_var.trace_add('write', lambda *args: (setattr(self, 'fruit_storage_key', str(self.fruit_key_var.get())), self.auto_save_settings()))
        row += 1
        
                             
        ttk.Label(frame, text='Fruit Key 2:').grid(row=row, column=0, sticky='e', pady=5, padx=(0, 10))
        self.fruit_key_2_var = tk.IntVar(value=int(getattr(self, 'fruit_storage_key_2', '3')))
        fruit_key_2_spinbox = ttk.Spinbox(frame, from_=1, to=9, increment=1, textvariable=self.fruit_key_2_var, width=10)
        fruit_key_2_spinbox.grid(row=row, column=1, pady=5, sticky='w')
        help_btn = ttk.Button(frame, text='?', width=3)
        help_btn.grid(row=row, column=2, padx=(10, 0), pady=5)
        ToolTip(help_btn, "Select which key (1-9) to press for second fruit storage")
        self.fruit_key_2_var.trace_add('write', lambda *args: (setattr(self, 'fruit_storage_key_2', str(self.fruit_key_2_var.get())), self.auto_save_settings()))
        row += 1
        
                     
        ttk.Label(frame, text='Fruit Point:').grid(row=row, column=0, sticky='e', pady=5, padx=(0, 10))
        self.fruit_point_button = ttk.Button(frame, text='Fruit Point',
                                            command=lambda: self.capture_mouse_click('fruit_point'))
        self.fruit_point_button.grid(row=row, column=1, pady=5, sticky='w')
        help_btn = ttk.Button(frame, text='?', width=3)
        help_btn.grid(row=row, column=2, padx=(10, 0), pady=5)
        ToolTip(help_btn, "Click to set where to click for fruit selection (Store button)")
        row += 1
        
                                
        ttk.Label(frame, text='Fruit Point 2:').grid(row=row, column=0, sticky='e', pady=5, padx=(0, 10))
        self.fruit_point_2_button = ttk.Button(frame, text='Fruit Point 2',
                                            command=lambda: self.capture_mouse_click('fruit_point_2'))
        self.fruit_point_2_button.grid(row=row, column=1, pady=5, sticky='w')
        help_btn = ttk.Button(frame, text='?', width=3)
        help_btn.grid(row=row, column=2, padx=(10, 0), pady=5)
        ToolTip(help_btn, "Optional: Backup click point to help trigger hover detection")
        row += 1
        
                 
        ttk.Label(frame, text='Rod Key:').grid(row=row, column=0, sticky='e', pady=5, padx=(0, 10))
        self.rod_key_var = tk.IntVar(value=int(getattr(self, 'rod_key', '1')))
        rod_key_spinbox = ttk.Spinbox(frame, from_=1, to=9, increment=1, textvariable=self.rod_key_var, width=10)
        rod_key_spinbox.grid(row=row, column=1, pady=5, sticky='w')
        help_btn = ttk.Button(frame, text='?', width=3)
        help_btn.grid(row=row, column=2, padx=(10, 0), pady=5)
        ToolTip(help_btn, "Select which key (1-9) to press for rod selection")
        self.rod_key_var.trace_add('write', lambda *args: (setattr(self, 'rod_key', str(self.rod_key_var.get())), self.auto_save_settings()))
        row += 1
        
                    
        ttk.Label(frame, text='Bait Point:').grid(row=row, column=0, sticky='e', pady=5, padx=(0, 10))
        self.bait_point_button = ttk.Button(frame, text='Bait Point',
                                           command=lambda: self.capture_mouse_click('bait_point'))
        self.bait_point_button.grid(row=row, column=1, pady=5, sticky='w')
        help_btn = ttk.Button(frame, text='?', width=3)
        help_btn.grid(row=row, column=2, padx=(10, 0), pady=5)
        ToolTip(help_btn, "Click to set where to click for bait selection")





    def create_hotkeys_section(self, start_row):
        """Create the hotkey bindings collapsible section"""
        section = CollapsibleFrame(self.main_frame, "⌨️ Hotkey Bindings", start_row)
                                    
        section.is_expanded = False
        section.content_frame.pack_forget()
        section.toggle_btn.config(text='+')
        self.collapsible_sections['hotkeys'] = section
        frame = section.get_content_frame()
        
                                       
        frame.columnconfigure((0, 1, 2, 3), weight=1)
        
        row = 0
        ttk.Label(frame, text='Toggle Main Loop:').grid(row=row, column=0, sticky='e', pady=5, padx=(0, 10))
        self.loop_key_label = ttk.Label(frame, text=self.hotkeys['toggle_loop'].upper(), relief=tk.RIDGE, padding=5, width=10)
        self.loop_key_label.grid(row=row, column=1, pady=5)
        self.loop_rebind_btn = ttk.Button(frame, text='Rebind', command=lambda: self.start_rebind('toggle_loop'))
        self.loop_rebind_btn.grid(row=row, column=2, padx=(10, 0), pady=5)
        help_btn = ttk.Button(frame, text='?', width=3)
        help_btn.grid(row=row, column=3, padx=(10, 0), pady=5)
        ToolTip(help_btn, "Start/stop the fishing bot")
        row += 1
        
        ttk.Label(frame, text='Toggle Layout:').grid(row=row, column=0, sticky='e', pady=5, padx=(0, 10))
        self.layout_key_label = ttk.Label(frame, text=self.hotkeys['toggle_layout'].upper(), relief=tk.RIDGE, padding=5, width=10)
        self.layout_key_label.grid(row=row, column=1, pady=5)
        self.layout_rebind_btn = ttk.Button(frame, text='Rebind', command=lambda: self.start_rebind('toggle_layout'))
        self.layout_rebind_btn.grid(row=row, column=2, padx=(10, 0), pady=5)
        help_btn = ttk.Button(frame, text='?', width=3)
        help_btn.grid(row=row, column=3, padx=(10, 0), pady=5)
        ToolTip(help_btn, "Switch between Bar Layout (blue) and Drop Layout (green)")
        row += 1
        

        
        ttk.Label(frame, text='Exit:').grid(row=row, column=0, sticky='e', pady=5, padx=(0, 10))
        self.exit_key_label = ttk.Label(frame, text=self.hotkeys['exit'].upper(), relief=tk.RIDGE, padding=5, width=10)
        self.exit_key_label.grid(row=row, column=1, pady=5)
        self.exit_rebind_btn = ttk.Button(frame, text='Rebind', command=lambda: self.start_rebind('exit'))
        self.exit_rebind_btn.grid(row=row, column=2, padx=(10, 0), pady=5)
        help_btn = ttk.Button(frame, text='?', width=3)
        help_btn.grid(row=row, column=3, padx=(10, 0), pady=5)
        ToolTip(help_btn, "Close the application completely")
        row += 1
        
        ttk.Label(frame, text='Toggle Minimize:').grid(row=row, column=0, sticky='e', pady=5, padx=(0, 10))
        self.minimize_key_label = ttk.Label(frame, text=self.hotkeys['toggle_minimize'].upper(), relief=tk.RIDGE, padding=5, width=10)
        self.minimize_key_label.grid(row=row, column=1, pady=5)
        self.minimize_rebind_btn = ttk.Button(frame, text='Rebind', command=lambda: self.start_rebind('toggle_minimize'))
        self.minimize_rebind_btn.grid(row=row, column=2, padx=(10, 0), pady=5)
        help_btn = ttk.Button(frame, text='?', width=3)
        help_btn.grid(row=row, column=3, padx=(10, 0), pady=5)
        ToolTip(help_btn, "Toggle between minimized and normal window")

    def create_webhook_section(self, start_row):
        """Create the Discord webhook collapsible section"""
        section = CollapsibleFrame(self.main_frame, "🔗 Discord Webhook", start_row)
        self.collapsible_sections['webhook'] = section
        frame = section.get_content_frame()
        
                                       
        frame.columnconfigure((0, 1, 2, 3), weight=1)
        
        row = 0
                                 
        self.webhook_enabled_var = tk.BooleanVar(value=self.webhook_enabled)
        webhook_check = ttk.Checkbutton(frame, text='Enable Discord Webhook', variable=self.webhook_enabled_var, command=self.auto_save_settings)
        webhook_check.grid(row=row, column=0, columnspan=2, pady=5)
        help_btn = ttk.Button(frame, text='?', width=3)
        help_btn.grid(row=row, column=2, padx=(10, 0), pady=5)
        ToolTip(help_btn, "Send fishing progress updates to Discord")
        self.webhook_enabled_var.trace_add('write', lambda *args: (setattr(self, 'webhook_enabled', self.webhook_enabled_var.get()), self.auto_save_settings()))
        row += 1
        
                     
        ttk.Label(frame, text='Webhook URL:').grid(row=row, column=0, sticky='e', pady=5, padx=(0, 10))
        self.webhook_url_var = tk.StringVar(value=self.webhook_url)
        webhook_entry = ttk.Entry(frame, textvariable=self.webhook_url_var, width=25)
        webhook_entry.grid(row=row, column=1, sticky='ew', pady=5)
        help_btn = ttk.Button(frame, text='?', width=3)
        help_btn.grid(row=row, column=2, padx=(10, 0), pady=5)
        ToolTip(help_btn, "Discord webhook URL from your server settings")
        self.webhook_url_var.trace_add('write', lambda *args: (setattr(self, 'webhook_url', self.webhook_url_var.get()), self.auto_save_settings()))
        row += 1
        
                          
        ttk.Label(frame, text='Send Every X Fish:').grid(row=row, column=0, sticky='e', pady=5, padx=(0, 10))
        self.webhook_interval_var = tk.IntVar(value=self.webhook_interval)
        interval_spinbox = ttk.Spinbox(frame, from_=1, to=100, textvariable=self.webhook_interval_var, width=10)
        interval_spinbox.grid(row=row, column=1, pady=5, sticky='w')
        help_btn = ttk.Button(frame, text='?', width=3)
        help_btn.grid(row=row, column=2, padx=(10, 0), pady=5)
        ToolTip(help_btn, "Send webhook message every X fish caught (e.g., 10 = message every 10 fish)")
        self.webhook_interval_var.trace_add('write', lambda *args: (setattr(self, 'webhook_interval', self.webhook_interval_var.get()), self.auto_save_settings()))
        row += 1
        
                                           
        ttk.Label(frame, text='Notification Types:', font=('TkDefaultFont', 9, 'bold')).grid(row=row, column=0, columnspan=3, pady=(10, 5), sticky='w')
        row += 1
        
                                     
        self.fish_progress_webhook_var = tk.BooleanVar(value=getattr(self, 'fish_progress_webhook_enabled', True))
        fish_progress_check = ttk.Checkbutton(frame, text='🐟 Fish Progress Updates', variable=self.fish_progress_webhook_var, command=self.auto_save_settings)
        fish_progress_check.grid(row=row, column=0, columnspan=2, pady=2, sticky='w')
        help_btn = ttk.Button(frame, text='?', width=3)
        help_btn.grid(row=row, column=2, padx=(10, 0), pady=2)
        ToolTip(help_btn, "Send notifications every X fish caught (based on interval above)")
        self.fish_progress_webhook_var.trace_add('write', lambda *args: (setattr(self, 'fish_progress_webhook_enabled', self.fish_progress_webhook_var.get()), self.auto_save_settings()))
        row += 1
        
                                           
        self.devil_fruit_webhook_var = tk.BooleanVar(value=getattr(self, 'devil_fruit_webhook_enabled', True))
        devil_fruit_check = ttk.Checkbutton(frame, text='🍎 Devil Fruit Catch Alerts', variable=self.devil_fruit_webhook_var, command=self.auto_save_settings)
        devil_fruit_check.grid(row=row, column=0, columnspan=2, pady=2, sticky='w')
        help_btn = ttk.Button(frame, text='?', width=3)
        help_btn.grid(row=row, column=2, padx=(10, 0), pady=2)
        ToolTip(help_btn, "Send Discord notifications when devil fruits are caught while fishing")
        self.devil_fruit_webhook_var.trace_add('write', lambda *args: (setattr(self, 'devil_fruit_webhook_enabled', self.devil_fruit_webhook_var.get()), self.auto_save_settings()))
        row += 1
        
                                                       
                                           
                                                                                                                
                                                                                                                              
                                                                                     
                                                         
                                                                
                                                                                              
                                                                                                                                                                                      
                  
        
                                     
        self.purchase_webhook_var = tk.BooleanVar(value=getattr(self, 'purchase_webhook_enabled', True))
        purchase_check = ttk.Checkbutton(frame, text='🛒 Auto Purchase Alerts', variable=self.purchase_webhook_var, command=self.auto_save_settings)
        purchase_check.grid(row=row, column=0, columnspan=2, pady=2, sticky='w')
        help_btn = ttk.Button(frame, text='?', width=3)
        help_btn.grid(row=row, column=2, padx=(10, 0), pady=2)
        ToolTip(help_btn, "Send notifications when auto purchase completes")
        self.purchase_webhook_var.trace_add('write', lambda *args: (setattr(self, 'purchase_webhook_enabled', self.purchase_webhook_var.get()), self.auto_save_settings()))
        row += 1
        
                                      
        self.recovery_webhook_var = tk.BooleanVar(value=getattr(self, 'recovery_webhook_enabled', True))
        recovery_check = ttk.Checkbutton(frame, text='🔄 Recovery/Error Alerts', variable=self.recovery_webhook_var, command=self.auto_save_settings)
        recovery_check.grid(row=row, column=0, columnspan=2, pady=2, sticky='w')
        help_btn = ttk.Button(frame, text='?', width=3)
        help_btn.grid(row=row, column=2, padx=(10, 0), pady=2)
        ToolTip(help_btn, "Send notifications when bot recovers from errors or gets stuck")
        self.recovery_webhook_var.trace_add('write', lambda *args: (setattr(self, 'recovery_webhook_enabled', self.recovery_webhook_var.get()), self.auto_save_settings()))
        row += 1
        
                                       
        self.bait_webhook_var = tk.BooleanVar(value=getattr(self, 'bait_webhook_enabled', True))
        bait_check = ttk.Checkbutton(frame, text='🎣 Bait Management Alerts', variable=self.bait_webhook_var, command=self.auto_save_settings)
        bait_check.grid(row=row, column=0, columnspan=2, pady=2, sticky='w')
        help_btn = ttk.Button(frame, text='?', width=3)
        help_btn.grid(row=row, column=2, padx=(10, 0), pady=2)
        ToolTip(help_btn, "Send notifications when bait runs out and auto purchase is triggered")
        self.bait_webhook_var.trace_add('write', lambda *args: (setattr(self, 'bait_webhook_enabled', self.bait_webhook_var.get()), self.auto_save_settings()))
        row += 1
        
                             
        test_btn = ttk.Button(frame, text='Test Webhook', command=self.test_webhook)
        test_btn.grid(row=row, column=0, columnspan=2, pady=10)
        help_btn = ttk.Button(frame, text='?', width=3)
        help_btn.grid(row=row, column=2, padx=(10, 0), pady=5)
        ToolTip(help_btn, "Send a test message to verify webhook is working")



    def create_startup_section(self, start_row):
        """Create the Auto Setup settings section"""
        section = CollapsibleFrame(self.main_frame, "🚀 Auto Setup Settings", start_row)
                                    
        section.is_expanded = False
        section.toggle()
        self.collapsible_sections['zoom'] = section
        frame = section.get_content_frame()
        
        row = 0
        
                                    
                                                                   
        zoom_default = getattr(self, 'auto_zoom_enabled', False)
        self.auto_zoom_var = tk.BooleanVar(value=zoom_default)
        zoom_check = ttk.Checkbutton(frame, text="Enable Auto Zoom on Startup", 
                                    variable=self.auto_zoom_var,
                                    command=self.auto_save_settings)
        zoom_check.grid(row=row, column=0, sticky='w', pady=2)
        ToolTip(zoom_check, "Automatically zoom out when fishing starts for better visibility")
        self.auto_zoom_var.trace_add('write', lambda *args: self._sync_auto_zoom_var())
        
        row += 1
        
        mouse_default = getattr(self, 'auto_mouse_position_enabled', False)
        self.auto_mouse_position_var = tk.BooleanVar(value=mouse_default)
        mouse_check = ttk.Checkbutton(frame, text="Enable Auto Mouse Position on Startup",
                                     variable=self.auto_mouse_position_var,
                                     command=self.auto_save_settings)
        mouse_check.grid(row=row, column=0, sticky='w', pady=2)
        ToolTip(mouse_check, "Automatically move mouse to fishing location when fishing starts")
        self.auto_mouse_position_var.trace_add('write', lambda *args: self._sync_auto_mouse_position_var())
        
        row += 1
        
                                                    
        self.zoom_out_var = tk.IntVar(value=getattr(self, 'zoom_out_steps', 5))
        self.zoom_in_var = tk.IntVar(value=getattr(self, 'zoom_in_steps', 8))
        
                                                       
        self.zoom_out_var.trace_add('write', lambda *args: (setattr(self, 'zoom_out_steps', self.zoom_out_var.get()), self.auto_save_settings()))
        self.zoom_in_var.trace_add('write', lambda *args: (setattr(self, 'zoom_in_steps', self.zoom_in_var.get()), self.auto_save_settings()))
        
        row += 1
        


    def create_discord_section(self, start_row):
        """Create the Discord join section at the bottom"""
        discord_frame = ttk.Frame(self.main_frame)
        discord_frame.grid(row=start_row, column=0, sticky='ew', pady=(25, 10))
        discord_frame.columnconfigure(0, weight=1)
        
                                                                  
        discord_btn = ttk.Button(discord_frame, text='💬 Join our Discord!', 
                               command=self.open_discord)
        
        discord_btn.pack(pady=5, padx=10, fill='x')
        
                                                      
        ToolTip(discord_btn, "Click to join our Discord community!")

    def open_settings_window(self):
        """Open modern settings window with timing and theme options"""
        if hasattr(self, 'settings_window') and self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.lift()
            return
        
        self.settings_window = tk.Toplevel(self.root)
        self.settings_window.title('⚙️ Settings')
        self.settings_window.geometry('700x750')
        self.settings_window.attributes('-topmost', True)
        self.settings_window.resizable(False, False)
        
                                                       
        theme_colors = self.theme_manager.themes[self.current_theme]["colors"]
        self.settings_window.configure(bg=theme_colors["bg"])
        
                                                                    
        style = ttk.Style()
        
                      
        style.configure('Settings.TFrame', 
                       background=theme_colors["bg"],
                       relief='flat')
        
                        
        style.configure('Settings.TLabel',
                       background=theme_colors["bg"],
                       foreground=theme_colors["fg"],
                       font=('Segoe UI', 9))
        
                             
        style.configure('SectionTitle.TLabel',
                       background=theme_colors["bg"],
                       foreground=theme_colors["accent"],
                       font=('Segoe UI', 10, 'bold'))
        
                        
        style.configure('Subtitle.TLabel',
                       background=theme_colors["bg"],
                       foreground=theme_colors["accent"],
                       font=('Segoe UI', 9, 'bold'))
        
                                          
        style.configure('Settings.TLabelFrame',
                       background=theme_colors["bg"],
                       foreground=theme_colors["accent"],
                       relief='solid',
                       borderwidth=1,
                       bordercolor=theme_colors["accent"])
        style.configure('Settings.TLabelFrame.Label',
                       background=theme_colors["bg"],
                       foreground=theme_colors["accent"],
                       font=('Segoe UI', 11, 'bold'))
        
                       
        style.configure('Settings.TButton',
                       background=theme_colors["button_bg"],
                       foreground=theme_colors["fg"],
                       borderwidth=1,
                       relief='flat',
                       font=('Segoe UI', 9))
        style.map('Settings.TButton',
                 background=[('active', theme_colors["button_hover"])])
        
                        
        style.configure('Settings.TSpinbox',
                       fieldbackground=theme_colors["button_bg"],
                       background=theme_colors["button_bg"],
                       foreground=theme_colors["fg"],
                       bordercolor=theme_colors["accent"],
                       insertcolor=theme_colors["fg"],
                       font=('Segoe UI', 9))
        
                          
        style.configure('Settings.TSeparator',
                       background=theme_colors["accent"])
        
                                                             
        main_container = ttk.Frame(self.settings_window, style='Settings.TFrame')
        main_container.pack(fill='both', expand=True, padx=15, pady=15)
        
                                       
        top_frame = ttk.Frame(main_container, style='Settings.TFrame')
        top_frame.pack(fill='x', pady=(0, 20))
        top_frame.columnconfigure(1, weight=1)
        
                               
        title_label = ttk.Label(top_frame, text='⚙️ Settings', style='SectionTitle.TLabel')
        title_label.grid(row=0, column=0, sticky='w')
        
                                     
        close_btn = ttk.Button(top_frame, text='✕ Close', command=self.settings_window.destroy, 
                              style='Settings.TButton')
        close_btn.grid(row=0, column=2, sticky='e')
        
                                         
        content_frame = ttk.Frame(main_container, style='Settings.TFrame')
        content_frame.pack(fill='both', expand=True)
        
                                  
        self.create_simple_timing_section(content_frame, theme_colors)
        self.create_simple_presets_section(content_frame, theme_colors)
    
    def create_simple_timing_section(self, parent, theme_colors):
        """Create simplified timing settings section"""
                                 
        timing_frame = tk.LabelFrame(parent, text="⏱️ Timing Settings", 
                                    bg=theme_colors["bg"], fg=theme_colors["accent"],
                                    font=('Segoe UI', 11, 'bold'), padx=20, pady=15)
        timing_frame.pack(fill='x', padx=10, pady=(0, 20))
        
                                
        pd_label = tk.Label(timing_frame, text="🎛️ PD Controller", 
                           bg=theme_colors["bg"], fg=theme_colors["accent"],
                           font=('Segoe UI', 10, 'bold'))
        pd_label.grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 10))
        
                    
        kp_label = tk.Label(timing_frame, text="Proportional Gain (KP):", 
                           bg=theme_colors["bg"], fg=theme_colors["fg"])
        kp_label.grid(row=1, column=0, sticky='w', pady=2)
        
        self.kp_var = tk.DoubleVar(value=getattr(self, 'kp', 0.2))
        kp_spinbox = tk.Spinbox(timing_frame, from_=0.01, to=1.0, increment=0.01, 
                               textvariable=self.kp_var, width=15,
                               bg=theme_colors["button_bg"], fg=theme_colors["fg"],
                               insertbackground=theme_colors["fg"], selectbackground=theme_colors["accent"],
                               selectforeground=theme_colors["bg"], relief='flat', bd=1,
                               highlightthickness=1, highlightcolor=theme_colors["accent"],
                               highlightbackground=theme_colors["button_bg"])
        kp_spinbox.grid(row=1, column=1, sticky='e', padx=(10, 0), pady=2)
        self.kp_var.trace_add('write', lambda *args: (setattr(self, 'kp', self.kp_var.get()), self.auto_save_settings()))
        
                    
        kd_label = tk.Label(timing_frame, text="Derivative Gain (KD):", 
                           bg=theme_colors["bg"], fg=theme_colors["fg"])
        kd_label.grid(row=2, column=0, sticky='w', pady=2)
        
        self.kd_var = tk.DoubleVar(value=getattr(self, 'kd', 0.6))
        kd_spinbox = tk.Spinbox(timing_frame, from_=0.01, to=2.0, increment=0.01, 
                               textvariable=self.kd_var, width=15,
                               bg=theme_colors["button_bg"], fg=theme_colors["fg"],
                               insertbackground=theme_colors["fg"], selectbackground=theme_colors["accent"],
                               selectforeground=theme_colors["bg"], relief='flat', bd=1,
                               highlightthickness=1, highlightcolor=theme_colors["accent"],
                               highlightbackground=theme_colors["button_bg"])
        kd_spinbox.grid(row=2, column=1, sticky='e', padx=(10, 0), pady=2)
        self.kd_var.trace_add('write', lambda *args: (setattr(self, 'kd', self.kd_var.get()), self.auto_save_settings()))
        
                          
        timeout_label = tk.Label(timing_frame, text="⏰ Timeout Settings", 
                                bg=theme_colors["bg"], fg=theme_colors["accent"],
                                font=('Segoe UI', 10, 'bold'))
        timeout_label.grid(row=3, column=0, columnspan=2, sticky='w', pady=(15, 10))
        
                      
        scan_label = tk.Label(timing_frame, text="Fish Detection Timeout (s):", 
                             bg=theme_colors["bg"], fg=theme_colors["fg"])
        scan_label.grid(row=4, column=0, sticky='w', pady=2)
        
        self.scan_timeout_var = tk.DoubleVar(value=getattr(self, 'scan_timeout', 15.0))
        scan_spinbox = tk.Spinbox(timing_frame, from_=5.0, to=60.0, increment=1.0, 
                                 textvariable=self.scan_timeout_var, width=15,
                                 bg=theme_colors["button_bg"], fg=theme_colors["fg"],
                                 insertbackground=theme_colors["fg"], selectbackground=theme_colors["accent"],
                                 selectforeground=theme_colors["bg"], relief='flat', bd=1,
                                 highlightthickness=1, highlightcolor=theme_colors["accent"],
                                 highlightbackground=theme_colors["button_bg"])
        scan_spinbox.grid(row=4, column=1, sticky='e', padx=(10, 0), pady=2)
        self.scan_timeout_var.trace_add('write', lambda *args: (setattr(self, 'scan_timeout', self.scan_timeout_var.get()), self.auto_save_settings()))
        
        timing_frame.columnconfigure(1, weight=1)

    def open_theme_window(self):
        """Open dedicated theme customization window"""
        if hasattr(self, 'theme_window') and self.theme_window and self.theme_window.winfo_exists():
            self.theme_window.lift()
            return
        
        self.theme_window = tk.Toplevel(self.root)
        self.theme_window.title('🎨 Theme Customization')
        self.theme_window.geometry('750x650')
        self.theme_window.attributes('-topmost', True)
        self.theme_window.resizable(False, False)
        
                                    
        theme_colors = self.theme_manager.themes[self.current_theme]["colors"]
        self.theme_window.configure(bg=theme_colors["bg"])
        
                        
        main_container = tk.Frame(self.theme_window, bg=theme_colors["bg"])
        main_container.pack(fill='both', expand=True, padx=20, pady=20)
        
                                                 
        top_frame = tk.Frame(main_container, bg=theme_colors["bg"])
        top_frame.pack(fill='x', pady=(0, 20))
        
        title_label = tk.Label(top_frame, text='🎨 Theme Customization', 
                              bg=theme_colors["bg"], fg=theme_colors["accent"],
                              font=('Segoe UI', 14, 'bold'))
        title_label.pack(side=tk.LEFT)
        
        close_btn = tk.Button(top_frame, text='✕ Close', 
                             bg=theme_colors["button_bg"], fg=theme_colors["fg"],
                             command=self.theme_window.destroy, relief='flat',
                             font=('Segoe UI', 9), cursor='hand2', padx=10, pady=5)
        close_btn.pack(side=tk.RIGHT)
        
                       
        content_frame = tk.Frame(main_container, bg=theme_colors["bg"])
        content_frame.pack(fill='both', expand=True)
        
                              
        self.create_theme_content(content_frame, theme_colors)
    
    def refresh_theme_window(self):
        """Refresh the theme window to show updated theme while preserving position"""
        try:
            if not (hasattr(self, 'theme_window') and self.theme_window):
                print("No theme window to refresh")
                return
                
            if not self.theme_window.winfo_exists():
                print("Theme window doesn't exist")
                return
            
                                          
            x = self.theme_window.winfo_x()
            y = self.theme_window.winfo_y()
            print(f"🔄 Refreshing theme window at position: x={x}, y={y}")
            
                                    
            self.theme_window.destroy()
            self.theme_window = None
            
                                                        
            self.root.update_idletasks()
            
                                                 
            self.open_theme_window()
            
                                                  
            if hasattr(self, 'theme_window') and self.theme_window:
                self.theme_window.update_idletasks()
                self.theme_window.geometry(f'+{x}+{y}')
                self.theme_window.lift()
                print(f"✅ Theme window refreshed successfully at x={x}, y={y}")
            else:
                print("❌ Failed to recreate theme window")
                
        except Exception as e:
            print(f"❌ Error in refresh_theme_window: {e}")
            import traceback
            traceback.print_exc()
    
    def create_theme_content(self, parent, theme_colors):
        """Create enhanced theme settings section with preview cards"""
                                
        theme_frame = tk.LabelFrame(parent, text="🎨 Theme Settings", 
                                   bg=theme_colors["bg"], fg=theme_colors["accent"],
                                   font=('Segoe UI', 11, 'bold'), padx=20, pady=15)
        theme_frame.pack(fill='x', padx=10, pady=(0, 20))
        
                                                             
        current_container = tk.Frame(theme_frame, bg=theme_colors["button_bg"], relief='flat', bd=2)
        current_container.grid(row=0, column=0, columnspan=3, sticky='ew', pady=(0, 20), padx=5)
        
                                
        current_theme_key = getattr(self, 'current_theme', 'red')
        current_theme_data = self.theme_manager.themes.get(current_theme_key, {})
        current_theme_name = current_theme_data.get('name', 'Unknown')
        current_theme_desc = current_theme_data.get('description', '')
        current_theme_colors = current_theme_data.get('colors', {})
        
                           
        left_frame = tk.Frame(current_container, bg=theme_colors["button_bg"])
        left_frame.pack(side='left', fill='both', expand=True, padx=15, pady=10)
        
        tk.Label(left_frame, text="✨ Active Theme:", 
                bg=theme_colors["button_bg"], fg=theme_colors["accent"],
                font=('Segoe UI', 11, 'bold')).pack(anchor='w')
        
        tk.Label(left_frame, text=current_theme_name, 
                bg=theme_colors["button_bg"], fg=theme_colors["fg"],
                font=('Segoe UI', 14, 'bold')).pack(anchor='w', pady=(2, 0))
        
        tk.Label(left_frame, text=current_theme_desc, 
                bg=theme_colors["button_bg"], fg=theme_colors["fg"],
                font=('Segoe UI', 8), wraplength=300).pack(anchor='w', pady=(5, 0))
        
                                    
        right_frame = tk.Frame(current_container, bg=theme_colors["button_bg"])
        right_frame.pack(side='right', padx=15, pady=10)
        
        tk.Label(right_frame, text="Colors:", 
                bg=theme_colors["button_bg"], fg=theme_colors["accent"],
                font=('Segoe UI', 9, 'bold')).pack()
        
        color_preview = tk.Frame(right_frame, bg=theme_colors["button_bg"])
        color_preview.pack(pady=5)
        
                               
        preview_colors = [
            (current_theme_colors.get('bg', '#000'), 'BG'),
            (current_theme_colors.get('accent', '#fff'), 'Accent'),
            (current_theme_colors.get('success', '#0f0'), 'Success'),
            (current_theme_colors.get('button_bg', '#333'), 'Button')
        ]
        
        for color, label in preview_colors:
            swatch = tk.Frame(color_preview, bg=color, width=30, height=30, relief='solid', bd=1)
            swatch.pack(side='left', padx=3)
            swatch.pack_propagate(False)
        
                   
        separator = tk.Frame(theme_frame, bg=theme_colors["accent"], height=2)
        separator.grid(row=1, column=0, columnspan=3, sticky='ew', pady=(0, 15))
        
                                   
        tk.Label(theme_frame, text="🎭 Select Theme:", 
                bg=theme_colors["bg"], fg=theme_colors["accent"],
                font=('Segoe UI', 10, 'bold')).grid(row=2, column=0, columnspan=3, sticky='w', pady=(0, 10))
        
                                                 
        themes_info = [
            ("Red", "red", "🔴"), ("Dark Mode", "dark", "⚫"),
            ("Pink", "pink", "💖"), ("Christmas", "christmas", "🎄"),
            ("Ocean", "ocean", "🌊"), ("Sunset", "sunset", "🌅"), 
            ("Purple", "purple", "💜"), ("Neon", "neon", "⚡"),
            ("Solarized", "solarized", "🔆"), ("Forest", "forest", "🌳"),
            ("Nord", "nord", "❄️"), ("Sepia", "sepia", "📜")
        ]
        
        row = 3
        for i, (name, theme_id, icon) in enumerate(themes_info):
            if i % 3 == 0:                          
                row += 1
            col = i % 3
            
                                          
            theme_data = self.theme_manager.themes.get(theme_id, {})
            theme_accent = theme_data.get('colors', {}).get('accent', theme_colors["accent"])
            
            theme_btn = tk.Button(theme_frame, text=f"{icon} {name}", 
                                 bg=theme_colors["button_bg"], fg=theme_colors["fg"],
                                 activebackground=theme_accent,
                                 command=lambda t=theme_id: self.apply_theme_and_update(t),
                                 width=12, relief='flat', font=('Segoe UI', 9),
                                 cursor='hand2', padx=5, pady=8)
            theme_btn.grid(row=row, column=col, padx=5, pady=5, sticky='ew')
            
                                                                      
            if theme_id == current_theme_key:
                theme_btn.configure(bg=theme_colors["accent"], fg='#ffffff',
                                  relief='solid', bd=2, font=('Segoe UI', 9, 'bold'))
        
                                              
        for i in range(3):
            theme_frame.columnconfigure(i, weight=1)

    def create_simple_presets_section(self, parent, theme_colors):
        """Create simplified presets section for settings window"""
                         
        presets_frame = tk.LabelFrame(parent, text="💾 Presets", 
                                     bg=theme_colors["bg"], fg=theme_colors["accent"],
                                     font=('Segoe UI', 11, 'bold'), padx=20, pady=15)
        presets_frame.pack(fill='x', padx=10, pady=(0, 20))
        
                     
        save_label = tk.Label(presets_frame, text="Save:", 
                             bg=theme_colors["bg"], fg=theme_colors["fg"])
        save_label.grid(row=0, column=0, sticky='w', pady=5)
        
        save_btn = tk.Button(presets_frame, text="💾 Save Preset", 
                            bg=theme_colors["button_bg"], fg=theme_colors["fg"],
                            command=self.save_preset, width=15, relief='flat')
        save_btn.grid(row=0, column=1, sticky='w', padx=(10, 0), pady=5)
        
                     
        load_label = tk.Label(presets_frame, text="Load:", 
                             bg=theme_colors["bg"], fg=theme_colors["fg"])
        load_label.grid(row=1, column=0, sticky='w', pady=5)
        
        load_btn = tk.Button(presets_frame, text="📁 Load Preset", 
                            bg=theme_colors["button_bg"], fg=theme_colors["fg"],
                            command=self.load_preset, width=15, relief='flat')
        load_btn.grid(row=1, column=1, sticky='w', padx=(10, 0), pady=5)
        
                   
        info_label = tk.Label(presets_frame, 
                             text="Save/load all settings except webhooks and keybinds", 
                             bg=theme_colors["bg"], fg=theme_colors["fg"],
                             font=('Segoe UI', 8))
        info_label.grid(row=2, column=0, columnspan=2, sticky='w', pady=(10, 0))
        
        presets_frame.columnconfigure(1, weight=1)

    def create_timing_settings_section_old(self, parent):
        """Create timing settings section"""
                                 
        timing_section = ttk.LabelFrame(parent, text="⏱️ Timing Settings", padding=20, style='Settings.TLabelFrame')
        timing_section.pack(fill='x', padx=10, pady=(0, 20))
        timing_section.columnconfigure(1, weight=1)
        
        row = 0
        
                                  
        pd_frame = ttk.Frame(timing_section, style='Settings.TFrame')
        pd_frame.grid(row=row, column=0, columnspan=2, sticky='ew', pady=(0, 15))
        pd_frame.columnconfigure(1, weight=1)
        row += 1
        
        ttk.Label(pd_frame, text="🎛️ PD Controller", style='SectionTitle.TLabel').grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 10))
        
                    
        ttk.Label(pd_frame, text="Proportional Gain (KP):", style='Settings.TLabel').grid(row=1, column=0, sticky='w', pady=2)
        self.kp_var = tk.DoubleVar(value=getattr(self, 'kp', 0.2))
        kp_spinbox = ttk.Spinbox(pd_frame, from_=0.01, to=1.0, increment=0.01, 
                                textvariable=self.kp_var, width=15, style='Settings.TSpinbox')
        kp_spinbox.grid(row=1, column=1, sticky='e', padx=(10, 0), pady=2)
        self.kp_var.trace_add('write', lambda *args: (setattr(self, 'kp', self.kp_var.get()), self.auto_save_settings()))
        
                    
        ttk.Label(pd_frame, text="Derivative Gain (KD):", style='Settings.TLabel').grid(row=2, column=0, sticky='w', pady=2)
        self.kd_var = tk.DoubleVar(value=getattr(self, 'kd', 0.6))
        kd_spinbox = ttk.Spinbox(pd_frame, from_=0.01, to=2.0, increment=0.01, 
                                textvariable=self.kd_var, width=15, style='Settings.TSpinbox')
        kd_spinbox.grid(row=2, column=1, sticky='e', padx=(10, 0), pady=2)
        self.kd_var.trace_add('write', lambda *args: (setattr(self, 'kd', self.kd_var.get()), self.auto_save_settings()))
        
                   
        separator1 = ttk.Separator(timing_section, orient='horizontal', style='Settings.TSeparator')
        separator1.grid(row=row, column=0, columnspan=2, sticky='ew', pady=10)
        row += 1
        
                            
        timeout_frame = ttk.Frame(timing_section, style='Settings.TFrame')
        timeout_frame.grid(row=row, column=0, columnspan=2, sticky='ew', pady=(0, 15))
        timeout_frame.columnconfigure(1, weight=1)
        row += 1
        
        ttk.Label(timeout_frame, text="⏰ Timeout Settings", style='SectionTitle.TLabel').grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 10))
        
                      
        ttk.Label(timeout_frame, text="Fish Detection Timeout (s):", style='Settings.TLabel').grid(row=1, column=0, sticky='w', pady=2)
        self.scan_timeout_var = tk.DoubleVar(value=getattr(self, 'scan_timeout', 15.0))
        scan_spinbox = ttk.Spinbox(timeout_frame, from_=5.0, to=60.0, increment=1.0, 
                                  textvariable=self.scan_timeout_var, width=15, style='Settings.TSpinbox')
        scan_spinbox.grid(row=1, column=1, sticky='e', padx=(10, 0), pady=2)
        self.scan_timeout_var.trace_add('write', lambda *args: (setattr(self, 'scan_timeout', self.scan_timeout_var.get()), self.auto_save_settings()))
        
                         
        ttk.Label(timeout_frame, text="Wait After Catch (s):", style='Settings.TLabel').grid(row=2, column=0, sticky='w', pady=2)
        self.wait_after_loss_var = tk.DoubleVar(value=getattr(self, 'wait_after_loss', 1.0))
        wait_spinbox = ttk.Spinbox(timeout_frame, from_=0.1, to=10.0, increment=0.1, 
                                  textvariable=self.wait_after_loss_var, width=15, style='Settings.TSpinbox')
        wait_spinbox.grid(row=2, column=1, sticky='e', padx=(10, 0), pady=2)
        self.wait_after_loss_var.trace_add('write', lambda *args: (setattr(self, 'wait_after_loss', self.wait_after_loss_var.get()), self.auto_save_settings()))
        
                   
        separator2 = ttk.Separator(timing_section, orient='horizontal', style='Settings.TSeparator')
        separator2.grid(row=row, column=0, columnspan=2, sticky='ew', pady=10)
        row += 1
        
                                    
        purchase_frame = ttk.Frame(timing_section, style='Settings.TFrame')
        purchase_frame.grid(row=row, column=0, columnspan=2, sticky='ew')
        purchase_frame.columnconfigure(1, weight=1)
        
        ttk.Label(purchase_frame, text="🛒 Purchase Timing", style='SectionTitle.TLabel').grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 10))
        
                                  
        ttk.Label(purchase_frame, text="Delay After 'E' Key (s):", style='Settings.TLabel').grid(row=1, column=0, sticky='w', pady=2)
        self.purchase_delay_var = tk.DoubleVar(value=getattr(self, 'purchase_delay_after_key', 2.0))
        delay_spinbox = ttk.Spinbox(purchase_frame, from_=0.5, to=10.0, increment=0.1, 
                                   textvariable=self.purchase_delay_var, width=15, style='Settings.TSpinbox')
        delay_spinbox.grid(row=1, column=1, sticky='e', padx=(10, 0), pady=2)
        self.purchase_delay_var.trace_add('write', lambda *args: (setattr(self, 'purchase_delay_after_key', self.purchase_delay_var.get()), self.auto_save_settings()))
        
                     
        ttk.Label(purchase_frame, text="Click Delay (s):", style='Settings.TLabel').grid(row=2, column=0, sticky='w', pady=2)
        self.click_delay_var = tk.DoubleVar(value=getattr(self, 'purchase_click_delay', 1.0))
        click_spinbox = ttk.Spinbox(purchase_frame, from_=0.1, to=5.0, increment=0.1, 
                                   textvariable=self.click_delay_var, width=15, style='Settings.TSpinbox')
        click_spinbox.grid(row=2, column=1, sticky='e', padx=(10, 0), pady=2)
        self.click_delay_var.trace_add('write', lambda *args: (setattr(self, 'purchase_click_delay', self.click_delay_var.get()), self.auto_save_settings()))
        
                    
        ttk.Label(purchase_frame, text="After Type Delay (s):", style='Settings.TLabel').grid(row=3, column=0, sticky='w', pady=2)
        self.type_delay_var = tk.DoubleVar(value=getattr(self, 'purchase_after_type_delay', 1.0))
        type_spinbox = ttk.Spinbox(purchase_frame, from_=0.1, to=5.0, increment=0.1, 
                                  textvariable=self.type_delay_var, width=15, style='Settings.TSpinbox')
        type_spinbox.grid(row=3, column=1, sticky='e', padx=(10, 0), pady=2)
        self.type_delay_var.trace_add('write', lambda *args: (setattr(self, 'purchase_after_type_delay', self.type_delay_var.get()), self.auto_save_settings()))

    def create_theme_settings_section(self, parent):
        """Create theme settings section with banner-style theme cards"""
                                  
        theme_colors = self.theme_manager.themes[self.current_theme]["colors"]
        
                                
        theme_section = ttk.LabelFrame(parent, text="🎨 Theme Settings", padding=20, style='Settings.TLabelFrame')
        theme_section.pack(fill='x', padx=10, pady=(0, 20))
        
                               
        current_frame = ttk.Frame(theme_section, style='Settings.TFrame')
        current_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Label(current_frame, text="Current Theme:", style='SectionTitle.TLabel').pack(side='left')
        current_theme_name = getattr(self, 'current_theme', 'default').title()
        ttk.Label(current_frame, text=current_theme_name, 
                 style='Subtitle.TLabel').pack(side='left', padx=(10, 0))
        
                                                 
        themes_info = [
            ("Default", "default", "🔵", "Classic blue theme with modern styling"),
            ("Dark Mode", "dark", "⚫", "Pure black theme with gray accents"),
            ("Pink", "pink", "💖", "Light, cute pink theme with soft pastel vibes"),
            ("Christmas", "christmas", "🎄", "Festive holiday theme with red and green"),
            ("Ocean", "ocean", "🌊", "Cool ocean blues and aqua tones"),
            ("Sunset", "sunset", "🌅", "Warm sunset oranges and purples"),
            ("Purple", "purple", "💜", "Royal purple with elegant styling"),
            ("Neon", "neon", "⚡", "Bright neon colors for vibrant experience")
        ]
        
                                                                     
        themes_frame = ttk.Frame(theme_section, style='Settings.TFrame')
        themes_frame.pack(fill='x')
        themes_frame.columnconfigure(0, weight=1)
        themes_frame.columnconfigure(1, weight=1)
        
        for i, (name, theme_id, icon, description) in enumerate(themes_info):
            row = i // 2
            col = i % 2
            
                                                                                
            banner_frame = tk.Frame(themes_frame, 
                                   bg=theme_colors["button_bg"], 
                                   relief='solid', 
                                   borderwidth=1,
                                   highlightbackground=theme_colors["accent"],
                                   highlightthickness=1)
            banner_frame.grid(row=row, column=col, padx=5, pady=3, sticky='ew')
            banner_frame.columnconfigure(1, weight=1)
            
                        
            icon_label = tk.Label(banner_frame, text=icon, font=('Segoe UI', 14),
                                 bg=theme_colors["button_bg"], fg=theme_colors["fg"])
            icon_label.grid(row=0, column=0, padx=(10, 5), pady=8)
            
                        
            info_frame = tk.Frame(banner_frame, bg=theme_colors["button_bg"])
            info_frame.grid(row=0, column=1, sticky='ew', padx=(0, 5), pady=5)
            info_frame.columnconfigure(0, weight=1)
            
                        
            name_label = tk.Label(info_frame, text=name, font=('Segoe UI', 10, 'bold'),
                                 bg=theme_colors["button_bg"], fg=theme_colors["fg"])
            name_label.grid(row=0, column=0, sticky='w')
            
                               
            desc_label = tk.Label(info_frame, text=description, font=('Segoe UI', 8),
                                 bg=theme_colors["button_bg"], fg=theme_colors["fg"])
            desc_label.grid(row=1, column=0, sticky='w')
            
                          
            apply_btn = ttk.Button(banner_frame, text='Apply', width=8, style='Settings.TButton',
                                  command=lambda t=theme_id: self.apply_theme_and_update(t))
            apply_btn.grid(row=0, column=2, padx=(5, 10), pady=8)
            
                                     
            if theme_id == getattr(self, 'current_theme', 'default'):
                banner_frame.configure(highlightbackground=theme_colors["accent"], highlightthickness=2)
                name_label.configure(fg=theme_colors["accent"])
    
    def apply_theme_and_update(self, theme_id):
        """Apply theme and refresh windows properly"""
        print(f"\n{'='*50}")
        print(f"🎨 APPLYING THEME: {theme_id}")
        print(f"{'='*50}")
        
        if hasattr(self, 'theme_manager') and theme_id in self.theme_manager.themes:
                             
            self.current_theme = theme_id
            self.apply_theme()
            self.auto_save_settings()
            
            print("✅ Theme applied to main GUI")
            
                                          
            theme_window_exists = hasattr(self, 'theme_window') and self.theme_window
            print(f"Theme window exists: {theme_window_exists}")
            
            if theme_window_exists:
                try:
                    if self.theme_window.winfo_exists():
                        print("🔄 Calling refresh_theme_window()...")
                        self.refresh_theme_window()
                    else:
                        print("⚠️ Theme window not visible")
                except Exception as e:
                    print(f"❌ Error refreshing theme window: {e}")
                    import traceback
                    traceback.print_exc()
            
                                             
            try:
                if hasattr(self, 'settings_window') and self.settings_window:
                    if self.settings_window.winfo_exists():
                        print("🔄 Refreshing settings window...")
                        self.settings_window.destroy()
                        self.settings_window = None
                        self.root.after(50, self.open_settings_window)
            except Exception as e:
                print(f"❌ Error refreshing settings window: {e}")
            
            print(f"\n✅ Successfully applied {theme_id} theme")
            print(f"{'='*50}\n")
        else:
            print(f"❌ Theme {theme_id} not found or theme_manager not available")



    def open_discord(self):
        """Open Discord invite link in browser"""
        import webbrowser
        try:
            webbrowser.open('https://discord.gg/5Gtsgv46ce')
            self.status_msg.config(text='Opened Discord invite', foreground='#0DA50DFF')
        except Exception as e:
            self.status_msg.config(text=f'Error opening Discord: {e}', foreground='red')

    def check_for_updates(self):
        """Manual update check triggered by user"""
        if not self.update_manager:
            self.update_status('UpdateManager not available', 'error', '❌')
            return
        
                                               
        threading.Thread(target=self.update_manager.check_for_updates_manual, daemon=True).start()


    
    def update_status(self, message, status_type='info', icon=''):
        """Update status message from UpdateManager"""
        color_map = {
            'success': 'green',
            'error': 'red',
            'warning': 'orange',
            'info': '#58a6ff'
        }
        color = color_map.get(status_type, '#58a6ff')
        
        full_message = f'{icon} {message}' if icon else message
        self.status_msg.config(text=full_message, foreground=color)

    def test_webhook(self):
        """Send a test webhook message"""
        self.webhook_manager.test()
    

    

    
    def on_zoom_settings_change(self, *args):
        """Called when zoom settings change in GUI"""
        if hasattr(self, 'zoom_controller'):
            self.update_zoom_controller_settings()
    
    def update_zoom_controller_settings(self):
        """Update zoom controller with current GUI settings"""
        if hasattr(self, 'zoom_controller'):
            self.zoom_controller.update_settings({
                'zoom_out_steps': self.zoom_out_var.get(),
                'zoom_in_steps': self.zoom_in_var.get()
            })
            print(f"🔧 Zoom settings updated: Out={self.zoom_out_var.get()}, In={self.zoom_in_var.get()}")

    def apply_theme(self):
        """Apply the current theme to the application"""
        style = ttk.Style()
        
                                             
        theme_colors = self.theme_manager.themes[self.current_theme]["colors"]
        is_dark = theme_colors["bg"] == "#0d1117"
        
        if is_dark:
                                                                  
            self.root.configure(bg=theme_colors["bg"])
            style.theme_use('clam')
            
                                
            style.configure('TFrame', 
                          background=theme_colors["bg"],
                          relief='flat',
                          borderwidth=0)
            
            style.configure('TLabel', 
                          background=theme_colors["bg"], 
                          foreground=theme_colors["fg"],
                          font=('Segoe UI', 9))
            
                                   
            style.configure('TButton',
                          background=theme_colors["button_bg"],
                          foreground=theme_colors["fg"],
                          borderwidth=1,
                          focuscolor='none',
                          font=('Segoe UI', 9),
                          relief='flat')
            style.map('TButton',
                     background=[('active', theme_colors["button_hover"]), ('pressed', theme_colors["button_hover"])],
                     bordercolor=[('active', theme_colors["accent"]), ('pressed', theme_colors["accent"])])
            
                                               
            style.configure('Accent.TButton',
                          background='#238636',
                          foreground='#ffffff',
                          borderwidth=0,
                          font=('Segoe UI', 9, 'bold'))
            style.map('Accent.TButton',
                     background=[('active', '#2ea043'), ('pressed', '#1a7f37')])
            
                            
            style.configure('Status.TButton',
                          background='#1f6feb',
                          foreground='#ffffff',
                          borderwidth=0,
                          font=('Segoe UI', 9))
            style.map('Status.TButton',
                     background=[('active', '#388bfd'), ('pressed', '#0969da')])
            
            style.configure('TCheckbutton',
                          background=theme_colors["bg"],
                          foreground=theme_colors["fg"],
                          focuscolor='none',
                          font=('Segoe UI', 9))
            style.map('TCheckbutton',
                     background=[('active', theme_colors["bg"]),
                               ('selected', theme_colors["bg"])])
            
            style.configure('TSpinbox',
                          fieldbackground=theme_colors["button_bg"],
                          background=theme_colors["button_bg"],
                          foreground=theme_colors["fg"],
                          bordercolor=theme_colors["accent"],
                          arrowcolor=theme_colors["fg"],
                          insertcolor=theme_colors["fg"],
                          selectbackground=theme_colors["accent"],
                          selectforeground=theme_colors["bg"],
                          font=('Segoe UI', 9))
            style.map('TSpinbox',
                     fieldbackground=[('focus', theme_colors["button_hover"])],
                     bordercolor=[('focus', theme_colors["accent"])])
            
                                                  
            style.configure('Vertical.TScrollbar',
                          background=theme_colors["scrollbar_bg"],
                          troughcolor=theme_colors["scrollbar_trough"],
                          bordercolor=theme_colors["scrollbar_active"],
                          arrowcolor=theme_colors["fg"],
                          darkcolor=theme_colors["scrollbar_bg"],
                          lightcolor=theme_colors["scrollbar_active"])
            style.map('Vertical.TScrollbar',
                     background=[('active', theme_colors["scrollbar_active"]), ('pressed', theme_colors["scrollbar_pressed"])])
            
                            
            style.configure('Title.TLabel',
                          background=theme_colors["bg"],
                          foreground=theme_colors["accent"],
                          font=('Segoe UI', 18, 'bold'))
            
            style.configure('Subtitle.TLabel',
                          background=theme_colors["bg"],
                          foreground=theme_colors["fg"],
                          font=('Segoe UI', 8))
            
                                   
            style.configure('SectionTitle.TLabel',
                          background=theme_colors["bg"],
                          foreground=theme_colors["accent"],
                          font=('Segoe UI', 11, 'bold'))
            
                           
            style.configure('StatusOn.TLabel',
                          background=theme_colors["bg"],
                          foreground=theme_colors["success"],
                          font=('Segoe UI', 10, 'bold'))
            
            style.configure('StatusOff.TLabel',
                          background=theme_colors["bg"],
                          foreground=theme_colors["error"],
                          font=('Segoe UI', 10))
            
            style.configure('StatusInfo.TLabel',
                          background=theme_colors["bg"],
                          foreground=theme_colors["accent"],
                          font=('Segoe UI', 10, 'bold'))
            
            style.configure('Counter.TLabel',
                          background=theme_colors["bg"],
                          foreground=theme_colors["fg"],
                          font=('Segoe UI', 11, 'bold'))
            
                                                    
            if hasattr(self, 'canvas'):
                self.canvas.configure(bg=theme_colors["bg"])
            
                                                    
            self.update_fishing_location_colors()
        else:
                                                   
            self.root.configure(bg=theme_colors["bg"])
            style.theme_use('clam')
            
                                
            style.configure('TFrame', 
                          background=theme_colors["bg"],
                          relief='flat',
                          borderwidth=0)
            
            style.configure('TLabel', 
                          background=theme_colors["bg"], 
                          foreground=theme_colors["fg"],
                          font=('Segoe UI', 9))
            
                                                  
            style.configure('TButton',
                          background=theme_colors["button_bg"],
                          foreground=theme_colors["fg"],
                          borderwidth=1,
                          focuscolor='none',
                          font=('Segoe UI', 9),
                          relief='flat')
            style.map('TButton',
                     background=[('active', theme_colors["button_hover"]), ('pressed', theme_colors["button_hover"])],
                     bordercolor=[('active', theme_colors["accent"]), ('pressed', theme_colors["accent"])])
            
                                               
            style.configure('Accent.TButton',
                          background='#2da44e',
                          foreground='#ffffff',
                          borderwidth=0,
                          font=('Segoe UI', 9, 'bold'))
            style.map('Accent.TButton',
                     background=[('active', '#2c974b'), ('pressed', '#298e46')])
            
                            
            style.configure('Status.TButton',
                          background='#0969da',
                          foreground='#ffffff',
                          borderwidth=0,
                          font=('Segoe UI', 9))
            style.map('Status.TButton',
                     background=[('active', '#0860ca'), ('pressed', '#0757ba')])
            
            style.configure('TCheckbutton',
                          background=theme_colors["bg"],
                          foreground=theme_colors["fg"],
                          focuscolor='none',
                          font=('Segoe UI', 9))
            style.map('TCheckbutton',
                     background=[('active', theme_colors["bg"]),
                               ('selected', theme_colors["bg"])])
            
            style.configure('TSpinbox',
                          fieldbackground=theme_colors["button_bg"],
                          background=theme_colors["button_bg"],
                          foreground=theme_colors["fg"],
                          bordercolor=theme_colors["accent"],
                          arrowcolor=theme_colors["fg"],
                          insertcolor=theme_colors["fg"],
                          selectbackground=theme_colors["accent"],
                          selectforeground=theme_colors["bg"],
                          font=('Segoe UI', 9))
            style.map('TSpinbox',
                     fieldbackground=[('focus', theme_colors["button_hover"])],
                     bordercolor=[('focus', theme_colors["accent"])])
            
                                                   
            style.configure('TEntry',
                          fieldbackground='#f6f8fa',
                          background='#e1e4e8',
                          foreground='#24292f',
                          bordercolor='#d0d7de',
                          font=('Segoe UI', 9))
            
                                                  
            style.configure('Vertical.TScrollbar',
                          background=theme_colors["scrollbar_bg"],
                          troughcolor=theme_colors["scrollbar_trough"],
                          bordercolor=theme_colors["scrollbar_active"],
                          arrowcolor=theme_colors["fg"],
                          darkcolor=theme_colors["scrollbar_bg"],
                          lightcolor=theme_colors["scrollbar_active"])
            style.map('Vertical.TScrollbar',
                     background=[('active', theme_colors["scrollbar_active"]), ('pressed', theme_colors["scrollbar_pressed"])])
            
                            
            style.configure('Title.TLabel',
                          background=theme_colors["bg"],
                          foreground=theme_colors["accent"],
                          font=('Segoe UI', 18, 'bold'))
            
            style.configure('Subtitle.TLabel',
                          background=theme_colors["bg"],
                          foreground=theme_colors["fg"],
                          font=('Segoe UI', 8))
            
                                   
            style.configure('SectionTitle.TLabel',
                          background=theme_colors["bg"],
                          foreground=theme_colors["accent"],
                          font=('Segoe UI', 11, 'bold'))
            
                           
            style.configure('StatusOn.TLabel',
                          background=theme_colors["bg"],
                          foreground=theme_colors["success"],
                          font=('Segoe UI', 10, 'bold'))
            
            style.configure('StatusOff.TLabel',
                          background=theme_colors["bg"],
                          foreground=theme_colors["error"],
                          font=('Segoe UI', 10))
            
            style.configure('StatusInfo.TLabel',
                          background=theme_colors["bg"],
                          foreground=theme_colors["accent"],
                          font=('Segoe UI', 10, 'bold'))
            
            style.configure('Counter.TLabel',
                          background=theme_colors["bg"],
                          foreground=theme_colors["fg"],
                          font=('Segoe UI', 11, 'bold'))
            
                                                     
            if hasattr(self, 'canvas'):
                self.canvas.configure(bg=theme_colors["bg"])
            
                                                    
            self.update_fishing_location_colors()
        
                                                      
                                          
        style.configure('Badge.TLabel',
                      background='#238636',
                      foreground='#ffffff',
                      font=('Segoe UI', 9, 'bold'),
                      padding=(8, 2))
        
                                                                             
        style.configure('StatCard.TLabel',
                      background=theme_colors["button_bg"],
                      foreground=theme_colors["fg"],
                      font=('Segoe UI', 11),
                      padding=15,
                      relief='flat')
        
                                
        style.configure('Description.TLabel',
                      background=theme_colors["bg"],
                      foreground=theme_colors["fg"],
                      font=('Segoe UI', 9))
        
                            
        style.configure('Status.TLabel',
                      background=theme_colors["bg"],
                      foreground=theme_colors["accent"],
                      font=('Segoe UI', 9, 'italic'))
        
                                                     
        style.configure('TLabelframe',
                      background=theme_colors["bg"],
                      foreground=theme_colors["fg"],
                      borderwidth=1,
                      bordercolor=theme_colors["button_bg"],
                      relief='solid')
        
        style.configure('TLabelframe.Label',
                      background=theme_colors["bg"],
                      foreground=theme_colors["accent"],
                      font=('Segoe UI', 10, 'bold'))
        
                                                 
        style.configure('Tab.TButton',
                      background=theme_colors["button_bg"],
                      foreground=theme_colors["fg"],
                      borderwidth=0,
                      relief='flat',
                      padding=[10, 15],
                      font=('Segoe UI', 11))
        style.map('Tab.TButton',
                 background=[('active', theme_colors["button_hover"])],
                 foreground=[('active', theme_colors["fg"])])
        
                                 
        style.configure('TabActive.TButton',
                      background=theme_colors["accent"],
                      foreground='#ffffff',
                      borderwidth=0,
                      relief='flat',
                      padding=[10, 15],
                      font=('Segoe UI', 11, 'bold'))
        style.map('TabActive.TButton',
                 background=[('active', theme_colors["accent"])],
                 foreground=[('active', '#ffffff')])




    def on_window_resize(self, event):
        """Handle window resize events and save window size"""
                                                       
        if event.widget == self.root:
            try:
                                         
                width = self.root.winfo_width()
                height = self.root.winfo_height()
                
                                                                       
                if not hasattr(self, '_resize_after_id'):
                    self._resize_after_id = None
                
                if self._resize_after_id:
                    self.root.after_cancel(self._resize_after_id)
                
                                                        
                self._resize_after_id = self.root.after(500, lambda: self.save_window_size(width, height))
            except Exception as e:
                print(f"Error handling window resize: {e}")
    
    def save_window_size(self, width, height):
        """Save window size to settings"""
        try:
            self.window_width = width
            self.window_height = height
            self.auto_save_settings()
            self._resize_after_id = None
        except Exception as e:
            print(f"Error saving window size: {e}")

    def auto_save_settings(self):
        """Auto-save current settings to default.json"""
        loading_flag = getattr(self, '_loading_settings', False)
        print(f"💾 auto_save_settings() called, _loading_settings={loading_flag}")
        
        if loading_flag:
            print("⏸️ Skipping auto-save during initialization")
            return
            
        try:
            print("💾 Auto-saving settings...")
            
            if not hasattr(self, 'auto_purchase_var'):
                print("⚠️ Skipping save - GUI not fully initialized")
                return                                 
            
            preset_data = {
                                        
                'auto_purchase_enabled': self.auto_purchase_var.get() if hasattr(self, 'auto_purchase_var') else False,
                'auto_purchase_amount': self._safe_get_int(self.amount_var, getattr(self, 'auto_purchase_amount', 100)) if hasattr(self, 'amount_var') else 100,
                'loops_per_purchase': self._safe_get_int(self.loops_var, getattr(self, 'loops_per_purchase', 1)) if hasattr(self, 'loops_var') else 1,
                'purchase_interval': self.purchase_interval.get() if hasattr(self, 'purchase_interval') else 0,
                'point_coords': getattr(self, 'point_coords', {}),
                
                                        
                'fruit_coords': getattr(self, 'fruit_coords', {}),
                'fishing_location': getattr(self, 'fishing_location', None),
                'fruit_storage_enabled': self.fruit_storage_var.get() if hasattr(self, 'fruit_storage_var') else False,
                'fruit_storage_key': getattr(self, 'fruit_storage_key', '2'),
                'fruit_storage_key_2': getattr(self, 'fruit_storage_key_2', '3'),
                'rod_key': getattr(self, 'rod_key', '1'),
                
                                    
                'auto_bait_enabled': self.auto_bait_var.get() if hasattr(self, 'auto_bait_var') else False,
                'top_bait_coords': getattr(self, 'top_bait_coords', None),
                'top_bait_coords_2': getattr(self, 'top_bait_coords_2', None),
                
                                        
                'kp': getattr(self, 'kp', 0.1),
                'kd': getattr(self, 'kd', 0.5),
                'scan_timeout': getattr(self, 'scan_timeout', 15.0),
                'wait_after_loss': getattr(self, 'wait_after_loss', 1.0),
                'smart_check_interval': getattr(self, 'smart_check_interval', 15.0),
                
                                  
                'webhook_url': getattr(self, 'webhook_url', ''),
                'webhook_enabled': self.webhook_var.get() if hasattr(self, 'webhook_var') else False,
                'webhook_interval': getattr(self, 'webhook_interval', 10),
                'fish_progress_webhook_enabled': getattr(self, 'fish_progress_webhook_enabled', True),
                'devil_fruit_webhook_enabled': getattr(self, 'devil_fruit_webhook_enabled', True),
                'fruit_spawn_webhook_enabled': getattr(self, 'fruit_spawn_webhook_enabled', True),
                'purchase_webhook_enabled': getattr(self, 'purchase_webhook_enabled', True),
                'recovery_webhook_enabled': getattr(self, 'recovery_webhook_enabled', True),
                'bait_webhook_enabled': getattr(self, 'bait_webhook_enabled', True),
                
                              
                'ocr_performance_mode': getattr(self, 'ocr_performance_mode', 'fast'),
                
                                      
                'window_width': getattr(self, 'window_width', 420),
                'window_height': getattr(self, 'window_height', 650),

                                
                'dark_theme': getattr(self, 'dark_theme', True),
                'current_theme': getattr(self, 'current_theme', 'default'),
                'layout_settings': getattr(self.layout_manager, 'layouts', {}) if hasattr(self, 'layout_manager') else {},

                               
                'zoom_settings': {
                    'auto_zoom_enabled': getattr(self, 'auto_zoom_enabled', False),
                    'auto_mouse_position_enabled': getattr(self, 'auto_mouse_position_enabled', False),
                    'zoom_out_steps': self.zoom_out_var.get() if hasattr(self, 'zoom_out_var') else 5,
                    'zoom_in_steps': self.zoom_in_var.get() if hasattr(self, 'zoom_in_var') else 8,
                    'step_delay': 0.1,
                    'sequence_delay': 0.5,
                    'zoom_cooldown': 2.0
                },
                'last_saved': datetime.now().isoformat()
            }
            
            print(f"💾 Zoom settings to save: auto_zoom_enabled={preset_data['zoom_settings']['auto_zoom_enabled']}, auto_mouse_position_enabled={preset_data['zoom_settings']['auto_mouse_position_enabled']}")
            
            settings_file = "default_settings.json"
            with open(settings_file, 'w') as f:
                json.dump(preset_data, f, indent=2)
            
            print(f"✅ Settings saved to {settings_file}")
            print(f"   - Auto Purchase: {preset_data['auto_purchase_enabled']}")
            print(f"   - Fruit Storage: {preset_data['fruit_storage_enabled']}")
            print(f"   - Auto Bait: {preset_data['auto_bait_enabled']}")
            print(f"   - Webhook: {preset_data['webhook_enabled']}")
            print(f"   - Point Coords: {len(preset_data['point_coords'])} points")
            print(f"   - Fruit Coords: {len(preset_data['fruit_coords'])} points")
            
        except Exception as e:
            print(f'❌ ERROR auto-saving settings: {e}')
            import traceback
            traceback.print_exc()

    def save_preset(self):
        """Save current settings to a preset file (excluding webhooks and keybinds)"""
        try:
                                      
            preset_name = simpledialog.askstring("Save Preset", "Enter preset name:")
            if not preset_name:
                return
            
                            
            import re
            preset_name = re.sub(r'[<>:"/\\|?*]', '_', preset_name)
            
                                                               
            preset_data = {
                                        
                'auto_purchase_enabled': getattr(self, 'auto_purchase_var', None) and self.auto_purchase_var.get() if hasattr(self, 'auto_purchase_var') else False,
                'auto_purchase_amount': getattr(self, 'auto_purchase_amount', 100),
                'loops_per_purchase': getattr(self, 'loops_per_purchase', 1),
                'point_coords': getattr(self, 'point_coords', {}),
                
                                        
                'kp': getattr(self, 'kp', 0.1),
                'kd': getattr(self, 'kd', 0.5),
                
                                 
                'scan_timeout': getattr(self, 'scan_timeout', 15.0),
                'wait_after_loss': getattr(self, 'wait_after_loss', 1.0),
                'purchase_delay_after_key': getattr(self, 'purchase_delay_after_key', 2.0),
                'purchase_click_delay': getattr(self, 'purchase_click_delay', 1.0),
                'purchase_after_type_delay': getattr(self, 'purchase_after_type_delay', 1.0),
                

                
                                    
                'auto_bait_enabled': getattr(self, 'auto_bait_enabled', False),

                
                                   
                'recovery_enabled': getattr(self, 'recovery_enabled', True),
                
                                      
                'silent_mode': getattr(self, 'silent_mode', False),
                'verbose_logging': getattr(self, 'verbose_logging', False),
                
                                
                'dark_theme': getattr(self, 'dark_theme', True),
            }
            
                                    
            preset_file = os.path.join(self.presets_dir, f"{preset_name}.json")
            with open(preset_file, 'w') as f:
                json.dump(preset_data, f, indent=2)
            
            self.status_msg.config(text=f'Preset "{preset_name}" saved successfully!', foreground='green')
            print(f'✅ Preset saved: {preset_file}')
            
        except Exception as e:
            self.status_msg.config(text=f'Error saving preset: {e}', foreground='red')
            print(f'❌ Error saving preset: {e}')

    def load_preset(self):
        """Load settings from a preset file"""
        try:
                                               
            preset_file = filedialog.askopenfilename(
                title="Load Preset",
                initialdir=self.presets_dir,
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if not preset_file:
                return
            
                              
            with open(preset_file, 'r') as f:
                preset_data = json.load(f)
            
                                                              
            
                                    
            if hasattr(self, 'auto_purchase_var'):
                self.auto_purchase_var.set(preset_data.get('auto_purchase_enabled', False))
            self.auto_purchase_amount = preset_data.get('auto_purchase_amount', 100)
            if hasattr(self, 'amount_var'):
                self.amount_var.set(self.auto_purchase_amount)
            
            self.loops_per_purchase = preset_data.get('loops_per_purchase', 1)
            if hasattr(self, 'loops_var'):
                self.loops_var.set(self.loops_per_purchase)
            
                                                                   
            loaded_coords = preset_data.get('point_coords', {})
            self.point_coords = {}
            for key, value in loaded_coords.items():
                try:
                    int_key = int(key)
                    self.point_coords[int_key] = value
                except (ValueError, TypeError):
                    pass
                                                
            for idx in range(1, 5):
                if hasattr(self, 'point_buttons') and idx in self.point_buttons:
                    self.update_point_button(idx)
            
                                            
            self.fruit_coords = preset_data.get('fruit_coords', {})
            
                                         
            self.fruit_storage_enabled = preset_data.get('fruit_storage_enabled', False)
            if hasattr(self, 'fruit_storage_var'):
                self.fruit_storage_var.set(self.fruit_storage_enabled)
            
            self.fruit_storage_key = preset_data.get('fruit_storage_key', '2')
            self.fruit_storage_key_2 = preset_data.get('fruit_storage_key_2', '3')
            self.rod_key = preset_data.get('rod_key', '1')
            
                                                        
            if hasattr(self, 'fruit_key_var'):
                self.fruit_key_var.set(int(self.fruit_storage_key))
            if hasattr(self, 'fruit_key_2_var'):
                self.fruit_key_2_var.set(int(self.fruit_storage_key_2))
            if hasattr(self, 'rod_key_var'):
                self.rod_key_var.set(int(self.rod_key))
            if hasattr(self, 'fruit_point_button') and 'fruit_point' in self.fruit_coords:
                coords = self.fruit_coords['fruit_point']
                self.fruit_point_button.config(text=f'Fruit Point: {coords}')
            if hasattr(self, 'fruit_point_2_button') and 'fruit_point_2' in self.fruit_coords:
                coords = self.fruit_coords['fruit_point_2']
                self.fruit_point_2_button.config(text=f'Fruit Point 2: {coords}')
            if hasattr(self, 'bait_point_button') and 'bait_point' in self.fruit_coords:
                coords = self.fruit_coords['bait_point']
                self.bait_point_button.config(text=f'Bait Point: {coords}')
            
                                    
            self.kp = preset_data.get('kp', 0.1)
            if hasattr(self, 'kp_var'):
                self.kp_var.set(self.kp)
            
            self.kd = preset_data.get('kd', 0.5)
            if hasattr(self, 'kd_var'):
                self.kd_var.set(self.kd)
            
                             
            self.scan_timeout = preset_data.get('scan_timeout', 15.0)
            if hasattr(self, 'timeout_var'):
                self.timeout_var.set(self.scan_timeout)
            
            self.wait_after_loss = preset_data.get('wait_after_loss', 1.0)
            if hasattr(self, 'wait_var'):
                self.wait_var.set(self.wait_after_loss)
            
            self.purchase_delay_after_key = preset_data.get('purchase_delay_after_key', 2.0)
            self.purchase_click_delay = preset_data.get('purchase_click_delay', 1.0)
            self.purchase_after_type_delay = preset_data.get('purchase_after_type_delay', 1.0)
            

            
                                     
            self.auto_bait_enabled = preset_data.get('auto_bait_enabled', False)

            
                               
            self.recovery_enabled = preset_data.get('recovery_enabled', True)
            
                                  
            self.silent_mode = preset_data.get('silent_mode', False)
            self.verbose_logging = preset_data.get('verbose_logging', False)
            
                            
            new_theme = preset_data.get('dark_theme', True)
            if new_theme != self.dark_theme:
                self.dark_theme = new_theme
                self.apply_theme()
            

            
            preset_name = os.path.splitext(os.path.basename(preset_file))[0]
            self.status_msg.config(text=f'Preset "{preset_name}" loaded successfully!', foreground='green')
            print(f'✅ Preset loaded: {preset_file}')
            
                                                               
            self.auto_save_settings()
            
        except Exception as e:
            self.status_msg.config(text=f'Error loading preset: {e}', foreground='red')
            print(f'❌ Error loading preset: {e}')

    def refresh_button_labels(self):
        """Update all button labels to show loaded coordinates"""
        try:
                                                
            if hasattr(self, 'point_buttons') and hasattr(self, 'point_coords'):
                for idx, coords in self.point_coords.items():
                    if idx in self.point_buttons and coords:
                        self.point_buttons[idx].config(text=f'✓ Point {idx}: ({coords[0]}, {coords[1]})')
            
                                          
            if hasattr(self, 'fruit_coords'):
                if self.fruit_coords.get('fruit_point') and hasattr(self, 'fruit_point_btn'):
                    coords = self.fruit_coords['fruit_point']
                    self.fruit_point_btn.config(text=f'✓ Fruit 1: ({coords[0]}, {coords[1]})')
                if self.fruit_coords.get('fruit_point_2') and hasattr(self, 'fruit_point_2_btn'):
                    coords = self.fruit_coords['fruit_point_2']
                    self.fruit_point_2_btn.config(text=f'✓ Fruit 2 (Backup): ({coords[0]}, {coords[1]})')
            
                                 
            if self.top_bait_coords and hasattr(self, 'top_bait_btn'):
                coords = self.top_bait_coords
                self.top_bait_btn.config(text=f'✓ Bait 1: ({coords[0]}, {coords[1]})')
            if self.top_bait_coords_2 and hasattr(self, 'top_bait_2_btn'):
                coords = self.top_bait_coords_2
                self.top_bait_2_btn.config(text=f'✓ Bait 2 (Backup): ({coords[0]}, {coords[1]})')
            
                                            
            if self.fishing_location and hasattr(self, 'fishing_location_btn'):
                coords = self.fishing_location
                self.fishing_location_btn.config(text=f'🎯 Cast Location: ({coords[0]}, {coords[1]})')
                
            print(f"🔄 Button labels refreshed with loaded coordinates")
        except Exception as e:
            print(f"⚠️ Error refreshing button labels: {e}")

    def setup_console_redirect(self):
        """Redirect stdout and stderr to dev log"""
        import sys
        import io
        
                                                                      
        class LogWriter:
            def __init__(self, gui, original_stream):
                self.gui = gui
                # Some frozen builds (or when launched via vbs) give None for stdout/stderr
                # so fall back to the real std streams if available.
                self.original_stream = original_stream or getattr(sys, '__stdout__', None)
            
            def write(self, message):
                # Skip if no underlying stream is available (silent logging)
                if self.original_stream:
                    try:
                        self.original_stream.write(message)
                        self.original_stream.flush()
                    except Exception:
                        pass
                
                # Also mirror into the activity log, if it exists
                if hasattr(self.gui, 'activity_log') and message.strip():
                    try:
                        self.gui.root.after(0, lambda msg=message: self.gui.add_activity(msg.strip()))
                    except Exception:
                        pass
            
            def flush(self):
                if self.original_stream:
                    try:
                        self.original_stream.flush()
                    except Exception:
                        pass
        
        sys.stdout = LogWriter(self, sys.stdout)
        sys.stderr = LogWriter(self, sys.stderr)

    def load_basic_settings(self):
        """Load basic settings before UI creation"""
        settings_file = "default_settings.json"
        print(f"\n📂 Loading settings from {settings_file}...")
        
        if not os.path.exists(settings_file):
            print("⚠️ No settings file found - using defaults")
                                              
            self.settings = {
                'zoom_settings': {
                    'auto_zoom_enabled': False,
                    'zoom_out_steps': 5,
                    'zoom_in_steps': 8,
                    'step_delay': 0.1,
                    'sequence_delay': 0.5,
                    'zoom_cooldown': 2.0
                },
                'layout_settings': {}
            }
            return                                   
            
        try:
            with open(settings_file, 'r') as f:
                preset_data = json.load(f)
            
            print(f"✅ Settings file loaded successfully")
            print(f"   - Auto Purchase: {preset_data.get('auto_purchase_enabled', False)}")
            print(f"   - Fruit Storage: {preset_data.get('fruit_storage_enabled', False)}")
            print(f"   - Auto Bait: {preset_data.get('auto_bait_enabled', False)}")
            print(f"   - Webhook: {preset_data.get('webhook_enabled', False)}")
            print(f"   - Point Coords: {len(preset_data.get('point_coords', {}))} points")
            print(f"   - Fruit Coords: {len(preset_data.get('fruit_coords', {}))} points")
            
                                                                
            self.settings = preset_data
            
                                                                
            self.auto_purchase_amount = preset_data.get('auto_purchase_amount', 100)
            self.loops_per_purchase = preset_data.get('loops_per_purchase', 1)
            self.purchase_interval_value = preset_data.get('purchase_interval', 0)
            
                                
            self.auto_zoom_enabled = preset_data.get('zoom_settings', {}).get('auto_zoom_enabled', False)
            
                                                                   
            loaded_coords = preset_data.get('point_coords', {})
            self.point_coords = {}
            for key, value in loaded_coords.items():
                try:
                    int_key = int(key)
                    self.point_coords[int_key] = value
                except (ValueError, TypeError):
                    pass
            self.kp = preset_data.get('kp', 0.1)
            self.kd = preset_data.get('kd', 0.5)
            self.scan_timeout = preset_data.get('scan_timeout', 15.0)
            self.wait_after_loss = preset_data.get('wait_after_loss', 1.0)
            self.smart_check_interval = preset_data.get('smart_check_interval', 15.0)
            self.webhook_url = preset_data.get('webhook_url', '')
            self.webhook_enabled = preset_data.get('webhook_enabled', False)
            self.webhook_interval = preset_data.get('webhook_interval', 10)
            
                                                        
            self.fish_progress_webhook_enabled = preset_data.get('fish_progress_webhook_enabled', True)
            self.devil_fruit_webhook_enabled = preset_data.get('devil_fruit_webhook_enabled', True)
            self.fruit_spawn_webhook_enabled = preset_data.get('fruit_spawn_webhook_enabled', True)
            self.purchase_webhook_enabled = preset_data.get('purchase_webhook_enabled', True)
            self.recovery_webhook_enabled = preset_data.get('recovery_webhook_enabled', True)
            self.bait_webhook_enabled = preset_data.get('bait_webhook_enabled', True)
            
                                       
            self.ocr_performance_mode = preset_data.get('ocr_performance_mode', 'fast')
            if hasattr(self, 'ocr_manager') and hasattr(self.ocr_manager, 'set_performance_mode'):
                self.ocr_manager.set_performance_mode(self.ocr_performance_mode)
            
                                                  
            self.auto_bait_enabled = preset_data.get('auto_bait_enabled', False)
            self.top_bait_coords = preset_data.get('top_bait_coords', None)
            self.top_bait_coords_2 = preset_data.get('top_bait_coords_2', None)
            
                                       
            self.window_width = preset_data.get('window_width', 420)
            self.window_height = preset_data.get('window_height', 650)

            self.fruit_storage_enabled = preset_data.get('fruit_storage_enabled', False)
            self.fruit_storage_key = preset_data.get('fruit_storage_key', '2')
            self.fruit_storage_key_2 = preset_data.get('fruit_storage_key_2', '3')
            self.rod_key = preset_data.get('rod_key', '1')
            self.bait_point = preset_data.get('bait_point', '2')
            
                                    
            self.fruit_coords = preset_data.get('fruit_coords', {})
            
                                                   
            self.fishing_location = preset_data.get('fishing_location', None)
            
            self.dark_theme = preset_data.get('dark_theme', True)
            self.current_theme = preset_data.get('current_theme', 'default')
            
        except Exception as e:
            print(f'Error loading basic settings: {e}')
                                                       
            self.settings = {
                'zoom_settings': {
                    'auto_zoom_enabled': False,
                    'zoom_out_steps': 5,
                    'zoom_in_steps': 8,
                    'step_delay': 0.1,
                    'sequence_delay': 0.5,
                    'zoom_cooldown': 2.0
                },
                'layout_settings': {}
            }

    def load_ui_settings(self):
        """Load UI-specific settings after widgets are created"""
        settings_file = "default_settings.json"
        if not os.path.exists(settings_file):
            self._loading_settings = False                    
            print("⚠️ No settings file found, using defaults")
            return                                   
            
        try:
            with open(settings_file, 'r') as f:
                preset_data = json.load(f)
            
            print(f"\n📋 Applying settings to UI...")
            
                                               
            if hasattr(self, 'auto_purchase_var') and self.auto_purchase_var:
                self.auto_purchase_var.set(preset_data.get('auto_purchase_enabled', False))
            if hasattr(self, 'amount_var') and self.amount_var:
                self.amount_var.set(self.auto_purchase_amount)
            if hasattr(self, 'loops_var') and self.loops_var:
                self.loops_var.set(self.loops_per_purchase)
            if hasattr(self, 'purchase_interval') and self.purchase_interval:
                self.purchase_interval.set(preset_data.get('purchase_interval', 0))
                
                                            
            if hasattr(self, 'fruit_storage_var') and self.fruit_storage_var:
                self.fruit_storage_var.set(preset_data.get('fruit_storage_enabled', False))
                print(f"   ✓ Fruit Storage: {preset_data.get('fruit_storage_enabled', False)}")
                
                                        
            if hasattr(self, 'auto_bait_var') and self.auto_bait_var:
                self.auto_bait_var.set(preset_data.get('auto_bait_enabled', False))
                print(f"   ✓ Auto Bait: {preset_data.get('auto_bait_enabled', False)}")
                
                                      
            if hasattr(self, 'webhook_var') and self.webhook_var:
                self.webhook_var.set(preset_data.get('webhook_enabled', False))
                print(f"   ✓ Webhook: {preset_data.get('webhook_enabled', False)}")
            if hasattr(self, 'webhook_enabled_var') and self.webhook_enabled_var:
                self.webhook_enabled_var.set(self.webhook_enabled)
            if hasattr(self, 'webhook_url_var') and self.webhook_url_var:
                self.webhook_url_var.set(self.webhook_url)
            if hasattr(self, 'webhook_interval_var') and self.webhook_interval_var:
                self.webhook_interval_var.set(self.webhook_interval)

            
                                                                   
            if hasattr(self, 'fish_progress_webhook_var') and self.fish_progress_webhook_var:
                self.fish_progress_webhook_var.set(self.fish_progress_webhook_enabled)
            if hasattr(self, 'devil_fruit_webhook_var') and self.devil_fruit_webhook_var:
                self.devil_fruit_webhook_var.set(self.devil_fruit_webhook_enabled)
            if hasattr(self, 'fruit_spawn_webhook_var') and self.fruit_spawn_webhook_var:
                self.fruit_spawn_webhook_var.set(self.fruit_spawn_webhook_enabled)
            if hasattr(self, 'purchase_webhook_var') and self.purchase_webhook_var:
                self.purchase_webhook_var.set(self.purchase_webhook_enabled)
            if hasattr(self, 'recovery_webhook_var') and self.recovery_webhook_var:
                self.recovery_webhook_var.set(self.recovery_webhook_enabled)
            if hasattr(self, 'bait_webhook_var') and self.bait_webhook_var:
                self.bait_webhook_var.set(self.bait_webhook_enabled)
            
                                                     
            if hasattr(self, 'auto_bait_var') and self.auto_bait_var:
                self.auto_bait_var.set(self.auto_bait_enabled)
            


            
                                      
            self.update_bait_buttons()

            
                               
            ocr_settings = preset_data.get('ocr_settings', {})
            if hasattr(self, 'ocr_enabled_var') and self.ocr_enabled_var:
                self.ocr_enabled_var.set(ocr_settings.get('enabled', True))
            if hasattr(self, 'tesseract_path_var') and self.tesseract_path_var:
                self.tesseract_path_var.set(ocr_settings.get('tesseract_path', 
                    'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'))
            
                                                                              
            try:
                zoom_settings = preset_data.get('zoom_settings', {})
                self.auto_zoom_enabled = zoom_settings.get('auto_zoom_enabled', False)
                self.auto_mouse_position_enabled = zoom_settings.get('auto_mouse_position_enabled', False)
                if hasattr(self, 'auto_zoom_var') and self.auto_zoom_var:
                    self.auto_zoom_var.set(self.auto_zoom_enabled)
                if hasattr(self, 'zoom_var') and self.zoom_var:
                    self.zoom_var.set(self.auto_zoom_enabled)
                if hasattr(self, 'auto_mouse_position_var') and self.auto_mouse_position_var:
                    self.auto_mouse_position_var.set(self.auto_mouse_position_enabled)
                if hasattr(self, 'mouse_pos_var') and self.mouse_pos_var:
                    self.mouse_pos_var.set(self.auto_mouse_position_enabled)
                if hasattr(self, 'zoom_out_var') and self.zoom_out_var:
                    self.zoom_out_var.set(zoom_settings.get('zoom_out_steps', 5))
                if hasattr(self, 'zoom_in_var') and self.zoom_in_var:
                    self.zoom_in_var.set(zoom_settings.get('zoom_in_steps', 8))
            except AttributeError:
                pass                                      
            
                                                  
            try:
                if hasattr(self, 'ocr_manager') and ocr_settings.get('tesseract_path'):
                    self.ocr_manager = OCRManager(ocr_settings['tesseract_path'])
                
                if hasattr(self, 'zoom_controller'):
                    zoom_settings = preset_data.get('zoom_settings', {})
                    self.zoom_controller.update_settings({
                        'zoom_out_steps': zoom_settings.get('zoom_out_steps', 5),
                        'zoom_in_steps': zoom_settings.get('zoom_in_steps', 8),
                        'step_delay': zoom_settings.get('step_delay', 0.1),
                        'sequence_delay': zoom_settings.get('sequence_delay', 0.5),
                        'zoom_cooldown': zoom_settings.get('zoom_cooldown', 2.0)
                    })
                                                          
                    self.update_zoom_controller_settings()
            except Exception:
                pass                                  
            
                                                    
            if hasattr(self, 'rod_key_entry'):
                self.rod_key_entry.delete(0, 'end')
                self.rod_key_entry.insert(0, self.rod_key)
            if hasattr(self, 'fruit_key_entry'):
                self.fruit_key_entry.delete(0, 'end')
                self.fruit_key_entry.insert(0, self.fruit_storage_key)
            if hasattr(self, 'fruit_key_2_entry'):
                self.fruit_key_2_entry.delete(0, 'end')
                self.fruit_key_2_entry.insert(0, self.fruit_storage_key_2)
            if hasattr(self, 'webhook_entry'):
                self.webhook_entry.delete(0, 'end')
                self.webhook_entry.insert(0, self.webhook_url)
            
                                                   
            if hasattr(self, 'point_buttons'):
                for idx, coords in self.point_coords.items():
                    if idx in self.point_buttons:
                        self.point_buttons[idx].config(text=f'✓ Point {idx}: ({coords[0]}, {coords[1]})')
            
                                                
            if self.fruit_coords.get('fruit_point') and hasattr(self, 'fruit_point_btn'):
                coords = self.fruit_coords['fruit_point']
                self.fruit_point_btn.config(text=f'✓ Fruit 1: ({coords[0]}, {coords[1]})')
            if self.fruit_coords.get('fruit_point_2') and hasattr(self, 'fruit_point_2_btn'):
                coords = self.fruit_coords['fruit_point_2']
                self.fruit_point_2_btn.config(text=f'✓ Fruit 2 (Backup): ({coords[0]}, {coords[1]})')
            
                                       
            if self.top_bait_coords and hasattr(self, 'top_bait_btn'):
                coords = self.top_bait_coords
                self.top_bait_btn.config(text=f'✓ Bait 1: ({coords[0]}, {coords[1]})')
            if self.top_bait_coords_2 and hasattr(self, 'top_bait_2_btn'):
                coords = self.top_bait_coords_2
                self.top_bait_2_btn.config(text=f'✓ Bait 2 (Backup): ({coords[0]}, {coords[1]})')
            
                                   
            self.fishing_location = preset_data.get('fishing_location', None)
            
                                
            if hasattr(self, 'point_buttons'):
                self.update_point_buttons()
            if hasattr(self, 'fruit_point_button') or hasattr(self, 'bait_point_button') or hasattr(self, 'fishing_location_button'):
                self.update_fruit_storage_buttons()
            if hasattr(self, 'auto_update_btn'):
                self.update_auto_update_button()
            
            print(f"✅ UI settings applied successfully!")
            
                                                            
            self._loading_settings = False
            print(f"▶️ Auto-save enabled\n")
            
        except Exception as e:
            print(f'❌ Error loading UI settings: {e}')
            self._loading_settings = False                                         

    def update_point_buttons(self):
        """Update point button texts with coordinates"""
        for idx, coords in self.point_coords.items():
            if coords and idx in self.point_buttons:
                self.point_buttons[idx].config(text=f'Point {idx}: {coords}')
    
    def update_fruit_storage_buttons(self):
        """Update fruit storage button texts with coordinates"""
        if hasattr(self, 'fruit_coords'):
            if hasattr(self, 'fruit_point_button') and 'fruit_point' in self.fruit_coords:
                coords = self.fruit_coords['fruit_point']
                self.fruit_point_button.config(text=f'Fruit Point: {coords}')
            if hasattr(self, 'fruit_point_2_button') and 'fruit_point_2' in self.fruit_coords:
                coords = self.fruit_coords['fruit_point_2']
                self.fruit_point_2_button.config(text=f'Fruit Point 2: {coords}')
            if hasattr(self, 'bait_point_button') and 'bait_point' in self.fruit_coords:
                coords = self.fruit_coords['bait_point']
                self.bait_point_button.config(text=f'Bait Point: {coords}')
        
                                        
        if hasattr(self, 'fishing_location_button') and hasattr(self, 'fishing_location') and self.fishing_location:
            coords = self.fishing_location
            self.fishing_location_button.config(text=f'🎯 Location: {coords}')

    def update_bait_buttons(self):
        """Update bait button texts with coordinates"""
        if hasattr(self, 'bait_coords') and self.bait_coords:
            button_map = {
                'legendary': ('legendary_bait_button', 'Legendary'),
                'rare': ('rare_bait_button', 'Rare'),
                'common': ('common_bait_button', 'Common')
            }
            
            for bait_type, (button_attr, display_name) in button_map.items():
                if hasattr(self, button_attr) and bait_type in self.bait_coords and self.bait_coords[bait_type]:
                    button = getattr(self, button_attr)
                    coords = self.bait_coords[bait_type]
                    button.config(text=f'{display_name}: ({coords[0]}, {coords[1]})')
        
                                
        if hasattr(self, 'top_bait_button') and hasattr(self, 'top_bait_coords') and self.top_bait_coords:
            x, y = self.top_bait_coords
            self.top_bait_button.config(text=f'Top Bait: ({x}, {y})')

    def update_hotkey_labels(self):
        """Update hotkey label texts"""
        try:
            self.loop_key_label.config(text=self.hotkeys['toggle_loop'].upper())

            self.exit_key_label.config(text=self.hotkeys['exit'].upper())
            self.minimize_key_label.config(text=self.hotkeys['toggle_minimize'].upper())
        except AttributeError:
            pass                          


def main():
    root = tk.Tk()
    app = HotkeyGUI(root)
    root.protocol('WM_DELETE_WINDOW', app.exit_app)
    root.mainloop()

if __name__ == '__main__':
    main()

if __name__ == '__main__':
    main()