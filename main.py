import time
import PySimpleGUI as sg
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
ACTION_COUNT_SLIDER_RANGE = (1, 10)

class Autoclicker:
    def __init__(self):
        self.positions: List[Action] = []
        self.adding_position = False
        self.window = None
        self.load_config()
        self.dpi_scaling = self.get_dpi_scaling()

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
            self.positions.append((scaled_x, scaled_y))
            self.window.write_event_value('-POSITION_ADDED-', (scaled_x, scaled_y))
            self.adding_position = False
            return False
        return True

    def on_scroll(self, x, y, dx, dy):
        if self.adding_position:
            action = 'scroll_up' if dy > 0 else 'scroll_down'
            amount = float(self.window[f'{action}_amount'].get())
            self.positions.append((action, amount))
            self.window.write_event_value('-POSITION_ADDED-', (action, amount))
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
                if self.window:
                    self.window['positions_list'].update(values=[f'{p}' for p in self.positions])
                logging.info('Configuration loaded.')
            except Exception as e:
                logging.error(f'Error loading configuration: {e}')
        else:
            logging.warning(f'Configuration file {CONFIG_FILE} does not exist.')

    def clear_positions(self):
        self.positions.clear()
        if self.window:
            self.window['positions_list'].update(values=[])
        logging.info('All positions cleared.')

    def run(self):
        sg.theme('DarkBlue3')  # Set a theme for the window

        layout = [
            [sg.Text('Autoclicker', size=(20, 1), justification='center', font=('Helvetica', 18), relief=sg.RELIEF_RIDGE)],
            [sg.Frame(layout=[
                [sg.Text('Click Position (x, y) or Scroll Action:')],
                [sg.InputText(key='position', size=(25, 1), disabled=True),
                 sg.Button('+ Add Click Position')],
                [sg.Text('Scroll up amount (pixels):'), sg.InputText(default_text='10', size=(5, 1), key='scroll_up_amount'),
                 sg.Button('+ Add Scroll Up')],
                [sg.Text('Scroll down amount (pixels):'), sg.InputText(default_text='10', size=(5, 1), key='scroll_down_amount'),
                 sg.Button('+ Add Scroll Down')],
                [sg.Button('- Remove Last Action')]
            ], title='Actions', relief=sg.RELIEF_SUNKEN, title_color='yellow', pad=(10, 10))],
            [sg.Frame(layout=[
                [sg.Text('Wait time (seconds):')],
                [sg.Slider(range=WAIT_TIME_SLIDER_RANGE, orientation='h', size=(20, 15), default_value=1, resolution=0.1, key='wait')],
                [sg.Text('Number of actions to perform:')],
                [sg.Slider(range=ACTION_COUNT_SLIDER_RANGE, orientation='h', size=(20, 15), default_value=1, key='count')],
                [sg.Text('DPI Scaling Factor:'), sg.InputText(default_text=str(self.dpi_scaling), size=(5, 1), key='dpi_scaling')]
            ], title='Settings', relief=sg.RELIEF_SUNKEN, title_color='yellow', pad=(10, 10))],
            [sg.Button('Start'), sg.Button('Stop'), sg.Button('Exit')],
            [sg.Listbox(values=[], size=(50, 10), key='positions_list')],
            [sg.Button('Save Config'), sg.Button('Load Config'), sg.Button('Clear All')]
        ]

        self.window = sg.Window('Autoclicker', layout, finalize=True)

        try:
            self.load_config()
            while True:
                event, values = self.window.read()
                if event == sg.WIN_CLOSED or event == 'Exit':
                    self.save_config()
                    break
                elif event == '+ Add Click Position':
                    self.window['position'].update('Click anywhere to add position...')
                    self.adding_position = True
                    self.mouse_listener_thread = threading.Thread(target=self.start_mouse_listener, daemon=True)
                    self.mouse_listener_thread.start()
                elif event == '+ Add Scroll Up':
                    amount = float(values['scroll_up_amount'])
                    self.positions.append(('scroll_up', amount))
                    self.window['positions_list'].update(values=[f'{p}' for p in self.positions])
                    logging.info('Added scroll up action.')
                elif event == '+ Add Scroll Down':
                    amount = float(values['scroll_down_amount'])
                    self.positions.append(('scroll_down', amount))
                    self.window['positions_list'].update(values=[f'{p}' for p in self.positions])
                    logging.info('Added scroll down action.')
                elif event == '- Remove Last Action':
                    if self.positions:
                        action = self.positions.pop()
                        self.window['positions_list'].update(values=[f'{p}' for p in self.positions])
                        logging.info(f'Removed action: {action}')
                    else:
                        logging.warning('No actions to remove.')
                elif event == 'Start':
                    try:
                        count = int(values['count'])
                        wait_time = float(values['wait'])
                        dpi_scaling = float(values['dpi_scaling'])

                        logging.info(f'Starting autoclicker for {count} times...')
                        for _ in range(count):
                            self.perform_actions(self.positions, wait_time, dpi_scaling)
                            time.sleep(wait_time)
                        logging.info('Autoclicker finished.')
                    except ValueError:
                        logging.error('Invalid input. Please enter numeric values.')
                    except Exception as e:
                        logging.error(f'Error: {e}')
                elif event == 'Stop':
                    logging.info('Autoclicker stopped.')
                    self.adding_position = False
                elif event == '-POSITION_ADDED-':
                    action = values[event]
                    if isinstance(action, tuple):
                        self.window['position'].update(f'{action[0]}, {action[1]}')
                    else:
                        self.window['position'].update(f'{action[0]} {action[1]}')
                    self.window['positions_list'].update(values=[f'{p}' for p in self.positions])
                    logging.info(f'Added action: {action}')
                elif event == 'Save Config':
                    self.save_config()
                elif event == 'Load Config':
                    self.load_config()
                elif event == 'Clear All':
                    self.clear_positions()
        except Exception as e:
            logging.error(f'An error occurred: {e}')
        finally:
            self.window.close()

if __name__ == '__main__':
    autoclicker = Autoclicker()
    autoclicker.run()
