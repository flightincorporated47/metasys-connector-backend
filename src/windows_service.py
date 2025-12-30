# src/windows_service.py
import win32serviceutil
import win32service
import win32event
import subprocess
import sys
import os


class MetasysConnectorService(win32serviceutil.ServiceFramework):
    _svc_name_ = "MetasysConnector"
    _svc_display_name_ = "Metasys Connector"
    _svc_description_ = "Polls Metasys and publishes deltas to Site Management App"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)

    def SvcDoRun(self):
        # Ensure working directory is project root
        project_root = os.path.dirname(os.path.dirname(__file__))
        os.chdir(project_root)

        cmd = [
            sys.executable,
            "-m",
            "src.main",
            "--config",
            "config\\pilot_generated.yml",
        ]

        subprocess.call(cmd)


if __name__ == "__main__":
    win32serviceutil.HandleCommandLine(MetasysConnectorService)
