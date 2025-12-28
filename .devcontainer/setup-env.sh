#!/bin/bash

# Path to the .env file
ENV_FILE="/workspaces/rpc-stream-prototype/.env"
EXAMPLE_FILE="/workspaces/rpc-stream-prototype/.env.example"

# Check if .env exists, if not copy from .env.example
if [ ! -f "$ENV_FILE" ]; then
    echo "Creating .env from .env.example"
    cp "$EXAMPLE_FILE" "$ENV_FILE"
fi

# List of secrets to check (customize as needed)
SECRETS=()

for SECRET_NAME in "${SECRETS[@]}"; do
    # Get the value of the secret from the environment
    SECRET_VALUE="${!SECRET_NAME}"

    if [ -n "$SECRET_VALUE" ]; then
        echo "Updating $SECRET_NAME in .env"
        if grep -q "^$SECRET_NAME=" "$ENV_FILE"; then
             python3 -c "
import sys
import os
import re

secret_name = '$SECRET_NAME'
secret_value = os.environ.get(secret_name, '')
env_file = '$ENV_FILE'

with open(env_file, 'r') as f:
    lines = f.readlines()

with open(env_file, 'w') as f:
    for line in lines:
        if line.startswith(f'{secret_name}='):
            f.write(f'{secret_name}={secret_value}\n')
        else:
            f.write(line)
"
        else
            echo "$SECRET_NAME=$SECRET_VALUE" >> "$ENV_FILE"
        fi
    else
        echo "Secret $SECRET_NAME not found in environment variables."
    fi
done

# Install dependencies
uv sync
