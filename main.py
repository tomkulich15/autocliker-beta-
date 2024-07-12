import time
import PySimpleGUI as sg
from pynput import mouse
import threading
from typing import List, Tuple, Union
import ctypes
import json
import os

Action = Union[Tuple[int, int], Tuple[str, float]]

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
            print(f'Error getting DPI scaling: {e}')
            return 1.0

    def perform_actions(self, actions: List[Action], wait_time: float, dpi_scaling: float):
        mouse_controller = mouse.Controller()
        for action in actions:
            try:
                if isinstance(action, tuple) and len(action) == 2 and isinstance(action[0], int):
                    adjusted_pos = (int(action[0] / dpi_scaling), int(action[1] / dpi_scaling))
                    mouse_controller.position = adjusted_pos
                    mouse_controller.click(mouse.Button.left)
                elif isinstance(action, tuple) and action[0] == 'scroll_up':
                    mouse_controller.scroll(0, action[1])
                elif isinstance(action, tuple) and action[0] == 'scroll_down':
                    mouse_controller.scroll(0, -action[1])
                time.sleep(wait_time)
            except Exception as e:
                print(f'Error performing action {action}: {e}')

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
            amount = self.window[f'{action}_amount'].get()
            self.positions.append((action, float(amount)))
            self.window.write_event_value('-POSITION_ADDED-', (action, float(amount)))
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
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
            print('Configuration saved.')
        except Exception as e:
            print(f'Error saving configuration: {e}')

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                self.positions = config.get('positions', [])
                if self.window:
                    self.window['positions_list'].update(values=[f'{p}' for p in self.positions])
                print('Configuration loaded.')
            except Exception as e:
                print(f'Error loading configuration: {e}')
        else:
            print(f'Configuration file {self.config_file} does not exist.')

    def clear_positions(self):
        self.positions.clear()
        if self.window:
            self.window['positions_list'].update(values=[])
        print('All positions cleared.')

    def run(self):
        layout = [
            [sg.Text('Autoclicker', size=(20, 1), justification='center', font=('Helvetica', 14))],
            [sg.Text('Click Position (x, y) or Scroll Action:')],
            [sg.InputText(key='position', size=(20, 1), disabled=True),
             sg.Button('+ Add Click Position')],
            [sg.Text('Scroll up amount (pixels):'), sg.InputText(default_text='10', size=(5, 1), key='scroll_up_amount'),
             sg.Button('+ Add Scroll Up')],
            [sg.Text('Scroll down amount (pixels):'), sg.InputText(default_text='10', size=(5, 1), key='scroll_down_amount'),
             sg.Button('+ Add Scroll Down')],
            [sg.Button('- Remove Last Action')],
            [sg.Text('Wait time (seconds):')],
            [sg.Slider(range=(0, 10), orientation='h', size=(20, 15), default_value=1, resolution=0.1, key='wait')],
            [sg.Text('Number of actions to perform:')],
            [sg.Slider(range=(1, 10), orientation='h', size=(20, 15), default_value=1, key='count')],
            [sg.Button('Start'), sg.Button('Stop'), sg.Button('Exit')],
            [sg.Listbox(values=[], size=(50, 10), key='positions_list')],
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
                    amount = float(values['scroll_up_amount'])
                    self.positions.append(('scroll_up', amount))
                    self.window['positions_list'].update(values=[f'{p}' for p in self.positions])
                    print('Added scroll up action.')
                elif event == '+ Add Scroll Down':
                    amount = float(values['scroll_down_amount'])
                    self.positions.append(('scroll_down', amount))
                    self.window['positions_list'].update(values=[f'{p}' for p in self.positions])
                    print('Added scroll down action.')
                elif event == '- Remove Last Action':
                    if self.positions:
                        action = self.positions.pop()
                        self.window['positions_list'].update(values=[f'{p}' for p in self.positions])
                        print(f'Removed action: {action}')
                    else:
                        print('No actions to remove.')
                elif event == 'Start':
                    try:
                        count = int(values['count'])
                        wait_time = float(values['wait'])
                        dpi_scaling = float(values['dpi_scaling'])

                        print(f'Starting autoclicker for {count} times...')
                        for _ in range(count):
                            self.perform_actions(self.positions, wait_time, dpi_scaling)
                            time.sleep(wait_time)
                        print('Autoclicker finished.')
                    except ValueError:
                        print('Invalid input. Please enter numeric values.')
                    except Exception as e:
                        print(f'Error: {e}')
                elif event == 'Stop':
                    print('Autoclicker stopped.')
                    self.adding_position = False
                elif event == '-POSITION_ADDED-':
                    action = values[event]
                    if isinstance(action, tuple):
                        self.window['position'].update(f'{action[0]}, {action[1]}')
                    else:
                        self.window['position'].update(f'{action[0]} {action[1]}')
                    self.window['positions_list'].update(values=[f'{p}' for p in self.positions])
                    print(f'Added action: {action}')
                elif event == 'Save Config':
                    self.save_config()
                elif event == 'Load Config':
                    self.load_config()
                elif event == 'Clear All':
                    self.clear_positions()
        except Exception as e:
            print(f'An error occurred: {e}')
        finally:
            self.window.close()

if __name__ == '__main__':
    autoclicker = Autoclicker()
    autoclicker.run()
