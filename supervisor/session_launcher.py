import ctypes
import logging
from pathlib import Path


# ============================================================
# Windows API
# ============================================================

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
wtsapi32 = ctypes.WinDLL("wtsapi32", use_last_error=True)
advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)


# ============================================================
# Constants
# ============================================================

INVALID_SESSION_ID = 0xFFFFFFFF

TOKEN_QUERY = 0x0008
TOKEN_DUPLICATE = 0x0002
TOKEN_ASSIGN_PRIMARY = 0x0001

CREATE_UNICODE_ENVIRONMENT = 0x00000400

STARTF_USESHOWWINDOW = 0x00000001

SW_HIDE = 0


# ============================================================
# Structures
# ============================================================

class STARTUPINFO(ctypes.Structure):

    _fields_ = [
        ("cb", ctypes.c_ulong),
        ("lpReserved", ctypes.c_wchar_p),
        ("lpDesktop", ctypes.c_wchar_p),
        ("lpTitle", ctypes.c_wchar_p),
        ("dwX", ctypes.c_ulong),
        ("dwY", ctypes.c_ulong),
        ("dwXSize", ctypes.c_ulong),
        ("dwYSize", ctypes.c_ulong),
        ("dwXCountChars", ctypes.c_ulong),
        ("dwYCountChars", ctypes.c_ulong),
        ("dwFillAttribute", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("wShowWindow", ctypes.c_ushort),
        ("cbReserved2", ctypes.c_ushort),
        ("lpReserved2", ctypes.POINTER(ctypes.c_ubyte)),
        ("hStdInput", ctypes.c_void_p),
        ("hStdOutput", ctypes.c_void_p),
        ("hStdError", ctypes.c_void_p),
    ]


class PROCESS_INFORMATION(ctypes.Structure):

    _fields_ = [
        ("hProcess", ctypes.c_void_p),
        ("hThread", ctypes.c_void_p),
        ("dwProcessId", ctypes.c_ulong),
        ("dwThreadId", ctypes.c_ulong),
    ]


# ============================================================
# Function definitions
# ============================================================

kernel32.WTSGetActiveConsoleSessionId.restype = ctypes.c_ulong


wtsapi32.WTSQueryUserToken.argtypes = [
    ctypes.c_ulong,
    ctypes.POINTER(ctypes.c_void_p),
]

wtsapi32.WTSQueryUserToken.restype = ctypes.c_int


advapi32.CreateProcessAsUserW.argtypes = [
    ctypes.c_void_p,
    ctypes.c_wchar_p,
    ctypes.c_wchar_p,
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_int,
    ctypes.c_ulong,
    ctypes.c_void_p,
    ctypes.c_wchar_p,
    ctypes.POINTER(STARTUPINFO),
    ctypes.POINTER(PROCESS_INFORMATION),
]

advapi32.CreateProcessAsUserW.restype = ctypes.c_int


kernel32.CloseHandle.argtypes = [
    ctypes.c_void_p
]

kernel32.CloseHandle.restype = ctypes.c_int


# ============================================================
# Configuration
# ============================================================

BASE_DIR = Path(
    __file__
).resolve().parent.parent


AGENT_EXE = (
    BASE_DIR
    / "dist"
    / "System-D-Agent.exe"
)


# ============================================================
# Logging
# ============================================================

LOG_DIR = Path(
    r"C:\ProgramData\System-D\logs"
)

LOG_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


logging.basicConfig(
    filename=str(
        LOG_DIR / "session_launcher.log"
    ),
    level=logging.INFO,
    format=(
        "%(asctime)s "
        "%(levelname)s "
        "%(message)s"
    ),
)


# ============================================================
# Get active session
# ============================================================

def get_active_session_id():

    session_id = (
        kernel32
        .WTSGetActiveConsoleSessionId()
    )

    logging.info(
        "Active console session ID: %s",
        session_id,
    )

    if session_id == INVALID_SESSION_ID:

        raise RuntimeError(
            "No active console session."
        )

    return session_id


# ============================================================
# Launch agent in user session
# ============================================================

def launch_agent():

    if not AGENT_EXE.exists():

        raise FileNotFoundError(
            f"Agent not found: {AGENT_EXE}"
        )


    session_id = (
        get_active_session_id()
    )


    # --------------------------------------------------------
    # Get user token
    # --------------------------------------------------------

    user_token = (
        ctypes.c_void_p()
    )


    result = (
        wtsapi32
        .WTSQueryUserToken(
            session_id,
            ctypes.byref(user_token),
        )
    )


    if not result:

        error = ctypes.get_last_error()

        raise ctypes.WinError(
            error
        )


    logging.info(
        "Obtained user token for session %s",
        session_id,
    )


    try:

        # ----------------------------------------------------
        # Startup information
        # ----------------------------------------------------

        startup = STARTUPINFO()

        startup.cb = ctypes.sizeof(
            STARTUPINFO
        )

        startup.lpDesktop = (
            r"winsta0\default"
        )

        startup.dwFlags = (
            STARTF_USESHOWWINDOW
        )

        startup.wShowWindow = SW_HIDE


        # ----------------------------------------------------
        # Process information
        # ----------------------------------------------------

        process_info = (
            PROCESS_INFORMATION()
        )


        command_line = (
            f'"{AGENT_EXE}"'
        )


        # ----------------------------------------------------
        # Create process
        # ----------------------------------------------------

        result = (
            advapi32
            .CreateProcessAsUserW(

                user_token,

                None,

                command_line,

                None,

                None,

                False,

                CREATE_UNICODE_ENVIRONMENT,

                None,

                str(
                    AGENT_EXE.parent
                ),

                ctypes.byref(
                    startup
                ),

                ctypes.byref(
                    process_info
                ),
            )
        )


        if not result:

            error = ctypes.get_last_error()

            raise ctypes.WinError(
                error
            )


        logging.info(
            "Agent started successfully."
        )

        logging.info(
            "Agent PID: %s",
            process_info.dwProcessId,
        )

        logging.info(
            "Agent session: %s",
            session_id,
        )


        return process_info


    finally:

        kernel32.CloseHandle(
            user_token
        )


# ============================================================
# Test
# ============================================================

if __name__ == "__main__":

    logging.info(
        "================================"
    )

    logging.info(
        "Session launcher test starting"
    )

    try:

        process_info = launch_agent()

        print(
            "Agent started."
        )

        print(
            f"PID: {process_info.dwProcessId}"
        )

        print(
            "Session:",
            get_active_session_id(),
        )


        # Close handles returned by
        # CreateProcessAsUser.

        kernel32.CloseHandle(
            process_info.hThread
        )

        kernel32.CloseHandle(
            process_info.hProcess
        )


    except Exception as error:

        logging.exception(
            "Failed to launch agent"
        )

        print(
            "ERROR:",
            error
        )

        raise