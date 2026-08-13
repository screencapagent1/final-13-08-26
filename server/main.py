import os
from pathlib import Path
from typing import Any
from datetime import datetime

from fastapi import (
    FastAPI,
    File,
    Header,
    HTTPException,
    Request,
    UploadFile,
)

from fastapi.responses import (
    FileResponse,
    HTMLResponse,
)

from fastapi.templating import Jinja2Templates

from pydantic import BaseModel

from server.commands import CommandManager
from server.registry import AgentRegistry


# ============================================================
# FastAPI application
# ============================================================

app = FastAPI(

    title=
    "Remote Screenshot Capture Server",

    version=
    "1.0.0",

)


# ============================================================
# Configuration
# ============================================================

API_KEY = "V6PF3U5g-xz9hMWTxYfgYjfiFpQZZaYO2rM0edtQd_s"


if not API_KEY:

    raise RuntimeError(

        "AGENT_API_KEY is not configured."

    )


# ============================================================
# Screenshot storage
# ============================================================

SCREENSHOT_DIR = Path(

    "server/data/screenshots"

)


SCREENSHOT_DIR.mkdir(

    parents=True,

    exist_ok=True,

)


# ============================================================
# Templates
# ============================================================

TEMPLATES_DIR = Path(

    "server/templates"

)


templates = Jinja2Templates(

    directory=

    str(

        TEMPLATES_DIR

    )

)


# ============================================================
# Managers
# ============================================================

registry = AgentRegistry()

command_manager = CommandManager()


# ============================================================
# Request models
# ============================================================

class AgentRegistration(BaseModel):

    agent_id: str


class HeartbeatRequest(BaseModel):

    agent_id: str


# ============================================================
# API key verification
# ============================================================

def verify_api_key(

    x_api_key:
    str | None,

) -> None:

    if x_api_key != API_KEY:

        raise HTTPException(

            status_code=
            401,

            detail=
            "Invalid API key.",

        )


# ============================================================
# Dashboard
# ============================================================

@app.get(

    "/",

    response_class=
    HTMLResponse,

)

def dashboard(

    request:
    Request,

) -> HTMLResponse:

    return templates.TemplateResponse(

        request=request,

        name="dashboard.html",

        context={},

    )


# ============================================================
# Agent Registration
# ============================================================

@app.post(

    "/agents/register"

)

def register_agent(

    registration:
    AgentRegistration,

    request:
    Request,

) -> dict[str, Any]:

    client_ip = (

        request.client.host

        if request.client

        else

        "unknown"

    )


    registry.register_agent(

        agent_id=

        registration.agent_id,

        ip_address=

        client_ip,

    )


    print(

        "Agent registered: "

        f"{registration.agent_id}"

        " | IP: "

        f"{client_ip}"

    )


    return {

        "status":

        "registered",

        "agent_id":

        registration.agent_id,

        "ip_address":

        client_ip,

    }


# ============================================================
# Agent Heartbeat
# ============================================================

@app.post(

    "/agents/heartbeat"

)

def heartbeat(

    heartbeat_data:
    HeartbeatRequest,

    request:
    Request,

) -> dict[str, Any]:

    client_ip = (

        request.client.host

        if request.client

        else

        "unknown"

    )


    success = (

        registry.update_heartbeat(

            agent_id=

            heartbeat_data.agent_id,

            ip_address=

            client_ip,

        )

    )


    if not success:

        raise HTTPException(

            status_code=
            404,

            detail=
            "Agent not registered.",

        )


    print(

        "Heartbeat received: "

        f"{heartbeat_data.agent_id}"

        " | IP: "

        f"{client_ip}"

    )


    return {

        "status":

        "heartbeat_received",

        "agent_id":

        heartbeat_data.agent_id,

        "ip_address":

        client_ip,

    }


# ============================================================
# Agent Command Polling
# ============================================================

@app.get(

    "/agents/{agent_id}/commands"

)

def get_pending_command(

    agent_id:
    str,

) -> dict[str, Any]:

    agent = registry.get_agent(

        agent_id

    )


    if agent is None:

        raise HTTPException(

            status_code=
            404,

            detail=
            "Agent not registered.",

        )


    command = (

        command_manager

        .get_pending_command(

            agent_id

        )

    )


    if command is None:

        return {

            "command":

            None

        }


    print(

        "Command dispatched: "

        f"{command.command_id}"

    )


    return {

        "command":

        command.to_dict()

    }


# ============================================================
# Agent Uploads Screenshot
# ============================================================

@app.post(

    "/screenshots/upload"

)

