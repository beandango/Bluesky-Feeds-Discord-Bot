import json
import os
import sys

CONFIG_FILE = "config.json"

def load_config():
    """Load the configuration file. If missing, create a new one."""
    if not os.path.exists(CONFIG_FILE):
        print(f"{CONFIG_FILE} not found. Creating a new configuration file.")
        config = {
            "TOKEN": "",  # Add your Discord bot token here
            "CHANNEL_ID": None,
            "BLSKY_USER_HANDLE": None
        }
        save_config(config)
        print(f"A new {CONFIG_FILE} file has been created.")
        print("Please add your bot token to the 'TOKEN' field in config.json.")
        input("Press Enter to exit once you've updated the configuration.")
        sys.exit()  # Close the program after informing the user

    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)

    if not config.get("TOKEN"):
        print("No bot token found in config.json.")
        print("Please add your bot token to the 'TOKEN' field in config.json.")
        print("You can also add in the channel_id and blsky_user_handle fields, otherwise, that can be setup with the bot's /setup command.")
        input("Press Enter to exit once you've updated the configuration.")
        sys.exit()  # Close the program after informing the user

    return config

def save_config(config):
    """Save the configuration data to the JSON file."""
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

def get_config_value(key, default=None):
    """Get a specific configuration value or return a default value if not found."""
    config = load_config()
    return config.get(key, default)

def update_config_value(key, value):
    """Update a specific configuration value and save it to the file."""
    config = load_config()
    config[key] = value
    save_config(config)
