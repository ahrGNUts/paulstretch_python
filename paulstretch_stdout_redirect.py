#!/usr/bin/env python
import sys
import threading

class StdoutRedirector:
    """
    A class to redirect stdout to a callback function.
    This is used to capture progress updates from the paulstretch scripts.
    """
    def __init__(self, callback=None):
        self.callback = callback
        self.original_stdout = sys.stdout
        self.lock = threading.Lock()
        self.capture_enabled = False
        
    def write(self, text):
        # Always write to the original stdout
        self.original_stdout.write(text)
        
        # If capture is enabled and we have a callback, call it
        if self.capture_enabled and self.callback:
            # Parse progress percentage from the output
            if "%" in text and not "Error" in text:
                try:
                    # Extract percentage from text like "50 % "
                    percentage = int(text.strip().split("%")[0])
                    self.callback(percentage)
                except (ValueError, IndexError):
                    pass
    
    def flush(self):
        self.original_stdout.flush()
    
    def enable_capture(self):
        """Enable capturing stdout"""
        with self.lock:
            self.capture_enabled = True
    
    def disable_capture(self):
        """Disable capturing stdout"""
        with self.lock:
            self.capture_enabled = False
    
    def __enter__(self):
        """Context manager entry point"""
        sys.stdout = self
        self.enable_capture()
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        """Context manager exit point"""
        self.disable_capture()
        sys.stdout = self.original_stdout 