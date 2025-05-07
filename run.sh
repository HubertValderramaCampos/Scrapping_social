#!/bin/bash

# Colors for terminal output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting TikTok Scraper API...${NC}"

# Check for Python environment
if [ -d "venv" ]; then
    echo -e "${GREEN}Activating virtual environment...${NC}"
    source venv/bin/activate
else
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python -m venv venv
    source venv/bin/activate
    
    echo -e "${YELLOW}Installing requirements...${NC}"
    pip install fastapi uvicorn undetected-chromedriver selenium whisper pyaudio wave numpy pydub soundcard
fi

# Check for cookies.json file
if [ ! -f "cookies.json" ]; then
    echo -e "${RED}Error: cookies.json file not found!${NC}"
    echo -e "${YELLOW}Please create a cookies.json file with valid TikTok cookies.${NC}"
    exit 1
fi

# Start the FastAPI server
echo -e "${GREEN}Starting server...${NC}"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000