# Mine-Autoclicker-Beta

## Overview

Mine-Autoclicker-Beta is a simple yet powerful tool that automates mouse clicks and scroll actions. It's designed to help you perform repetitive tasks effortlessly. This guide will walk you through the installation process and how to use the autoclicker.

## Installation

To get started with Mine-Autoclicker-Beta, you'll need to install the necessary dependencies. Run the following command to install them:

```bash
pip install PySimpleGUI pynput
```

## How to Use

1. **Launch the Autoclicker:**
   Run the Python script to open the Mine-Autoclicker-Beta GUI.

2. **Adding Click Positions:**
   - Click on the '+ Add Click Position' button.
   - Click anywhere on the screen to add the position. The position will be displayed in the 'Click Position (x, y) or Scroll Action' field and added to the list.

3. **Adding Scroll Actions:**
   - Enter the number of pixels for the scroll amount in the respective fields ('Scroll up amount (pixels):' or 'Scroll down amount (pixels):').
   - Click '+ Add Scroll Up' or '+ Add Scroll Down' to add the respective scroll action to the list.

4. **Removing Actions:**
   - Click the '- Remove Last Action' button to remove the most recent action from the list.

5. **Setting Wait Time:**
   - Use the 'Wait time (seconds):' slider to set the delay between actions.

6. **Setting Number of Actions:**
   - Use the 'Number of actions to perform:' slider to set how many times the autoclicker should repeat the actions.

7. **Starting the Autoclicker:**
   - Click the 'Start' button to begin the autoclicking process. The actions will be performed the specified number of times with the set wait time between them.

8. **Stopping the Autoclicker:**
   - Click the 'Stop' button to stop the autoclicker at any time.

9. **Saving and Loading Configurations:**
   - Click 'Save Config' to save the current list of actions to a configuration file.
   - Click 'Load Config' to load actions from a previously saved configuration file.

10. **Clearing All Actions:**
    - Click 'Clear All' to remove all actions from the list.

11. **Adjusting DPI Scaling:**
    - Enter a custom DPI scaling factor in the 'DPI Scaling Factor:' field if necessary. The default value is automatically detected based on your system settings.

## Example Usage

1. Add a click position at coordinates (100, 200).
2. Set the scroll up amount to 10 pixels and add a scroll up action.
3. Set the wait time to 1 second and the number of actions to 5.
4. Click 'Start' to perform the actions 5 times with a 1-second interval.

## Troubleshooting

If you encounter any issues, ensure the following:
- All dependencies are correctly installed.
- You have the necessary permissions to control mouse actions on your system.
- The DPI scaling factor is set correctly for your screen resolution.

## Contributions

Contributions are welcome! If you have any ideas or improvements, feel free to open an issue or submit a pull request.


---

With Mine-Autoclicker-Beta, automating repetitive mouse actions is easier than ever. Enjoy your productivity boost!
