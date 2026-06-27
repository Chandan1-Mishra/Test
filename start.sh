#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# SOLARIS — One-shot startup script (Mac / Linux)
# Usage:  chmod +x start.sh && ./start.sh
# ─────────────────────────────────────────────────────────────
set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

echo -e "${GREEN}☀  Starting SOLARIS...${NC}"

# ── 1. Check Python ───────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
  echo -e "${RED}✗ Python 3.10+ required. Install from https://python.org${NC}"; exit 1
fi
PYVER=$(python3 -c "import sys; print(sys.version_info >= (3,10))")
if [ "$PYVER" != "True" ]; then
  echo -e "${RED}✗ Python 3.10+ required (found $(python3 --version))${NC}"; exit 1
fi

# ── 2. Check Node ─────────────────────────────────────────────
if ! command -v node &>/dev/null; then
  echo -e "${RED}✗ Node 18+ required. Install from https://nodejs.org${NC}"; exit 1
fi

# ── 3. Check .env ─────────────────────────────────────────────
if [ ! -f backend/.env ]; then
  if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo -e "${RED}✗ No backend/.env found and ANTHROPIC_API_KEY not set in environment.${NC}"
    echo -e "  Copy backend/.env.example to backend/.env and add your key."
    exit 1
  fi
  echo -e "${YELLOW}⚠  Using ANTHROPIC_API_KEY from environment${NC}"
fi

# ── 4. Backend virtualenv + deps ──────────────────────────────
echo -e "${GREEN}→ Setting up Python virtual environment...${NC}"
cd backend
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo -e "${GREEN}✓ Backend dependencies installed${NC}"

# ── 5. Start backend in background ────────────────────────────
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo -e "${GREEN}✓ Backend running (PID $BACKEND_PID) → http://localhost:8000${NC}"
cd ..

# ── 6. Frontend deps + start ──────────────────────────────────
echo -e "${GREEN}→ Installing frontend dependencies...${NC}"
cd frontend
npm install --silent
echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
echo -e "${GREEN}✓ Frontend starting → http://localhost:3000${NC}"
echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}  SOLARIS is ready!                     ${NC}"
echo -e "${GREEN}  Open http://localhost:3000 in browser  ${NC}"
echo -e "${GREEN}  Press Ctrl+C to stop both servers      ${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo ""

npm run dev

# ── Cleanup on Ctrl+C ─────────────────────────────────────────
trap "kill $BACKEND_PID 2>/dev/null; echo 'Stopped.'" EXIT
