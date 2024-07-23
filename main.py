import time
import tkinter as tk
from tkinter import ttk, messagebox
from pynput import mouse
import threading
from typing import List, Tuple, Union
import ctypes
import json
import os
import logging

# Setting up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

Action = Union[Tuple[int, int], Tuple[str, float]]

# Configuration Constants
CONFIG_FILE = 'autoclicker_config.json'
DPI_SCALING_FACTOR = 96
WAIT_TIME_SLIDER_RANGE = (0, 10)
ACTION_COUNT_SLIDER_RANGE = (1, 100)
VERSION = "v0.0.5.3"

class Autoclicker:
    def __init__(self):
        self.positions: List[Action] = []
        self.adding_position = False
        self.window = None
        self.load_config()
        self.dpi_scaling = self.get_dpi_scaling()
        self.running = False
        self.last_action = None

    def get_dpi_scaling(self) -> float:
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
                time.sleep(wait_time)
            except Exception as e:
                logging.error(f'Error performing action {action}: {e}')

    def on_click(self, x: int, y: int, button, pressed: bool):
        if pressed and self.adding_position:
            scale_factor = self.get_dpi_scaling()
            scaled_x = int(x * scale_factor)
            scaled_y = int(y * scale_factor)
            self.last_action = (scaled_x, scaled_y)
            self.window.event_generate('<<PositionAdded>>')
            self.adding_position = False
            return False
        return True

    def on_scroll(self, x, y, dx, dy):
        if self.adding_position:
            action = 'scroll_up' if dy > 0 else 'scroll_down'
            amount = float(self.scroll_amount.get())
            self.last_action = (action, amount)
            self.window.event_generate('<<PositionAdded>>')
            self.adding_position = False
            return False
        return True

    def start_mouse_listener(self):
        listener = mouse.Listener(on_click=self.on_click, on_scroll=self.on_scroll)
        listener.start()
        listener.join()

    def save_config(self):
        config = {'positions': self.positions}
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f)
            logging.info('Configuration saved.')
        except Exception as e:
            logging.error(f'Error saving configuration: {e}')

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                self.positions = config.get('positions', [])
                if hasattr(self, 'positions_list'):
                    self.update_positions_list()
                logging.info('Configuration loaded.')
            except Exception as e:
                logging.error(f'Error loading configuration: {e}')
        else:
            logging.warning(f'Configuration file {CONFIG_FILE} does not exist.')

    def clear_positions(self):
        self.positions.clear()
        self.update_positions_list()
        logging.info('All positions cleared.')

    def run(self):
        self.window = tk.Tk()
        self.window.title('Autoclicker')
        self.window.geometry('395x700')  # Increased the height for additional controls
        self.window.resizable(False, False)  # Disable window resizing
        self.window.configure(bg='#e0e0e0')  # Set light gray background

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background='#e0e0e0')
        style.configure('TLabelframe', background='#e0e0e0')
        style.configure('TLabelframe.Label', background='#e0e0e0')
        style.configure('TButton', background='#d0d0d0')
        style.configure('TLabel', background='#e0e0e0')
        style.configure('TScale', background='#e0e0e0')

        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Label(main_frame, text='Autoclicker', font=('Helvetica', 16)).grid(column=0, row=0, columnspan=3)

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
        ttk.Button(actions_frame, text='+ Down', command=lambda: self.add_scroll('down'), width=5).grid(column=3, row=2)

        ttk.Button(actions_frame, text='- Remove Last', command=self.remove_last, width=12).grid(column=0, row=3, columnspan=2)

        # Settings Frame
        settings_frame = ttk.LabelFrame(main_frame, text='Settings', padding="5")
        settings_frame.grid(column=0, row=2, columnspan=3, sticky=(tk.W, tk.E))

        ttk.Label(settings_frame, text='Wait time (s):').grid(column=0, row=0)
        self.wait_time = ttk.Scale(settings_frame, from_=WAIT_TIME_SLIDER_RANGE[0], to=WAIT_TIME_SLIDER_RANGE[1], orient=tk.HORIZONTAL, length=200)
        self.wait_time.set(1)
        self.wait_time.grid(column=1, row=0)

        # Label to display current wait time value
        self.wait_time_value_label = ttk.Label(settings_frame, text='1.0')
        self.wait_time_value_label.grid(column=2, row=0, padx=10)

        # Update wait_time_value_label when the slider value changes
        self.wait_time.bind("<Motion>", self.update_wait_time_value)

        ttk.Label(settings_frame, text='Repetitions:').grid(column=0, row=1)
        self.count = ttk.Scale(settings_frame, from_=ACTION_COUNT_SLIDER_RANGE[0], to=ACTION_COUNT_SLIDER_RANGE[1], orient=tk.HORIZONTAL, length=200)
        self.count.set(1)
        self.count.grid(column=1, row=1)

        # Label to display current count value
        self.count_value_label = ttk.Label(settings_frame, text='1')
        self.count_value_label.grid(column=2, row=1, padx=10)

        # Update count_value_label when the slider value changes
        self.count.bind("<Motion>", self.update_count_value)

        ttk.Label(settings_frame, text='DPI Scale:').grid(column=0, row=2)
        self.dpi_scale_entry = ttk.Entry(settings_frame, width=5)
        self.dpi_scale_entry.insert(0, str(self.dpi_scaling))
        self.dpi_scale_entry.grid(column=1, row=2)

        # Action List Frame
        action_list_frame = ttk.LabelFrame(main_frame, text='Action List', padding="5")
        action_list_frame.grid(column=0, row=3, columnspan=3, sticky=(tk.W, tk.E))

        self.positions_list = tk.Listbox(action_list_frame, height=5, width=30)
        self.positions_list.grid(column=0, row=0, columnspan=3)

        ttk.Button(action_list_frame, text='Save', command=self.save_config, width=6).grid(column=0, row=1)
        ttk.Button(action_list_frame, text='Load', command=self.load_config, width=6).grid(column=1, row=1)
        ttk.Button(action_list_frame, text='Clear', command=self.clear_positions, width=6).grid(column=2, row=1)

        # Control Buttons
        start_button = tk.Button(main_frame, text='Start', command=self.start_autoclicker, bg='green', fg='white', width=8, height=1)
        start_button.grid(column=0, row=4, pady=10)
        stop_button = tk.Button(main_frame, text='Stop', command=self.stop_autoclicker, bg='red', fg='white', width=8, height=1)
        stop_button.grid(column=1, row=4, pady=10)
        ttk.Button(main_frame, text='Exit', command=self.exit_program, width=8).grid(column=2, row=4, pady=10)

        # Repetition Count Label
        self.repetition_label = ttk.Label(main_frame, text='Repetitions Remaining: 0')
        self.repetition_label.grid(column=0, row=5, columnspan=3, pady=10)

        ttk.Label(main_frame, text=f'Version: {VERSION}').grid(column=0, row=6, columnspan=3, sticky=tk.E)

        self.window.bind('<<PositionAdded>>', self.on_position_added)
        self.update_positions_list()
        self.window.mainloop()

    def update_wait_time_value(self, event):
        # Update wait_time_value_label with the current value of the wait time slider
        self.wait_time_value_label.config(text=f'{self.wait_time.get():.1f}')

    def update_count_value(self, event):
        # Update count_value_label with the current value of the count slider
        self.count_value_label.config(text=str(int(self.count.get())))

    def start_autoclicker(self):
        if not self.running:
            self.running = True
            threading.Thread(target=self.run_autoclicker, daemon=True).start()
            logging.info('Autoclicker started.')

    def stop_autoclicker(self):
        self.running = False
        logging.info('Autoclicker stopped.')

    def exit_program(self):
        self.stop_autoclicker()
        self.window.destroy()
        logging.info('Exiting program.')

    def update_positions_list(self):
        self.positions_list.delete(0, tk.END)
        for pos in self.positions:
            if isinstance(pos, tuple) and len(pos) == 2 and isinstance(pos[0], int):
                self.positions_list.insert(tk.END, f'Click at {pos}')
            elif isinstance(pos, tuple) and pos[0] in ['scroll_up', 'scroll_down']:
                self.positions_list.insert(tk.END, f'Scroll {pos[0]} by {pos[1]}')

    def add_click(self):
        self.adding_position = True
        self.last_action = None
        mouse_thread = threading.Thread(target=self.start_mouse_listener, daemon=True)
        mouse_thread.start()

    def add_scroll(self, direction: str):
        try:
            amount = float(self.scroll_amount.get())
            self.last_action = (f'scroll_{direction}', amount)
            self.window.event_generate('<<PositionAdded>>')
        except ValueError:
            logging.error('Invalid scroll amount. Please enter a numeric value.')
            messagebox.showerror("Error", "Invalid scroll amount. Please enter a numeric value.")

    def remove_last(self):
        if self.positions:
            self.positions.pop()
            self.update_positions_list()
            logging.info('Removed last position.')

    def on_position_added(self, event):
        if self.last_action:
            self.positions.append(self.last_action)
            self.update_positions_list()
            self.last_action = None

    def run_autoclicker(self):
        try:
            count = int(self.count.get())
            wait_time = float(self.wait_time.get())
            dpi_scaling = float(self.dpi_scale_entry.get())

            logging.info(f'Starting autoclicker for {count} repetitions...')
            for i in range(count):
                if not self.running:
                    break
                self.perform_actions(self.positions, wait_time, dpi_scaling)
                self.update_repetition_count(count - i - 1)  # Update the count after each repetition
                time.sleep(wait_time)
            logging.info('Autoclicker finished.')
        except ValueError:
            logging.error('Invalid input. Please enter numeric values.')
            messagebox.showerror("Error", "Invalid input. Please enter numeric values.")
        except Exception as e:
            logging.error(f'Error: {e}')
            messagebox.showerror("Error", f"An error occurred: {e}")
        finally:
            self.running = False

    def update_repetition_count(self, remaining_reps: int):
        # This method must be run in the main thread
        self.window.after(0, self.repetition_label.config, {'text': f'Repetitions Remaining: {remaining_reps}'})

if __name__ == "__main__":
    app = Autoclicker()
    app.run()
