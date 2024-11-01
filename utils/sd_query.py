import sounddevice as sd

from rich import print as rprint


def get_sound_device_info():
    return sd.query_devices()

def print_sound_device_info(device_info=None):
    if device_info is None:
        device_info = get_sound_device_info()
    
    for device in device_info:
        rprint(f"{device}\n")


if __name__ == "__main__":
    rprint()
    print_sound_device_info()