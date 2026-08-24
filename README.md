# Remote Screen Capture

A Python-based centralized screen capture system for authorized
and transparent enterprise environments.

## Project Architecture

Admin Console
    ↓
Central FastAPI Server
    ↓
Windows Agent
    ↓
In-memory Screen Capture
    ↓
Central Storage

## Technologies

- Python 3.12
- mss
- Pillow
- FastAPI
- Uvicorn
- httpx



   Full Installation Guide
1. Prerequisites
Windows
Python 3.12
Git (optional, if cloning repository)
pip


2. Prepare the project
Open a terminal in remote_screen_capture
Verify Python version: python --version


3. Create and activate a virtual environment:  python -m venv .venv
.\.venv\Scripts\Activate.ps1
If using cmd.exe: .\.venv\Scripts\activate.bat


4. Install Python dependencies: python -m pip install --upgrade pip
python -m pip install -r requirements.txt


5. Configure the API key
The project reads AGENT_API_KEY from .env.
Open .env
Confirm it contains: AGENT_API_KEY=V6PF3U5g-xz9hMWTxYfgYjfiFpQZZaYO2rM0edtQd_s
If you want a custom key, change it in .env and use the same value for both server and agent.


6. Verify the server URL
In main.py, the agent is configured with: SERVER_URL = "https://192.168.17.38:8443"

Update this value if your server runs on a different host, IP, or port.


7. Start the server
The server app is main.py.
From the repository root: python -m uvicorn server.main:app --host 0.0.0.0 --port 8443 --reload

HTTPS note
The agent expects HTTPS by default. If you want proper HTTPS, run uvicorn with certificate files: python -m uvicorn server.main:app --host 192.168.41.31 --port 8443 --ssl-keyfile certs/server.key --ssl-certfile certs/server.crt --reload

If you do not have TLS set up, you can also run the server on HTTP, but then:
-change SERVER_URL in main.py to http://<server-ip>:<port>
-keep in mind the current code uses verify_ssl=False only for HTTPS self-signed certs


8. Start the agent
From the repository root:python agent/main.py

The agent will:
-load AGENT_API_KEY from .env
-use agent_identity.json for its identity
-register with the server
start heartbeat polling
-poll for screenshot commands


9. Test the screenshot capture
There is a simple test script: python test_capture.py
This verifies the screen capture code can take a screenshot and reports the image size.


10. What the server provides
GET / — dashboard page
POST /agents/register — agent registration
POST /agents/heartbeat — agent heartbeat
GET /agents/{agent_id}/commands — agent command polling
POST /screenshots/upload — screenshot upload
Screenshot files are stored under:

screenshots
11. Optional packaging
The repo includes:

RemoteScreenshotAgent.spec
RemoteScreenshotAgent
This suggests a PyInstaller packaging workflow, but the source run steps above are enough for installation and testing.

12. Troubleshooting
If server fails to start: ensure .env exists and AGENT_API_KEY is set
If agent fails to register: verify SERVER_URL and that the server is running
If screenshots are missing: check screenshots
If using HTTPS with self-signed certs: verify_ssl=False is already set in the agent client

https://chatgpt.com/share/6a6860e2-dc94-83ee-817e-dd486af989e8?ogimg=plain
https://chatgpt.com/share/6a8bbda2-11d0-83ee-8cf7-2155df14914c
