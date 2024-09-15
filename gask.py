#!/usr/bin/env python3

import argparse
import configparser
import json
import os
import sys
from pathlib import Path
import requests

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


def load_config(config_path=None):
    """
    Load configuration from a file.
    """
    config = configparser.ConfigParser()

    # Default config path
    if not config_path:
        # Check the script's directory
        script_dir = Path(__file__).parent
        config_path = script_dir / "gask.conf"

        # If not found, check in the user's home directory
        if not config_path.exists():
            config_path = Path.home() / ".gask.conf"

    if not Path(config_path).exists():
        print(f"Configuration file not found at {config_path}")
        sys.exit(1)

    config.read(config_path)
    return config['DEFAULT']


def generate_commands(query, model_name, api_key):
    """
    Generate commands based on the user's query using Google Generative AI REST API.
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "contents": [{
            "parts": [{"text": query}]
        }],
        "generationConfig": {
            "response_mime_type": "application/json",
            "responseSchema": COMMAND_SCHEMA
        }
    }

    try:
        response = requests.post(f"{url}?key={api_key}", headers=headers, json=data, timeout=600)
        response.raise_for_status()
        result = response.json()
        return result['candidates'][0]['content']['parts'][0]['text']
    except requests.RequestException as e:
        print(f"Error generating commands: {e}")
        sys.exit(1)


def validate_command_json(data):
    """
    Validate the JSON response against the expected structure.
    """
    if not isinstance(data, dict):
        raise ValueError("Response is not a JSON object")
    
    if "command" not in data or not isinstance(data["command"], str):
        raise ValueError("Missing or invalid 'command' field")
    
    if "description" not in data or not isinstance(data["description"], str):
        raise ValueError("Missing or invalid 'description' field")
    
    return data


def validate_json(response_text):
    """
    Validate the JSON response against the expected structure.
    """
    try:
        response_json = json.loads(response_text)
        return validate_command_json(response_json)
    except json.JSONDecodeError:
        print("Invalid JSON response from the AI model.")
        sys.exit(1)
    except ValueError as ve:
        print(f"JSON validation error caused by AI model: {str(ve)}")
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
    # Argument parser setup
    parser = argparse.ArgumentParser(
        description="Gask: A command suggestion tool powered by Google AI Studio."
    )
    parser.add_argument(
        "query",
        nargs="?",
        help="The query to generate command suggestions for."
    )
    parser.add_argument(
        "-d", "--desc", "--description",
        action="store_true",
        help="Display the description of the suggested command."
    )

    args = parser.parse_args()

    if not args.query and not args.desc:
        parser.print_help()
        sys.exit(0)

    # Load configuration
    config = load_config()
    api_key = config.get("API_KEY")
    model_name = config.get("MODEL_NAME", "gemini-1.5-flash")

    if not api_key:
        print("API_KEY not found in configuration.")
        sys.exit(1)

    if args.query:
        # Generate commands based on the query
        response_text = response_text = generate_commands(args.query, model_name, api_key)
        commands_json = validate_json(response_text)

        # Display the command
        display_command(commands_json)

    if args.desc:
        if args.query:
            display_description(commands_json)
        else:
            print("Description requested without a query. Please provide a query.")
            sys.exit(1)


if __name__ == "__main__":
    main()
