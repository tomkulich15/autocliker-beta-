import time
import PySimpleGUI as sg
from pynput import mouse
import threading
from typing import List, Tuple, Union
import ctypes
import json
import os

Action = Union[Tuple[int, int], str]

class Autoclicker:
    def __init__(self):
        self.positions: List[Action] = []
        self.adding_position = False
        self.config_file = 'autoclicker_config.json'
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
            return dpi / 96
        except Exception as e:
            self.log_message(f'Error getting DPI scaling: {e}')
            return 1.0

    def perform_actions(self, actions: List[Action], wait_time: float, dpi_scaling: float, scroll_up_amount: float, scroll_down_amount: float):
        mouse_controller = mouse.Controller()
        for action in actions:
            try:
                if isinstance(action, tuple):
                    adjusted_pos = (int(action[0] / dpi_scaling), int(action[1] / dpi_scaling))
                    self.log_message(f'Clicking at position ({adjusted_pos[0]}, {adjusted_pos[1]})')
                    mouse_controller.position = adjusted_pos
                    mouse_controller.click(mouse.Button.left)
                elif action == 'scroll_up':
                    self.log_message(f'Scrolling up {scroll_up_amount} pixels')
                    mouse_controller.scroll(0, scroll_up_amount)
                elif action == 'scroll_down':
                    self.log_message(f'Scrolling down {scroll_down_amount} pixels')
                    mouse_controller.scroll(0, -scroll_down_amount)
                time.sleep(wait_time)
            except Exception as e:
                self.log_message(f'Error performing action {action}: {e}')

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
            self.positions.append(action)
            self.window.write_event_value('-POSITION_ADDED-', action)
            self.adding_position = False
            return False
        return True

    def start_mouse_listener(self):
        listener = mouse.Listener(on_click=self.on_click, on_scroll=self.on_scroll)
        listener.start()
        listener.join()

    def log_message(self, message: str):
        if self.window:
            self.window['log'].print(message)
        print(message)

    def save_config(self):
        config = {'positions': self.positions}
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
            self.log_message('Configuration saved.')
        except Exception as e:
            self.log_message(f'Error saving configuration: {e}')

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                self.positions = config.get('positions', [])
                if self.window:
                    self.window['positions_list'].update(values=[f'{p}' for p in self.positions])
                self.log_message('Configuration loaded.')
            except Exception as e:
                self.log_message(f'Error loading configuration: {e}')
        else:
            self.log_message(f'Configuration file {self.config_file} does not exist.')

    def clear_positions(self):
        self.positions.clear()
        if self.window:
            self.window['positions_list'].update(values=[])
        self.log_message('All positions cleared.')

    def run(self):
        layout = [
            [sg.Text('Autoclicker', size=(30, 1), justification='center', font=('Helvetica', 16))],
            [sg.Text('Click Position (x, y) or Scroll Action:')],
            [sg.InputText(key='position', size=(20, 1), disabled=True),
             sg.Button('+ Add Click Position'),
             sg.Button('+ Add Scroll Up'),
             sg.Button('+ Add Scroll Down'),
             sg.Button('- Remove Last Action')],
            [sg.Text('Wait time (seconds):')],
            [sg.Slider(range=(0, 10), orientation='h', size=(20, 15), default_value=1, resolution=0.1, key='wait')],
            [sg.Text('Number of actions to perform:')],
            [sg.Slider(range=(1, 10), orientation='h', size=(20, 15), default_value=1, key='count')],
            [sg.Text('Scroll up amount (pixels):')],
            [sg.Slider(range=(0.5, 100), orientation='h', size=(20, 15), default_value=10, resolution=0.5, key='scroll_up_amount')],
            [sg.Text('Scroll down amount (pixels):')],
            [sg.Slider(range=(0.5, 100), orientation='h', size=(20, 15), default_value=10, resolution=0.5, key='scroll_down_amount')],
            [sg.Button('Start'), sg.Button('Stop'), sg.Button('Exit')],
            [sg.Listbox(values=[], size=(50, 10), key='positions_list')],
            [sg.Text('LOG', size=(10, 1), font=('Helvetica', 12), pad=((0, 0), (0, 0)))],
            [sg.Multiline(size=(50, 5), key='log', autoscroll=True, disabled=True)],
            [sg.Button('Save Config'), sg.Button('Load Config'), sg.Button('Clear All')],
            [sg.Text('DPI Scaling Factor:'), sg.InputText(default_text=str(self.dpi_scaling), size=(5, 1), key='dpi_scaling')]
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
                    self.positions.append('scroll_up')
                    self.window['positions_list'].update(values=[f'{p}' for p in self.positions])
                    self.log_message('Added scroll up action.')
                elif event == '+ Add Scroll Down':
                    self.positions.append('scroll_down')
                    self.window['positions_list'].update(values=[f'{p}' for p in self.positions])
                    self.log_message('Added scroll down action.')
                elif event == '- Remove Last Action':
                    if self.positions:
                        action = self.positions.pop()
                        self.window['positions_list'].update(values=[f'{p}' for p in self.positions])
                        self.log_message(f'Removed action: {action}')
                    else:
                        self.log_message('No actions to remove.')
                elif event == 'Start':
                    try:
                        count = int(values['count'])
                        wait_time = float(values['wait'])
                        dpi_scaling = float(values['dpi_scaling'])
                        scroll_up_amount = float(values['scroll_up_amount'])
                        scroll_down_amount = float(values['scroll_down_amount'])

                        self.log_message(f'Starting autoclicker for {count} times...')
                        for _ in range(count):
                            self.perform_actions(self.positions, wait_time, dpi_scaling, scroll_up_amount, scroll_down_amount)
                            time.sleep(wait_time)
                        self.log_message('Autoclicker finished.')
                    except ValueError:
                        self.log_message('Invalid input. Please enter numeric values.')
                    except Exception as e:
                        self.log_message(f'Error: {e}')
                elif event == 'Stop':
                    self.log_message('Autoclicker stopped.')
                    self.adding_position = False
                elif event == '-POSITION_ADDED-':
                    action = values[event]
                    if isinstance(action, tuple):
                        self.window['position'].update(f'{action[0]}, {action[1]}')
                    else:
                        self.window['position'].update(action)
                    self.window['positions_list'].update(values=[f'{p}' for p in self.positions])
                    self.log_message(f'Added action: {action}')
                elif event == 'Save Config':
                    self.save_config()
                elif event == 'Load Config':
                    self.load_config()
                elif event == 'Clear All':
                    self.clear_positions()
        except Exception as e:
            self.log_message(f'An error occurred: {e}')
        finally:
            self.window.close()

if __name__ == '__main__':
    autoclicker = Autoclicker()
    autoclicker.run()
