#!/usr/bin/env python3
"""Main entry point for Pygame Editor"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from editor import PygameEditor

def main():
    """Main application entry point"""
    try:
        editor = PygameEditor()
        editor.run()
    except KeyboardInterrupt:
        print("\nEditor closed by user")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
