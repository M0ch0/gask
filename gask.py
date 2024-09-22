#!/usr/bin/env python3

import argparse
import configparser
import json
import os
import subprocess
import sys
from pathlib import Path
import urllib.request
import urllib.error


# Define the JSON schema
COMMAND_SCHEMA = {
    "type": "object",
    "properties": {
        "command": {
            "type": "string"
        },
        "description": {
            "type": "string"
        }
    },
    "required": [
        "command",
        "description"
    ]
}

DEFAULT_PROMPT = """
### Instruction
You are a command line tool that generates command suggestions based on user queries and environment. current user's environment is {environment}.
"command" must be a valid command that can be executed in the user's environment.
"description" must be a short description of the command.

### Input
User query: {query}
"""


def load_config(config_path=None):
    """
    Load configuration from a file.
    """
    config = configparser.ConfigParser()
    paths = [
        config_path,
        Path(__file__).parent / ".gask.conf",
        Path.home() / ".gask.conf"
    ]
    for path in paths:
        if path and Path(path).exists():
            config.read(path)
            return config['DEFAULT']
    print("Configuration file not found")
    sys.exit(1)


def get_terminal_info():
    if os.name == 'nt':
        return os.environ.get('COMSPEC', 'Unknown')
    else:
        terminal = os.environ.get('TERM', 'Unknown')
        shell = os.environ.get('SHELL', 'Unknown')
        return f"Terminal: {terminal}, Shell: {shell}"
    

def get_parent_cli():
    ppid = os.getppid()
    try:
        if os.name == 'nt':  # Windows
            result = subprocess.run(["tasklist", "/FI", f"PID eq {ppid}", "/FO", "CSV", "/NH"], 
                                    capture_output=True, text=True, check=True)
            output = result.stdout.strip().strip('"')
            if output:
                return output.split('","')[0]
            return "Unknown"
        else:  # UNIX-like systems
            result = subprocess.run(["ps", "-p", str(ppid), "-o", "comm="], 
                                    capture_output=True, text=True, check=True)
            return result.stdout.strip() if result.stdout else "Unknown"
    except subprocess.CalledProcessError:
        return "Unknown"


def generate_commands(query, model_name, api_key):
    """
    Generate commands based on the user's query using Google Generative AI REST API.
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
    headers = {
        "Content-Type": "application/json"
    }

    # Get OS and terminal information
    os_name = "Windows" if os.name == 'nt' else os.uname().sysname
    terminal_info = get_terminal_info()
    parent_cli = get_parent_cli()

    environment = f"OS: {os_name}, {terminal_info}, Parent CLI: {parent_cli}"
    
    prompt = DEFAULT_PROMPT.format(environment=environment, query=query)

    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "response_mime_type": "application/json",
            "responseSchema": COMMAND_SCHEMA
        }
    }
    
    request = urllib.request.Request(f"{url}?key={api_key}", 
                                    data=json.dumps(data).encode('utf-8'), 
                                    headers=headers, 
                                    method='POST')

    try:
        with urllib.request.urlopen(request, timeout=600) as response:
            result = json.load(response)
            return result['candidates'][0]['content']['parts'][0]['text']
    except urllib.error.HTTPError as e:
        print("An error occurred while communicating with the API. Please try again later.")
        if os.environ.get('GASK_DEBUG'):
            print(f"HTTP Error: {e.code} - {e.reason}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print("Failed to reach the server. Please check your internet connection.")
        if os.environ.get('GASK_DEBUG'):
            print(f"URL Error: {e.reason}")
        sys.exit(1)
    except Exception as e:
        print("An unexpected error occurred.")
        if os.environ.get('GASK_DEBUG'):
            print(f"Error: {str(e)}")
        sys.exit(1)


def validate_json(response_text):
    try:
        data = json.loads(response_text)
        if not isinstance(data, dict):
            raise ValueError("Response is not a JSON object")
        if "command" not in data or not isinstance(data["command"], str):
            raise ValueError("Missing or invalid 'command' field")
        if "description" not in data or not isinstance(data["description"], str):
            raise ValueError("Missing or invalid 'description' field")
        return data
    except json.JSONDecodeError:
        print("Invalid JSON response from the AI model.")
        sys.exit(1)
    except ValueError as ve:
        print(f"JSON validation error: {str(ve)}")
        sys.exit(1)


def display_description(commands_json):
    """
    Display the description from the JSON response.
    """
    print(commands_json.get("description", "No description available."))


def display_command(commands_json):
    """
    Display the command from the JSON response.
    """
    print(commands_json.get("command", "No command available."))


def main():
    parser = argparse.ArgumentParser(
        description="Gask: A command suggestion tool powered by Google AI Studio."
    )
    parser.add_argument("query", nargs="?", help="The query to generate command suggestions for.")
    parser.add_argument("-d", "--desc", "--description", action="store_true", 
                        help="Display the description of the suggested command.")
    args = parser.parse_args()

    if not args.query and not args.desc:
        parser.print_help()
        return

    config = load_config()
    api_key = config.get("API_KEY")
    model_name = config.get("MODEL_NAME", "gemini-1.5-flash")

    if not api_key or api_key == "your_google_api_key_here":
        print("Invalid API_KEY. Please set a valid API key in your configuration file (~/.gask.conf).")
        return

    if args.query:
        response_text = generate_commands(args.query, model_name, api_key)
        commands_json = validate_json(response_text)
        display_command(commands_json)
        if args.desc:
            display_description(commands_json)
    elif args.desc:
        print("Description requested without a query. Please provide a query.")


if __name__ == "__main__":
    main()
