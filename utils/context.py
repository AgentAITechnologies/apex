import json
import platform

def get_platform_details() -> str:
    return json.dumps({
        "os": platform.freedesktop_os_release(),
        "architecture": platform.machine()
    })