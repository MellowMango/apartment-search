#!/bin/bash

# Terminal colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}==================================================${NC}"
echo -e "${GREEN} TypeScript Migration Testing Script ${NC}"
echo -e "${GREEN}==================================================${NC}"
echo ""

# Function to check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

echo -e "${BLUE}Checking dependencies...${NC}"

# Check for required tools
if ! command_exists tmux; then
  echo -e "${YELLOW}Warning: tmux is not installed. Installing multiple terminal windows manually.${NC}"
  echo "Please install tmux for a better testing experience:"
  echo "  brew install tmux"
  MANUAL_LAUNCH=true
else
  MANUAL_LAUNCH=false
fi

# Validate environment
if [ ! -f "./frontend/package.json" ]; then
  echo "Error: Must be run from the root of the project. Current directory: $(pwd)"
  exit 1
fi

# Kill any running development servers
echo -e "${BLUE}Stopping any running development servers...${NC}"
pkill -f "next dev" || true
sleep 2

# Export needed environment variables
export NODE_OPTIONS="--max_old_space_size=4096"

if [ "$MANUAL_LAUNCH" = true ]; then
  # Manual launch approach
  echo -e "${YELLOW}Please open two terminal windows and run the following commands:${NC}"
  echo ""
  echo -e "${GREEN}Terminal 1 (JavaScript version - http://localhost:3000):${NC}"
  echo "cd $(pwd) && NEXT_PUBLIC_USE_TS=false npm run dev"
  echo ""
  echo -e "${GREEN}Terminal 2 (TypeScript version - http://localhost:3042):${NC}"
  echo "cd $(pwd) && NEXT_PUBLIC_USE_TS=true npm run dev -- -p 3042"
  echo ""
  echo -e "${YELLOW}When finished testing, press Ctrl+C in both terminals to stop the servers.${NC}"
else
  # Launch using tmux
  echo -e "${BLUE}Starting JavaScript and TypeScript versions...${NC}"
  
  # Create a new tmux session
  tmux new-session -d -s ts-migration
  
  # Split the window horizontally
  tmux split-window -h -t ts-migration
  
  # Send commands to each pane
  tmux send-keys -t ts-migration:0.0 "cd $(pwd)/frontend && NEXT_PUBLIC_USE_TS=false npm run dev" C-m
  tmux send-keys -t ts-migration:0.1 "cd $(pwd)/frontend && NEXT_PUBLIC_USE_TS=true npm run dev -- -p 3042" C-m
  
  # Attach to the session
  echo -e "${GREEN}JavaScript version (left) and TypeScript version (right) starting...${NC}"
  echo -e "${YELLOW}Press Ctrl+B then D to detach from tmux (servers will keep running)${NC}"
  echo -e "${YELLOW}To kill the servers later, run: tmux kill-session -t ts-migration${NC}"
  echo ""
  
  # Wait a moment for servers to start
  sleep 2
  
  # Open browsers
  if command_exists open; then
    echo -e "${BLUE}Opening browsers to test both versions...${NC}"
    open http://localhost:3000
    open http://localhost:3042
  fi
  
  # Attach to the tmux session
  tmux attach-session -t ts-migration
fi

echo -e "${GREEN}==================================================${NC}"
echo -e "${GREEN} Test Complete ${NC}"
echo -e "${GREEN}==================================================${NC}" 