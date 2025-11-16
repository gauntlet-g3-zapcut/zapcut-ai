#!/bin/bash
# Script to stop all Fly.io machines for zapcut-api and zapcut-worker

set -e

echo "Stopping all Fly.io machines..."

# Stop API machines
echo "Stopping zapcut-api machines..."
fly scale count 0 -a zapcut-api || echo "Failed to scale zapcut-api (app may not exist)"

# Stop Worker machines
echo "Stopping zapcut-worker machines..."
fly scale count 0 -a zapcut-worker || echo "Failed to scale zapcut-worker (app may not exist)"

# Alternative: Destroy all machines (more aggressive)
# Uncomment if scale count doesn't work:
# echo "Destroying all machines..."
# fly machine list -a zapcut-api | grep -v "^MACHINE" | awk '{print $1}' | xargs -I {} fly machine destroy {} -a zapcut-api --force || true
# fly machine list -a zapcut-worker | grep -v "^MACHINE" | awk '{print $1}' | xargs -I {} fly machine destroy {} -a zapcut-worker --force || true

echo "Done!"

