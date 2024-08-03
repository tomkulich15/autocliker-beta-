import time
import tkinter as tk
from tkinter import ttk, messagebox
from pynput import mouse, keyboard
import threading
from typing import List, Tuple, Union
import ctypes
import json
import os
import logging
import random

# Setting up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

Action = Union[Tuple[int, int], Tuple[str, float]]

# Configuration Constants
CONFIG_FILE = 'autoclicker_config.json'
DPI_SCALING_FACTOR = 96
WAIT_TIME_SLIDER_RANGE = (0, 10)
ACTION_COUNT_SLIDER_RANGE = (1, 500)
VERSION = "v0.0.9"

class Autoclicker:
    def __init__(self):
        self.positions: List[Action] = []
        self.adding_position = False
        self.window = None
        self.dpi_scaling = self.get_dpi_scaling()
        self.running = False
        self.last_action = None
        self.keyboard_listener = None
        self.start_mouse_listener_thread = None
        self.randomize_delays = False
        self.random_delay_range = 0.0
        self.start_key = 'f6'
        self.stop_key = 'f6'
        self.actions_listbox = None

        # Load configuration after initializing variables
        self.load_config()

    def get_dpi_scaling(self) -> float:
        """Retrieve the system DPI scaling factor."""
        try:
            user32 = ctypes.windll.user32
            user32.SetProcessDPIAware()
            hdc = user32.GetDC(0)
            dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)
            user32.ReleaseDC(0, hdc)
            return dpi / DPI_SCALING_FACTOR
        except Exception as e:
            logging.error(f'Error getting DPI scaling: {e}')
            return 1.0

    def perform_actions(self, actions: List[Action], wait_time: float, dpi_scaling: float):
        """Perform a series of actions."""
        mouse_controller = mouse.Controller()
        for action in actions:
            if not self.running:
                break
            try:
                if isinstance(action, tuple) and len(action) == 2 and isinstance(action[0], int):
                    adjusted_pos = (int(action[0] / dpi_scaling), int(action[1] / dpi_scaling))
                    mouse_controller.position = adjusted_pos
                    mouse_controller.click(mouse.Button.left)
                elif isinstance(action, tuple) and action[0] in ['scroll_up', 'scroll_down']:
                    scroll_amount = action[1] if action[0] == 'scroll_up' else -action[1]
                    mouse_controller.scroll(0, scroll_amount)

                # Apply randomization if enabled
                actual_wait_time = wait_time
                if self.randomize_delays:
                    actual_wait_time += random.uniform(-self.random_delay_range, self.random_delay_range)
                    actual_wait_time = max(0, actual_wait_time)  # Ensure wait time is not negative

                time.sleep(actual_wait_time)
            except Exception as e:
                logging.error(f'Error performing action {action}: {e}')

    def on_click(self, x: int, y: int, button, pressed: bool):
        """Handle mouse click events."""
        if pressed and self.adding_position:
            scale_factor = self.get_dpi_scaling()
            scaled_x = int(x * scale_factor)
            scaled_y = int(y * scale_factor)
            self.last_action = (scaled_x, scaled_y)
            self.positions.append(self.last_action)
            self.update_actions_list()
            self.adding_position = False
            return False
        return True

    def on_scroll(self, x, y, dx, dy):
        """Handle mouse scroll events."""
        if self.adding_position:
            action = 'scroll_up' if dy > 0 else 'scroll_down'
            amount = float(self.scroll_amount.get())
            self.last_action = (action, amount)
            self.positions.append(self.last_action)
            self.update_actions_list()
            self.adding_position = False
            return False
        return True

    def start_mouse_listener(self):
        """Start the mouse event listener."""
        listener = mouse.Listener(on_click=self.on_click, on_scroll=self.on_scroll)
        listener.start()
        listener.join()

    def save_config(self):
        """Save the current configuration to a file."""
        config = {
            'positions': self.positions,
            'start_key': self.start_key,
            'stop_key': self.stop_key
        }
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f)
            logging.info('Configuration saved.')
        except Exception as e:
            logging.error(f'Error saving configuration: {e}')

    def load_config(self):
        """Load the configuration from a file."""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                self.positions = config.get('positions', [])
                self.start_key = config.get('start_key', 'f6')
                self.stop_key = config.get('stop_key', 'f6')
                logging.info('Configuration loaded.')
                self.update_actions_list()  # Update the actions list display
            except Exception as e:
                logging.error(f'Error loading configuration: {e}')
        else:
            logging.warning(f'Configuration file {CONFIG_FILE} does not exist.')

    def clear_positions(self):
        """Clear all recorded positions."""
        self.positions.clear()
        self.update_actions_list()
        logging.info('All positions cleared.')

    def run(self):
        """Run the main application."""
        self.window = tk.Tk()
        self.window.title('Autoclicker')
        self.window.geometry('405x850')  # Reduce window size
        self.window.resizable(False, False)
        self.window.configure(bg='#f0f0f0')
        self.window.attributes('-topmost', True)  # Make window stay on top

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TLabelframe', background='#f0f0f0')
        style.configure('TLabelframe.Label', background='#f0f0f0')
        style.configure('TButton', background='#e0e0e0')
        style.configure('TLabel', background='#f0f0f0')
        style.configure('TScale', background='#f0f0f0')

        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Label(main_frame, text='Autoclicker', font=('Helvetica', 14)).grid(column=0, row=0, columnspan=3)

        # Actions Frame
        actions_frame = ttk.LabelFrame(main_frame, text='Actions', padding="5")
        actions_frame.grid(column=0, row=1, columnspan=3, sticky=(tk.W, tk.E))

        self.position_var = tk.StringVar()
        ttk.Label(actions_frame, text='Click Position (x, y) or Scroll Action:').grid(column=0, row=0, columnspan=2)
        ttk.Entry(actions_frame, textvariable=self.position_var, state='readonly', width=20).grid(column=0, row=1)
        ttk.Button(actions_frame, text='+ Click', command=self.add_click, width=8).grid(column=1, row=1)

        ttk.Label(actions_frame, text='Scroll amount:').grid(column=0, row=2)
        self.scroll_amount = ttk.Entry(actions_frame, width=5)
        self.scroll_amount.insert(0, '10')
        self.scroll_amount.grid(column=1, row=2)
        ttk.Button(actions_frame, text='+ Up', command=lambda: self.add_scroll('up'), width=5).grid(column=2, row=2)
        ttk.Button(actions_frame, text='+ Down', command=lambda: self.add_scroll('down'), width=6.5).grid(column=3, row=2)

        # Settings Frame
        settings_frame = ttk.LabelFrame(main_frame, text='Settings', padding="5")
        settings_frame.grid(column=0, row=2, columnspan=3, sticky=(tk.W, tk.E))

        ttk.Label(settings_frame, text='Wait time (s):').grid(column=0, row=0)
        self.wait_time = ttk.Scale(settings_frame, from_=WAIT_TIME_SLIDER_RANGE[0], to=WAIT_TIME_SLIDER_RANGE[1], orient=tk.HORIZONTAL, length=180)
        self.wait_time.set(1)
        self.wait_time.grid(column=1, row=0)

        self.wait_time_value_label = ttk.Label(settings_frame, text='1.0')
        self.wait_time_value_label.grid(column=2, row=0, padx=10)
        self.wait_time.bind("<Motion>", self.update_wait_time_value)

        ttk.Label(settings_frame, text='Repetitions:').grid(column=0, row=1)
        self.count = ttk.Scale(settings_frame, from_=ACTION_COUNT_SLIDER_RANGE[0], to=ACTION_COUNT_SLIDER_RANGE[1], orient=tk.HORIZONTAL, length=180)
        self.count.set(1)
        self.count.grid(column=1, row=1)

        self.count_value_label = ttk.Label(settings_frame, text='1')
        self.count_value_label.grid(column=2, row=1, padx=10)
        self.count.bind("<Motion>", self.update_count_value)

        # Random Delays
        self.randomize_delays_var = tk.IntVar(value=0)
        self.randomize_delays_checkbox = ttk.Checkbutton(settings_frame, text="Randomize Delays", variable=self.randomize_delays_var, command=self.toggle_randomize_delays)
        self.randomize_delays_checkbox.grid(column=0, row=2, columnspan=2, sticky=tk.W)

        ttk.Label(settings_frame, text='Random Range (s):').grid(column=0, row=3)
        self.random_delay_range = ttk.Scale(settings_frame, from_=0, to=5, orient=tk.HORIZONTAL, length=180)
        self.random_delay_range.set(0)
        self.random_delay_range.grid(column=1, row=3)

        self.random_delay_range_value_label = ttk.Label(settings_frame, text='0.0')
        self.random_delay_range_value_label.grid(column=2, row=3, padx=10)
        self.random_delay_range.bind("<Motion>", self.update_random_delay_range_value)
        
        ttk.Button(settings_frame, text='- Remove Last', command=self.remove_last, width=15).grid(column=0, row=4, pady=5)
        # Removed "Clear Positions" button
        ttk.Button(settings_frame, text='Preview Actions', command=self.preview_actions, width=15).grid(column=0, row=5, pady=5)
        
        # Start/Stop Controls
        control_frame = ttk.LabelFrame(main_frame, text='Controls', padding="5")
        control_frame.grid(column=0, row=3, columnspan=3, sticky=(tk.W, tk.E))

        self.start_button = ttk.Button(control_frame, text='Start', command=self.start_autoclicker, width=8)
        self.start_button.grid(column=0, row=0)

        self.stop_button = ttk.Button(control_frame, text='Stop', command=self.stop_autoclicker, width=8)
        self.stop_button.grid(column=1, row=0)

        # Keybind Settings
        keybind_frame = ttk.LabelFrame(main_frame, text='Keybind Settings', padding="5")
        keybind_frame.grid(column=0, row=4, columnspan=3, sticky=(tk.W, tk.E))

        ttk.Label(keybind_frame, text='Start Key:').grid(column=0, row=0)
        self.start_key_entry = ttk.Entry(keybind_frame, width=10)
        self.start_key_entry.insert(0, self.start_key)
        self.start_key_entry.grid(column=1, row=0)
        ttk.Button(keybind_frame, text='Set Start Key', command=self.set_start_key, width=15).grid(column=2, row=0)

        ttk.Label(keybind_frame, text='Stop Key:').grid(column=0, row=1)
        self.stop_key_entry = ttk.Entry(keybind_frame, width=10)
        self.stop_key_entry.insert(0, self.stop_key)
        self.stop_key_entry.grid(column=1, row=1)
        ttk.Button(keybind_frame, text='Set Stop Key', command=self.set_stop_key, width=15).grid(column=2, row=1)

        self.keyboard_listener = keyboard.Listener(on_press=self.on_key_press)
        self.keyboard_listener.start()

        # Actions List Frame
        actions_list_frame = ttk.LabelFrame(main_frame, text='Actions List', padding="5")
        actions_list_frame.grid(column=0, row=5, columnspan=3, sticky=(tk.W, tk.E))

        self.actions_listbox = tk.Listbox(actions_list_frame, height=8)
        self.actions_listbox.grid(column=0, row=0, columnspan=3)

        self.update_actions_list()

        # Save, Load, Clear All Buttons
        ttk.Button(actions_list_frame, text='Save', command=self.save_config, width=10).grid(column=0, row=1, pady=5)
        ttk.Button(actions_list_frame, text='Load', command=self.load_config, width=10).grid(column=1, row=1, pady=5)
        ttk.Button(actions_list_frame, text='Clear All', command=self.clear_positions, width=10).grid(column=2, row=1, pady=5)

        self.window.mainloop()
    
    def add_click(self):
        """Start adding a click position."""
        self.adding_position = True
        self.start_mouse_listener_thread = threading.Thread(target=self.start_mouse_listener)
        self.start_mouse_listener_thread.start()

    def add_scroll(self, direction: str):
        """Add a scroll action."""
        amount = float(self.scroll_amount.get())
        self.positions.append((f'scroll_{direction}', amount))
        self.update_actions_list()

    def update_actions_list(self):
        """Update the displayed list of positions."""
        if self.actions_listbox:
            self.actions_listbox.delete(0, tk.END)
            for pos in self.positions:
                self.actions_listbox.insert(tk.END, pos)

    def remove_last(self):
        """Remove the last recorded action."""
        if self.positions:
            self.positions.pop()
        self.update_actions_list()

    def start_autoclicker(self):
        """Start the autoclicker with the configured actions."""
        self.running = True
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        repetitions = int(self.count.get())
        wait_time = self.wait_time.get()
        for _ in range(repetitions):
            if not self.running:
                break
            self.perform_actions(self.positions, wait_time, self.get_dpi_scaling())
        self.running = False
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')

    def stop_autoclicker(self):
        """Stop the autoclicker."""
        self.running = False
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')

    def on_key_press(self, key):
        """Handle key press events."""
        try:
            if hasattr(key, 'char'):
                key_char = key.char
            else:
                key_char = str(key).replace("'", "").lower()

            if key_char == self.start_key and not self.running:
                self.start_autoclicker()
            elif key_char == self.stop_key and self.running:
                self.stop_autoclicker()
        except AttributeError:
            pass

    def toggle_randomize_delays(self):
        """Toggle randomize delays option."""
        self.randomize_delays = bool(self.randomize_delays_var.get())

    def update_wait_time_value(self, event):
        """Update the display value of wait time."""
        self.wait_time_value_label.config(text=f'{self.wait_time.get():.1f}')

    def update_count_value(self, event):
        """Update the display value of action count."""
        self.count_value_label.config(text=f'{int(self.count.get())}')

    def update_random_delay_range_value(self, event):
        """Update the display value of random delay range."""
        self.random_delay_range_value_label.config(text=f'{self.random_delay_range.get():.1f}')

    def set_start_key(self):
        """Set the start key from the entry."""
        self.start_key = self.start_key_entry.get().lower()
        self.save_config()

    def set_stop_key(self):
        """Set the stop key from the entry."""
        self.stop_key = self.stop_key_entry.get().lower()
        self.save_config()

    def preview_actions(self):
        """Preview the list of actions in a message box."""
        actions_preview = '\n'.join(map(str, self.positions))
        messagebox.showinfo("Action Preview", f"Actions:\n{actions_preview}")

if __name__ == '__main__':
    autoclicker = Autoclicker()
    autoclicker.run()
