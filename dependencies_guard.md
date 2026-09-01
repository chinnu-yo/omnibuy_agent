### 6. `dependencies_guard.md`

# Dependencies & Environment Guard

## 1. Backend Requirements (`backend/requirements.txt`)
text
fastapi==0.115.0
uvicorn==0.30.6
pydantic==2.9.2
google-genai==0.1.1
duckduckgo-search==6.2.11
razorpay==1.4.2
python-dotenv==1.0.1
2. Frontend Dependencies (frontend/package.json)
JSON
{
  "name": "omnibuyer-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "clsx": "^2.1.1",
    "lucide-react": "^0.441.0",
    "next": "15.0.0",
    "react": "19.0.0-rc-65a02de0-20241023",
    "react-dom": "19.0.0-rc-65a02de0-20241023",
    "tailwind-merge": "^2.5.2"
  },
  "devDependencies": {
    "@types/node": "^20.16.5",
    "@types/react": "^18.3.5",
    "@types/react-dom": "^18.3.0",
    "postcss": "^8.4.47",
    "tailwindcss": "^3.4.11",
    "typescript": "^5.6.2"
  }
}
3. Environment Variables Specification
backend/.env
Code snippet
# Google Gemini API Key (Obtain from Google AI Studio - free tier)
GEMINI_API_KEY=your_gemini_api_key_here

# Razorpay Test Credentials (Obtain from Razorpay Dashboard -> Settings -> API Keys)
RAZORPAY_KEY_ID=rzp_test_your_key_id
RAZORPAY_KEY_SECRET=your_key_secret_here

# Local Development Flag
MOCK_PAYMENT_MODE=false
frontend/.env.local
Code snippet
NEXT_PUBLIC_API_BASE_URL=[http://127.0.0.1:8000](http://127.0.0.1:8000)

4. Initialization & Execution Commands
Run Backend
Bash
cd backend
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
Run Frontend
Bash
cd frontend
npm install
npm run dev