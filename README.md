# Gask: Super Simple Command Suggestion Tool

Gask is a command-line tool powered by Google AI Studio that generates command suggestions based on user queries. It leverages the Gemini AI model to provide accurate and context-aware command recommendations.

## Features

- Generate command suggestions based on natural language queries
- Optional display command descriptions

## Prerequisites

- Python 3.6 or higher
- Google AI Studio API key

## Installation

### 1-1. Download the binary from [Releases](https://github.com/M0ch0/gask/releases)

1-2. Place the binary in your PATH

1-3. Set up the configuration:
   - Copy the `gask.conf` file to your home directory:
     ```
     cp gask.conf ~/.gask.conf
     ```
   - Edit `~/.gask.conf` and replace `your_google_api_key_here` with your actual Google AI Studio API key.

### 2-1. Clone the repository:
   ```
   git clone https://github.com/M0ch0/gask.git
   cd gask
   ```

2-2. Install the required dependencies:
   ```
   pip install google-generativeai jsonschema
   ```

2-3. Set up the configuration:
   - Copy the `gask.conf` file to your home directory:
     ```
     cp gask.conf ~/.gask.conf
     ```
   - Edit `~/.gask.conf` and replace `your_google_api_key_here` with your actual Google AI Studio API key.

## Usage

`python gask.py [-d] ["query"]`
- `query`: The natural language query to generate command suggestions for.
- `-d`, `--desc`, `--description`: Display the description of the suggested command.
