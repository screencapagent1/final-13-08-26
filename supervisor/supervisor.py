import os
import sys
import time
import subprocess
import logging
from pathlib import Path

from session_launcher import launch_agent

# ============================================================
# Configuration
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

AGENT_EXE = (
    BASE_DIR
    / "dist"
    / "System-D-Agent.exe"
)

LOG_DIR = Path(
    r"C:\ProgramData\System-D\logs"
)

LOG_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# Logging
# ============================================================

logging.basicConfig(
    filename=str(
        LOG_DIR / "supervisor.log"
    ),
    level=logging.INFO,
    format=(
        "%(asctime)s "
        "%(levelname)s "
        "%(message)s"
    ),
)


# ============================================================
# Windows process helpers
# ============================================================

import ctypes

kernel32 = ctypes.WinDLL(
    "kernel32",
    use_last_error=True,
)

kernel32.GetExitCodeProcess.argtypes = [
    ctypes.c_void_p,
    ctypes.POINTER(ctypes.c_ulong),
]

kernel32.GetExitCodeProcess.restype = ctypes.c_int

kernel32.TerminateProcess.argtypes = [
    ctypes.c_void_p,
    ctypes.c_uint,
]

kernel32.TerminateProcess.restype = ctypes.c_int

kernel32.CloseHandle.argtypes = [
    ctypes.c_void_p,
]

kernel32.CloseHandle.restype = ctypes.c_int


STILL_ACTIVE = 259


# ============================================================
# Agent Supervisor
# ============================================================

class AgentSupervisor:

    def __init__(self):

        self.process_info = None


    # --------------------------------------------------------
    # Start agent
    # --------------------------------------------------------

    def start_agent(self):

        if not AGENT_EXE.exists():

            logging.error(
                "Agent executable not found: %s",
                AGENT_EXE,
            )

            raise FileNotFoundError(
                AGENT_EXE
            )


        logging.info(
            "Starting agent in active user session: %s",
            AGENT_EXE,
        )


        self.process_info = launch_agent()


        logging.info(
            "Agent started. PID=%s",
            self.process_info.dwProcessId,
        )


    # --------------------------------------------------------
    # Check whether agent is running
    # --------------------------------------------------------

    def is_agent_running(self):

        if self.process_info is None:

            return False


        exit_code = ctypes.c_ulong()


        result = (
            kernel32.GetExitCodeProcess(
                self.process_info.hProcess,
                ctypes.byref(
                    exit_code
                ),
            )
        )


        if not result:

            error = ctypes.get_last_error()

            logging.error(
                "GetExitCodeProcess failed: %s",
                error,
            )

            return False


        return (
            exit_code.value
            == STILL_ACTIVE
        )


    # --------------------------------------------------------
    # Monitor agent
    # --------------------------------------------------------

    def monitor(self):

        while True:

            if self.process_info is None:

                self.start_agent()

                continue


            if self.is_agent_running():

                time.sleep(2)

                continue


            # ------------------------------------------------
            # Agent exited
            # ------------------------------------------------

            logging.warning(
                "Agent exited."
            )


            self.close_process_handles()


            self.process_info = None


            logging.info(
                "Restarting agent..."
            )


            time.sleep(5)


    # --------------------------------------------------------
    # Stop agent
    # --------------------------------------------------------

    def stop_agent(self):

        if self.process_info is None:

            return


        if not self.is_agent_running():

            self.close_process_handles()

            self.process_info = None

            return


        pid = (
            self.process_info.dwProcessId
        )


        logging.info(
            "Stopping agent. PID=%s",
            pid,
        )


        result = (
            kernel32.TerminateProcess(
                self.process_info.hProcess,
                0,
            )
        )


        if not result:

            error = ctypes.get_last_error()

            logging.error(
                "TerminateProcess failed: %s",
                error,
            )

        else:

            logging.info(
                "Agent terminated. PID=%s",
                pid,
            )


        self.close_process_handles()

        self.process_info = None


    # --------------------------------------------------------
    # Close process handles
    # --------------------------------------------------------

    def close_process_handles(self):

        if self.process_info is None:

            return


        if self.process_info.hThread:

            kernel32.CloseHandle(
                self.process_info.hThread
            )


        if self.process_info.hProcess:

            kernel32.CloseHandle(
                self.process_info.hProcess
            )


        self.process_info = None


# ============================================================
# Main
# ============================================================

def main():

    logging.info(
        "================================"
    )

    logging.info(
        "System-D Supervisor starting"
    )


    supervisor = AgentSupervisor()


    try:

        supervisor.monitor()


    except KeyboardInterrupt:

        logging.info(
            "Supervisor interrupted."
        )


    except Exception:

        logging.exception(
            "Supervisor crashed."
        )

        raise


    finally:

        logging.info(
            "Supervisor stopping..."
        )

        supervisor.stop_agent()

        logging.info(
            "System-D Supervisor stopped"
        )


if __name__ == "__main__":

    main()