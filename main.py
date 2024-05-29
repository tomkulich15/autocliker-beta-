import time
import PySimpleGUI as sg
from pynput import mouse
import pyautogui

# Global variables
positions = []
adding_position = False
listener = None

# Function for clicking at specified positions
def click_positions(positions):
    for pos in positions:
        try:
            log_message(f'Moving to position ({pos[0]}, {pos[1]})')
            pyautogui.moveTo(pos[0], pos[1])  # Move to the position
            log_message(f'Clicking at position ({pos[0]}, {pos[1]})')
            pyautogui.click(pos[0], pos[1])  # Perform actual click
            time.sleep(1)  # Time delay between clicks
        except Exception as e:
            log_message(f'Error clicking at position ({pos[0]}, {pos[1]}): {e}')

# Function to handle mouse click events
def on_click(x, y, button, pressed):
    if pressed:
        global positions, window, adding_position, listener
        if adding_position:
            positions.append((x, y))
            window['position'].update(f'{x}, {y}')
            window['positions_list'].update(values=[f'({p[0]}, {p[1]})' for p in positions])
            log_message(f'Added position: ({x}, {y})')
            adding_position = False
            listener.stop()  # Stop the listener
        return False  # Stop listener

# Function to log messages to the output box
def log_message(message):
    window['log'].print(message)
    print(message)  # Also print to the console for debug purposes

# Main function to run the application
def main():
    global positions, window, adding_position, listener

    # Define layout
    layout = [
        [sg.Text('Autoclicker', size=(30, 1), justification='center', font=('Helvetica', 16))],
        [sg.Text('Click Position (x, y):')],
        [sg.InputText(key='position', size=(20, 1), disabled=True),
         sg.Button('+ Add Position'),
         sg.Button('- Remove Position')],
        [sg.Text('Wait time (seconds):')],
        [sg.Slider(range=(0, 10), orientation='h', size=(20, 15), default_value=1, key='wait')],
        [sg.Text('Number of actions to perform:')],
        [sg.Slider(range=(1, 10), orientation='h', size=(20, 15), default_value=1, key='count')],
        [sg.Button('Start'), sg.Button('Stop'), sg.Button('Exit')],
        [sg.Listbox(values=[], size=(50, 10), key='positions_list')],
        [sg.Text('LOG', size=(10, 1), font=('Helvetica', 12), pad=((0, 0), (0, 0)))],
        [sg.Multiline(size=(50, 5), key='log', autoscroll=True, disabled=True)]
    ]

    window = sg.Window('Autoclicker', layout)

    try:
        while True:
            event, values = window.read()

            if event == sg.WIN_CLOSED or event == 'Exit':
                break
            elif event == '+ Add Position':
                window['position'].update('Click anywhere to add position...')
                adding_position = True
                listener = mouse.Listener(on_click=on_click)
                listener.start()

            elif event == '- Remove Position':
                if positions:
                    pos = positions.pop()
                    window['positions_list'].update(values=[f'({p[0]}, {p[1]})' for p in positions])
                    log_message(f'Removed position: ({pos[0]}, {pos[1]})')
                    window['position'].update('')
                else:
                    log_message('No positions to remove.')

            elif event == 'Start':
                try:
                    count = int(values['count'])
                    wait_time = float(values['wait'])

                    log_message(f'Starting autoclicker for {count} times...')
                    for _ in range(count):
                        click_positions(positions)
                        time.sleep(wait_time)

                    log_message('Autoclicker finished.')

                except ValueError:
                    log_message('Invalid input. Please enter numeric values.')
                except Exception as e:
                    log_message(f'Error: {e}')

            elif event == 'Stop':
                log_message('Autoclicker stopped.')
                adding_position = False

    finally:
        if listener and listener.running:
            listener.stop()
        window.close()

if __name__ == '__main__':
    main()
