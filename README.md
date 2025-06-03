# CigiHoldSpam

CigiHoldSpam is a Python application designed to automate keystrokes in a target application when specific conditions are met. It features a graphical user interface (GUI) built with CustomTkinter for easy configuration.

## Features

-   **Targeted Keystroke Automation**: Sends a specified keystroke (`SpamKey`) to a target application (`ProcessName`).
-   **Trigger Activation**: Activates when the target application is in focus AND a specified `TriggerKey` is held down.
-   **Configurable Delay**: Allows setting a base delay (`DelayMS`) for the keystroke, with a small random jitter (+/- 4ms) applied automatically.
-   **GUI for Configuration**: 
    -   **Features Tab**: Toggle the spamming functionality on/off. Displays a "Spamming" status.
    -   **Setup Tab**: Configure `ProcessName`, `TriggerKey`, `SpamKey`, and `DelayMS`. Settings can be saved to and loaded from a `config.ini` file.
-   **Modular Core Components**: The backend logic is split into single-responsibility modules for key mapping, process monitoring, input simulation, and overall control.

## Requirements

-   Python 3.13 (as specified in `pyproject.toml`)
-   PDM (Python Dependency Manager)
-   Windows Operating System (for the OS-level listening and input simulation features)
-   The following Python packages (managed by PDM):
    -   `customtkinter`
    -   `pywin32`
    -   `psutil`

## Setup and Installation

1.  **Clone the repository (if applicable) or ensure you have the project files.**
2.  **Install PDM**: If you don't have PDM, follow the installation instructions on the [official PDM website](https://pdm-project.org/).
3.  **Install Dependencies**: Open a terminal in the project's root directory and run:
    ```bash
    pdm install
    ```
    This command will create a virtual environment (if one doesn't exist) and install all the necessary dependencies listed in `pyproject.toml`.

## Usage

1.  **Run the Application**: From the project's root directory, use the PDM script:
    ```bash
    pdm run start
    ```
    This will launch the CigiHoldSpam GUI.

2.  **Configure Settings (Setup Tab)**:
    -   **ProcessName**: Enter the executable name of the target application (e.g., `notepad.exe`).
    -   **TriggerKey**: Enter the key that needs to be held down to activate spamming. 
        -   Can be a single alphanumeric character (e.g., `2`, `a`, `Z`).
        -   Can be a named key (e.g., `F1`, `ENTER`, `SHIFT`, `CTRL`, `ALT`, `SPACE`, `LEFT`, `UP`). Case-insensitive.
        -   *See Known Issues below.*
    -   **SpamKey**: Enter the key that will be sent as a keystroke to the target application.
        -   Same input options as `TriggerKey`.
        -   *See Known Issues below.*
    -   **DelayMS**: Enter the base delay in milliseconds before the `SpamKey` is sent after conditions are met.
    -   Click **Save** to save your settings to `config.ini`. 
    -   Click **Load** to load settings from `config.ini` into the fields.

3.  **Activate Spamming (Features Tab)**:
    -   Toggle the **"Active"** switch to "on".
    -   When the switch is active:
        -   If the window of the specified `ProcessName` is in focus AND your `TriggerKey` is held down, the "Spamming" label will turn green, and the application will start sending the `SpamKey` keystroke with the configured delay.
    -   Toggle the switch to "off" to deactivate the listener.

## Known Issues

-   **Trigger Key and Spam Key Conflict**: The `TriggerKey` and `SpamKey` **cannot be the same key**. 
    -   **Reason**: The mechanism for detecting if the `TriggerKey` is held down (`GetAsyncKeyState`) can interfere with the simulation of the same key as the `SpamKey` (`keybd_event`). If they are the same, the `TriggerKey` might be detected as released when the `SpamKey` event is simulated, leading to inconsistent behavior or the spamming stopping prematurely.
    -   **Workaround**: Always use different keys for `TriggerKey` and `SpamKey`.

## Project Structure

-   `main.py`: Entry point for the application.
-   `config.ini`: Stores user-defined settings.
-   `src/`:
    -   `view/view.py`: Contains the `App` class responsible for the GUI (CustomTkinter).
    -   `core/`:
        -   `config_manager.py`: Manages loading and saving settings from/to `config.ini`.
        -   `key_mapper.py`: Maps key names/characters to virtual key codes.
        -   `process_monitor.py`: Checks for focused application windows.
        -   `input_simulator.py`: Simulates keyboard input and checks key states.
        -   `spam_controller.py`: Orchestrates the core components and manages the main spamming logic and OS interactions.
-   `pyproject.toml`: Project metadata and dependencies for PDM. 