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
  local frontend_cmd="$3"
  local backend_port="$4"

  osascript - "$title" "$backend_cmd" "$frontend_cmd" "$backend_port" <<'APPLESCRIPT'
on run argv
  set projectTitle to item 1 of argv
  set backendCmd to item 2 of argv
  set frontendCmd to item 3 of argv
  set backendPort to item 4 of argv

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
    
    -- Create second tab and run frontend command
    tell application "System Events"
      tell process "Terminal"
        keystroke "t" using {command down}
      end tell
    end tell
    delay 0.5
    
    tell front window
      do script frontendCmd in selected tab
      try
        set custom title of tab 2 of front window to "Frontend"
      end try
    end tell
  end tell
end run
APPLESCRIPT

  # Wait for backend to be ready
  wait_for_backend "$backend_port"
}

require_cli "osascript"
require_cli "python3"
require_cli "uv"

# Check if npm/yarn is available (for frontend)
if ! command -v npm >/dev/null 2>&1 && ! command -v yarn >/dev/null 2>&1; then
  echo -e "${RED}Missing npm or yarn. Please install Node.js.${NC}"
  exit 1
fi

BACKEND_CMD="cd \"$SCRIPT_DIR/backend\" && printf 'Installing shell...\\n' && UV_VENV_CLEAR=1 v && printf 'Activating virtual environment...\\n' && source .venv/bin/activate && printf 'Installing dependencies if needed...\\n' && uv pip install -q -r requirements.txt && printf 'Starting FastAPI backend...\\n' && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
FRONTEND_CMD="cd \"$SCRIPT_DIR/frontend\" && printf 'Starting Vite frontend...\\n' && npm run dev"

echo -e "${BLUE}Starting ${PROJECT_NAME} services...${NC}"
launch_terminal_tabs "$PROJECT_NAME" "$BACKEND_CMD" "$FRONTEND_CMD" "8000"

echo -e "${GREEN}All services are launching in a single Terminal window with two tabs.${NC}"
echo -e "${YELLOW}Backend: http://localhost:8000${NC}"
echo -e "${YELLOW}Frontend: http://localhost:5173 (or check the Frontend tab for the actual port)${NC}"
