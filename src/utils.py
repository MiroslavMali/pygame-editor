"""Utility functions, constants, and color definitions"""

# --- Constants ---
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60

# Layout
PROJECT_WIDTH = 250
INSPECTOR_WIDTH = 300
CONSOLE_HEIGHT = 150
MENU_HEIGHT = 40

class Colors:
    """Color definitions for the editor"""
    # Dark theme
    DARK_GRAY = (30, 30, 30)
    PANEL_BG = (40, 40, 40)
    BORDER_COLOR = (60, 60, 60)
    TEXT_COLOR = (220, 220, 220)
    ACCENT_COLOR = (100, 150, 255)
    HOVER_COLOR = (80, 80, 80)
    SELECTION_COLOR = (255, 255, 0)
    
    # Semantic colors
    SUCCESS = (100, 255, 100)
    WARNING = (255, 255, 100)
    ERROR = (255, 100, 100)
    INFO = (100, 150, 255)

def clamp(value, min_val, max_val):
    """Clamp value between min and max"""
    return max(min_val, min(max_val, value))

def lerp(a, b, t):
    """Linear interpolation"""
    return a + (b - a) * t
