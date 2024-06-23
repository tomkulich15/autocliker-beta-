import time
import PySimpleGUI as sg
from pynput import mouse
import threading
from typing import List, Tuple, Union
import ctypes
import json
import os

# Type alias for position and scroll actions
Action = Union[Tuple[int, int], str]

# Global variables
positions: List[Action] = []
adding_position = False
window = None
config_file = 'autoclicker_config.json'

# Function to get the current DPI scaling
def get_dpi_scaling() -> float:
    try:
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()
        hdc = user32.GetDC(0)
        dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)
        user32.ReleaseDC(0, hdc)
        return dpi / 96  # 96 is the default DPI scaling (100%)
    except Exception as e:
        log_message(f'Error getting DPI scaling: {e}')
        return 1.0

# Function for clicking and scrolling at specified positions
def perform_actions(actions: List[Action], wait_time: float, dpi_scaling: float, scroll_amount: int):
    mouse_controller = mouse.Controller()
    for action in actions:
        try:
            if isinstance(action, tuple):  # Click action
                adjusted_pos = (int(action[0] / dpi_scaling), int(action[1] / dpi_scaling))
                log_message(f'Clicking at position ({adjusted_pos[0]}, {adjusted_pos[1]})')
                mouse_controller.position = adjusted_pos
                mouse_controller.click(mouse.Button.left)
            elif action == 'scroll_up':  # Scroll up action
                log_message(f'Scrolling up {scroll_amount} pixels')
                mouse_controller.scroll(0, scroll_amount)
            elif action == 'scroll_down':  # Scroll down action
                log_message(f'Scrolling down {scroll_amount} pixels')
                mouse_controller.scroll(0, -scroll_amount)
            time.sleep(wait_time)  # Time delay between actions
        except Exception as e:
            log_message(f'Error performing action {action}: {e}')

# Function to handle mouse click events
def on_click(x: int, y: int, button, pressed: bool):
    global adding_position, window
    if pressed and adding_position:
        scale_factor = get_dpi_scaling()
        scaled_x = int(x * scale_factor)
        scaled_y = int(y * scale_factor)
        positions.append((scaled_x, scaled_y))
        window.write_event_value('-POSITION_ADDED-', (scaled_x, scaled_y))
        adding_position = False
        return False  # Stop listener
    return True  # Continue listener

# Function to handle mouse scroll events
def on_scroll(x, y, dx, dy):
    global adding_position, window
    if adding_position:
        action = 'scroll_up' if dy > 0 else 'scroll_down'
        positions.append(action)
        window.write_event_value('-POSITION_ADDED-', action)
        adding_position = False
        return False  # Stop listener
    return True  # Continue listener

# Function to log messages to the output box
def log_message(message: str):
    if window:
        window['log'].print(message)
    print(message)  # Also print to the console for debug purposes

# Mouse listener thread function
def mouse_listener_thread():
    with mouse.Listener(on_click=on_click, on_scroll=on_scroll) as listener:
        listener.join()

# Save configuration to a file
def save_config(file_name=config_file):
    config = {
        'positions': positions,
    }
    try:
        with open(file_name, 'w') as f:
            json.dump(config, f)
        log_message('Configuration saved.')
    except Exception as e:
        log_message(f'Error saving configuration: {e}')

# Load configuration from a file
def load_config(file_name=config_file):
    global positions, window
    if os.path.exists(file_name):
        try:
            with open(file_name, 'r') as f:
                config = json.load(f)
            positions = config.get('positions', [])
            window['positions_list'].update(values=[f'{p}' for p in positions])
            log_message('Configuration loaded.')
        except Exception as e:
            log_message(f'Error loading configuration: {e}')
    else:
        log_message(f'Configuration file {file_name} does not exist.')

# Clear all positions
def clear_positions():
    global positions, window
    positions.clear()
    window['positions_list'].update(values=[])
    log_message('All positions cleared.')

