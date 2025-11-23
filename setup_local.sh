#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="Zapcut AI"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

if [[ "${OSTYPE:-}" != darwin* ]]; then
  echo -e "${RED}This launcher currently supports macOS Terminal only.${NC}"
  exit 1
fi

require_cli() {
  local cli_name="$1"
  if ! command -v "$cli_name" >/dev/null 2>&1; then
    echo -e "${RED}Missing required command: ${cli_name}.${NC}"
    exit 1
  fi
}

wait_for_backend() {
  local port="$1"
  local max_attempts=60
  local attempt=0
  
  echo -e "${YELLOW}Waiting for backend to be ready on port ${port}...${NC}"
  
  while [ $attempt -lt $max_attempts ]; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
      echo -e "${GREEN}Backend is ready!${NC}"
      return 0
    fi
    attempt=$((attempt + 1))
    sleep 1
  done
  
  echo -e "${RED}Backend did not become ready within ${max_attempts} seconds.${NC}"
  return 1
}

launch_terminal_tabs() {
  local title="$1"
  local backend_cmd="$2"
  local worker_cmd="$3"
  local frontend_cmd="$4"
  local backend_port="$5"

  osascript - "$title" "$backend_cmd" "$worker_cmd" "$frontend_cmd" "$backend_port" <<'APPLESCRIPT'
on run argv
  set projectTitle to item 1 of argv
  set backendCmd to item 2 of argv
  set workerCmd to item 3 of argv
  set frontendCmd to item 4 of argv
  set backendPort to item 5 of argv

  tell application "Terminal"
    -- Create new window with first tab for backend
    set newWindow to do script backendCmd
    activate
    try
      set custom title of front window to projectTitle
    end try
    try
      set custom title of tab 1 of front window to "Backend"
    end try
    
    -- Wait for shell installation, dependency installation, and backend to start
    delay 10
    
    -- Create second tab and run worker command
    tell application "System Events"
      tell process "Terminal"
        keystroke "t" using {command down}
      end tell
    end tell
    delay 0.5
    
    tell front window
      do script workerCmd in selected tab
      try
        set custom title of tab 2 of front window to "Worker"
      end try
    end tell
    
    delay 2
    
    -- Create third tab and run frontend command
    tell application "System Events"
      tell process "Terminal"
        keystroke "t" using {command down}
      end tell
    end tell
    delay 0.5
    
    tell front window
      do script frontendCmd in selected tab
      try
        set custom title of tab 3 of front window to "Frontend"
      end try
    end tell
  end tell
end run
APPLESCRIPT

  # Wait for backend to be ready
  wait_for_backend "$backend_port"
}

require_cli "osascript"
require_cli "python3.11"

# Check if npm/yarn is available (for frontend)
if ! command -v npm >/dev/null 2>&1 && ! command -v yarn >/dev/null 2>&1; then
  echo -e "${RED}Missing npm or yarn. Please install Node.js.${NC}"
  exit 1
fi

# Check if Redis is running (optional check, will fail gracefully if not)
if ! lsof -Pi :6379 -sTCP:LISTEN -t >/dev/null 2>&1; then
  echo -e "${YELLOW}Warning: Redis doesn't appear to be running on port 6379.${NC}"
  echo -e "${YELLOW}The worker requires Redis. Start it with: brew services start redis${NC}"
  echo -e "${YELLOW}Or set REDIS_URL environment variable if using remote Redis.${NC}"
  echo ""
fi

BACKEND_CMD="cd \"$SCRIPT_DIR/backend\" && printf 'Setting up Python 3.11 environment...\\n' && if [ ! -d .venv ] || ! .venv/bin/python --version 2>&1 | grep -q '3\\.11'; then printf 'Creating/recreating venv with Python 3.11...\\n' && rm -rf .venv && python3.11 -m venv .venv; fi && printf 'Activating virtual environment...\\n' && source .venv/bin/activate && printf 'Installing dependencies if needed...\\n' && pip install -q -r requirements.txt && printf 'Starting FastAPI backend...\\n' && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
WORKER_CMD="cd \"$SCRIPT_DIR/backend\" && printf 'Activating virtual environment...\\n' && source .venv/bin/activate && printf 'Starting Celery worker...\\n' && celery -A app.celery_app worker --loglevel=info"
FRONTEND_CMD="cd \"$SCRIPT_DIR/frontend\" && printf 'Starting Vite frontend...\\n' && npm run dev"

echo -e "${BLUE}Starting ${PROJECT_NAME} services...${NC}"
launch_terminal_tabs "$PROJECT_NAME" "$BACKEND_CMD" "$WORKER_CMD" "$FRONTEND_CMD" "8000"

echo -e "${GREEN}All services are launching in a single Terminal window with three tabs.${NC}"
echo -e "${YELLOW}Backend API: http://localhost:8000${NC}"
echo -e "${YELLOW}Worker: Running in background (check Worker tab for logs)${NC}"
echo -e "${YELLOW}Frontend: http://localhost:5173 (or check the Frontend tab for the actual port)${NC}"
