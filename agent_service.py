import servicemanager

import win32event

import win32service

import win32serviceutil


class RemoteScreenshotService(

    win32serviceutil.ServiceFramework

):

    _svc_name_ = "SystemD"

    _svc_display_name_ = "SystemD"

    _svc_description_ = "SystemD Service"

    def __init__(

        self,

        args,

    ):

        win32serviceutil.ServiceFramework.__init__(

            self,

            args,

        )

        self.stop_event = win32event.CreateEvent(

            None,

            0,

            0,

            None,

        )

    def SvcStop(

        self,

    ):

        self.ReportServiceStatus(

            win32service.SERVICE_STOP_PENDING,

        )

        win32event.SetEvent(

            self.stop_event,

        )

    def SvcDoRun(

        self,

    ):

        servicemanager.LogInfoMsg(

            "SystemD service started."

        )

        win32event.WaitForSingleObject(

            self.stop_event,

            win32event.INFINITE,

        )

        servicemanager.LogInfoMsg(

            "SystemD service stopped."

        )


if __name__ == "__main__":

    win32serviceutil.HandleCommandLine(

        RemoteScreenshotService

    )