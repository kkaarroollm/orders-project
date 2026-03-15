#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ENVS_DIR="$PROJECT_DIR/envs"

echo "Setting up local development environment..."

# Create env files from defaults if they don't exist
for default_file in "$ENVS_DIR"/default.*; do
  filename=$(basename "$default_file" | sed 's/^default\.//')
  target="$ENVS_DIR/$filename"
  if [ ! -f "$target" ]; then
    cp "$default_file" "$target"
    echo "Created $filename from default"
  else
    echo "$filename already exists, skipping"
  fi
done

# Generate mongo-keyfile if empty or missing
KEYFILE="$ENVS_DIR/mongo-keyfile"
if [ ! -s "$KEYFILE" ]; then
  openssl rand -base64 756 > "$KEYFILE"
  chmod 400 "$KEYFILE"
  echo "Generated mongo-keyfile"
else
  echo "mongo-keyfile already exists, skipping"
fi

echo ""
echo "Setup complete! Run: docker compose up --build"