# Main function to run the application
def main():
    global window, adding_position

    # Get the current DPI scaling
    dpi_scaling = get_dpi_scaling()
    log_message(f'Detected DPI scaling: {dpi_scaling * 100:.2f}%')

    # Define layout
    layout = [
        [sg.Text('Autoclicker', size=(30, 1), justification='center', font=('Helvetica', 16))],
        [sg.Text('Click Position (x, y) or Scroll Action:')],
        [sg.InputText(key='position', size=(20, 1), disabled=True),
         sg.Button('+ Add Click Position'),
         sg.Button('+ Add Scroll Up'),
         sg.Button('+ Add Scroll Down'),
         sg.Button('- Remove Last Action')],
        [sg.Text('Wait time (seconds):')],
        [sg.Slider(range=(0, 10), orientation='h', size=(20, 15), default_value=1, key='wait')],
        [sg.Text('Number of actions to perform:')],
        [sg.Slider(range=(1, 10), orientation='h', size=(20, 15), default_value=1, key='count')],
        [sg.Text('Scroll amount (pixels):')],
        [sg.Slider(range=(1, 100), orientation='h', size=(20, 15), default_value=10, key='scroll_amount')],
        [sg.Button('Start'), sg.Button('Stop'), sg.Button('Exit')],
        [sg.Listbox(values=[], size=(50, 10), key='positions_list')],
        [sg.Text('LOG', size=(10, 1), font=('Helvetica', 12), pad=((0, 0), (0, 0)))],
        [sg.Multiline(size=(50, 5), key='log', autoscroll=True, disabled=True)],
        [sg.Button('Save Config'), sg.Button('Load Config'), sg.Button('Clear All')],
        [sg.Text('DPI Scaling Factor:'), sg.InputText(default_text=str(dpi_scaling), size=(5, 1), key='dpi_scaling')]
    ]

    window = sg.Window('Autoclicker', layout, finalize=True)

    try:
        load_config()

        while True:
            event, values = window.read()

            if event == sg.WIN_CLOSED or event == 'Exit':
                save_config()
                break
            elif event == '+ Add Click Position':
                window['position'].update('Click anywhere to add position...')
                adding_position = True
                threading.Thread(target=mouse_listener_thread, daemon=True).start()

            elif event == '+ Add Scroll Up':
                positions.append('scroll_up')
                window['positions_list'].update(values=[f'{p}' for p in positions])
                log_message('Added scroll up action.')

            elif event == '+ Add Scroll Down':
                positions.append('scroll_down')
                window['positions_list'].update(values=[f'{p}' for p in positions])
                log_message('Added scroll down action.')

            elif event == '- Remove Last Action':
                if positions:
                    action = positions.pop()
                    window['positions_list'].update(values=[f'{p}' for p in positions])
                    log_message(f'Removed action: {action}')
                else:
                    log_message('No actions to remove.')

            elif event == 'Start':
                try:
                    count = int(values['count'])
                    wait_time = float(values['wait'])
                    dpi_scaling = float(values['dpi_scaling'])
                    scroll_amount = int(values['scroll_amount'])

                    log_message(f'Starting autoclicker for {count} times...')
                    for _ in range(count):
                        perform_actions(positions, wait_time, dpi_scaling, scroll_amount)
                        time.sleep(wait_time)

                    log_message('Autoclicker finished.')

                except ValueError:
                    log_message('Invalid input. Please enter numeric values.')
                except Exception as e:
                    log_message(f'Error: {e}')

            elif event == 'Stop':
                log_message('Autoclicker stopped.')
                adding_position = False

            elif event == '-POSITION_ADDED-':
                action = values[event]
                if isinstance(action, tuple):
                    window['position'].update(f'{action[0]}, {action[1]}')
                else:
                    window['position'].update(action)
                window['positions_list'].update(values=[f'{p}' for p in positions])
                log_message(f'Added action: {action}')

            elif event == 'Save Config':
                save_config()

            elif event == 'Load Config':
                load_config()

            elif event == 'Clear All':
                clear_positions()
    except Exception as e:
        log_message(f'An error occurred: {e}')
    finally:
        window.close()

if __name__ == '__main__':
    main()
