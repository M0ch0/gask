#!/usr/bin/env python3

import argparse
import configparser
import json
import os
import sys
from pathlib import Path

import google.generativeai as genai
from jsonschema import validate, ValidationError

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


def configure_genai(api_key):
    """
    Configure the Google Generative AI client.
    """
    genai.configure(api_key=api_key)


def generate_commands(query, model_name):
    """
    Generate commands based on the user's query using Google Generative AI.
    """
    try:
        model = genai.GenerativeModel(
            model_name,
            generation_config={"response_mime_type": "application/json"}
        )

        result = model.generate_content(
            query,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=COMMAND_SCHEMA
            ),
            request_options={"timeout": 600},
        )

        return result.text
    except Exception as e:
        print(f"Error generating commands: {e}")
        sys.exit(1)


def validate_json(response_text):
    """
    Validate the JSON response against the COMMAND_SCHEMA.
    """
    try:
        response_json = json.loads(response_text)
        validate(instance=response_json, schema=COMMAND_SCHEMA)
        return response_json
    except json.JSONDecodeError:
        print("Invalid JSON response from the AI model.")
        sys.exit(1)
    except ValidationError as ve:
        print(f"JSON Schema validation error: {ve.message}")
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

    # Configure Google Generative AI
    configure_genai(api_key)

    if args.query:
        # Generate commands based on the query
        response_text = generate_commands(args.query, model_name)
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
