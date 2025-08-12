"""System classes for the editor"""

class Console:
    """Console system for displaying messages"""
    def __init__(self):
        self.messages = []
        self.max_messages = 20
        
    def log(self, message):
        """Add a message to the console"""
        self.messages.append(message)
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)
        print(message)  # Also print to terminal for debugging
        
    def clear(self):
        """Clear all messages"""
        self.messages.clear()
        
    def get_messages(self):
        """Get all messages"""
        return self.messages