async def upload_screenshot(

    agent_id:
    str = File(...),

    command_id:
    str = File(...),

    screenshot:
    UploadFile = File(...),

) -> dict[str, Any]:

    command = (

        command_manager

        .get_command(

            command_id

        )

    )


    if command is None:

        raise HTTPException(

            status_code=
            404,

            detail=
            "Command not found.",

        )


    if command.agent_id != agent_id:

        raise HTTPException(

            status_code=
            403,

            detail=
            "Agent does not own this command.",

        )


    screenshot_bytes = (

        await screenshot.read()

    )


    if not screenshot_bytes:

        command_manager.fail_command(

            command_id,

            "Empty screenshot received.",

        )


        raise HTTPException(

            status_code=
            400,

            detail=
            "Screenshot is empty.",

        )


    original_filename = screenshot.filename or "screenshot.png"

    agent_dir = SCREENSHOT_DIR / agent_id

    agent_dir.mkdir(

        parents=True,

        exist_ok=True,

    )

    timestamp = datetime.now().strftime(

        "%Y%m%d_%H%M%S"

    )

    extension = (

        Path(original_filename).suffix

        or ".png"

    )

    safe_filename = f"{timestamp}{extension}"

    file_path = agent_dir / safe_filename


    try:

        with open(

            file_path,

            "wb"

        ) as output_file:

            output_file.write(

                screenshot_bytes

            )


    except Exception as error:

        command_manager.fail_command(

            command_id,

            str(error),

        )


        raise HTTPException(

            status_code=
            500,

            detail=
            "Failed to save screenshot.",

        )


    command_manager.complete_command(

        command_id,

        filename=

        safe_filename,

        size_bytes=

        len(

            screenshot_bytes

        ),

    )


    print(

        "Screenshot uploaded: "

        f"{safe_filename}"

    )


    return {

        "status":

        "completed",

        "agent_id":

        agent_id,

        "command_id":

        command_id,

        "filename":

        safe_filename,

        "size_bytes":

        len(

            screenshot_bytes

        ),

    }


# ============================================================
# Admin: List Agents
# ============================================================

@app.get(

    "/admin/agents"

)

def get_agents(

    x_api_key:
    str | None = Header(

        default=None

    ),

) -> list[dict[str, str]]:

    verify_api_key(

        x_api_key

    )


    return registry.get_agents()


# ============================================================
# Admin: Search Agent By IP
# ============================================================

@app.get(

    "/admin/agents/search"

)

def search_agent_by_ip(

    ip: str,

    x_api_key:
    str | None = Header(

        default=None

    ),

) -> dict[str, Any]:

    verify_api_key(

        x_api_key

    )


    agent = (

        registry.get_agent_by_ip(

            ip

        )

    )


    if agent is None:

        raise HTTPException(

            status_code=
            404,

            detail=
            "No agent found with this IP address.",

        )


    return agent


# ============================================================
# Admin: Get One Agent
# ============================================================

@app.get(

    "/admin/agents/{agent_id}"

)

def get_agent(

    agent_id:
    str,

    x_api_key:
    str | None = Header(

        default=None

    ),

) -> dict[str, Any]:

    verify_api_key(

        x_api_key

    )


    agent = registry.get_agent(

        agent_id

    )


    if agent is None:

        raise HTTPException(

            status_code=
            404,

            detail=
            "Agent not found.",

        )


    return agent


# ============================================================
# Admin: Request Screenshot
# ============================================================

@app.post(

    "/admin/agents/{agent_id}/screenshot"

)

def request_screenshot(

    agent_id:
    str,

    x_api_key:
    str | None = Header(

        default=None

    ),

) -> dict[str, Any]:

    verify_api_key(

        x_api_key

    )


    agent = registry.get_agent(

        agent_id

    )


    if agent is None:

        raise HTTPException(

            status_code=
            404,

            detail=
            "Agent not registered.",

        )


    command = (

        command_manager

        .create_screenshot_command(

            agent_id

        )

    )


    print(

        "Screenshot command created: "

        f"{command.command_id}"

    )


    return command.to_dict()


# ============================================================
# Admin: Get Command Status
# ============================================================

@app.get(

    "/admin/commands/{command_id}"

)

def get_command_status(

    command_id:
    str,

    x_api_key:
    str | None = Header(

        default=None

    ),

) -> dict[str, Any]:

    verify_api_key(

        x_api_key

    )


    command = (

        command_manager

        .get_command(

            command_id

        )

    )


    if command is None:

        raise HTTPException(

            status_code=
            404,

            detail=
            "Command not found.",

        )


    return command.to_dict()


# ============================================================
# Admin: List Screenshots
# ============================================================

@app.get(

    "/admin/screenshots"

)

def list_screenshots(

    x_api_key:
    str | None = Header(

        default=None

    ),

) -> list[dict[str, Any]]:

    verify_api_key(

        x_api_key

    )


    screenshots = []


    files = [

        file_path

        for file_path

        in SCREENSHOT_DIR.rglob("*")

        if file_path.is_file()

    ]


    files.sort(

        key=lambda file_path:

        file_path.stat().st_mtime,

        reverse=True,

    )


    for file_path in files:

        screenshots.append({

            "agent_id":

            file_path.parent.name,

            "filename":

            file_path.name,

            "size_bytes":

            file_path.stat().st_size,

            "download_endpoint": (

                f"/admin/screenshots/{file_path.parent.name}/{file_path.name}"

            ),

        })


    return screenshots


# ============================================================
# Admin: View / Download Screenshot
# ============================================================

@app.get("/admin/screenshots/{agent_id}/{filename}")
def download_screenshot(
    agent_id: str,
    filename: str,
    x_api_key: str | None = Header(default=None),
):

    verify_api_key(

        x_api_key

    )


    safe_filename = Path(

        filename

    ).name


    file_path = (

        SCREENSHOT_DIR

        /

        agent_id

        /

        safe_filename

    )


    if not file_path.exists():

        raise HTTPException(

            status_code=
            404,

            detail=
            "Screenshot not found.",

        )


    return FileResponse(

        path=

        file_path,

        filename=

        safe_filename,

        media_type=

        "image/png",

    )