from typing import Literal, Tuple, List, Union, Optional
import time
from dataclasses import dataclass
import pyautogui
import platform

@dataclass
class ScreenDimensions:
    width: int
    height: int
    display_number: int

class Computer:
    def __init__(self, dimensions: ScreenDimensions):
        """Initialize computer interface with screen dimensions"""
        self.dimensions = dimensions
        
        # Configure pyautogui safety and performance settings
        pyautogui.FAILSAFE = True  # Move mouse to corner to abort
        pyautogui.PAUSE = 0.1  # Small delay between actions for stability
        
        # Set up OS-specific key mappings
        self.os = platform.system()
        self.modifier_keys = {
            'Windows': {'ctrl': 'ctrl', 'alt': 'alt', 'shift': 'shift', 'win': 'win'},
            'Darwin': {'ctrl': 'command', 'alt': 'option', 'shift': 'shift', 'win': 'command'},
            'Linux': {'ctrl': 'ctrl', 'alt': 'alt', 'shift': 'shift', 'win': 'win'}
        }[self.os]

    def _validate_coordinates(self, x: int, y: int) -> Tuple[int, int]:
        """Ensure coordinates are within screen bounds"""
        x = max(0, min(x, self.dimensions.width))
        y = max(0, min(y, self.dimensions.height))
        return x, y

    def press_key(self, key: str) -> None:
        """Press a single key"""
        pyautogui.press(key)

    def press_keys(self, keys: List[str]) -> None:
        """Press a combination of keys"""
        # Map keys to OS-specific modifiers
        mapped_keys = [self.modifier_keys.get(k.lower(), k) for k in keys]
        pyautogui.hotkey(*mapped_keys)

    def type_text(self, text: str) -> None:
        """Type text with proper pacing and special character handling"""
        pyautogui.write(text, interval=0.01)  # Small delay between characters

    def get_cursor_position(self) -> Tuple[int, int]:
        """Get current cursor position"""
        x, y = pyautogui.position()
        return self._validate_coordinates(x, y)

    def move_cursor(self, x: int, y: int, duration: float = 0.2) -> None:
        """Move cursor to coordinates with smooth motion"""
        x, y = self._validate_coordinates(x, y)
        pyautogui.moveTo(x, y, duration=duration)

    def click(self, 
              button: Literal["left", "middle", "right"] = "left",
              clicks: int = 1) -> None:
        """Click at current cursor position"""
        pyautogui.click(button=button, clicks=clicks)

    def double_click(self) -> None:
        """Double click at current cursor position"""
        self.click(clicks=2)

    def click_and_drag(self, 
                      target_x: int, 
                      target_y: int, 
                      button: Literal["left", "middle", "right"] = "left",
                      duration: float = 0.2) -> None:
        """Click, hold, drag to coordinates, and release"""
        target_x, target_y = self._validate_coordinates(target_x, target_y)
        pyautogui.mouseDown(button=button)
        pyautogui.moveTo(target_x, target_y, duration=duration)
        pyautogui.mouseUp(button=button)

    def take_screenshot(self, 
                       region: Optional[Tuple[int, int, int, int]] = None) -> bytes:
        """Take screenshot of specified region or full screen"""
        return pyautogui.screenshot(region=region)._tobytes()

    def wait_for_color(self, 
                      x: int, 
                      y: int, 
                      expected_color: Union[str, Tuple[int, int, int]],
                      timeout: int = 30,
                      on_match: Optional[callable] = None) -> bool:
        """
        Wait for a pixel to match an expected color.
        
        Args:
            x: X coordinate to check
            y: Y coordinate to check
            expected_color: Color to wait for (RGB tuple or common color name)
            timeout: Maximum seconds to wait
            on_match: Optional callback to execute when color matches
            
        Returns:
            bool: True if color matched within timeout, False otherwise
        """
        if isinstance(expected_color, str):
            # Map common color names to RGB values
            color_map = {
                'red': (255, 0, 0),
                'green': (0, 255, 0),
                'blue': (0, 0, 255),
                'black': (0, 0, 0),
                'white': (255, 255, 255),
                # Add more as needed
            }
            expected_color = color_map.get(expected_color.lower(), (0, 0, 0))
            
        end_time = time.time() + timeout
        while time.time() < end_time:
            pixel_color = pyautogui.pixel(x, y)
            if pixel_color == expected_color:
                if on_match:
                    on_match()
                return True
            time.sleep(0.1)
        return False