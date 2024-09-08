import json
import platform

def get_platform_details() -> str:
    system_info = platform.uname()
    info_dict = { "System": system_info.system, "Release": system_info.release, "Version": system_info.version, "Machine": system_info.machine }
    
    return json.dumps(info_dict)