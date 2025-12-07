import json
import os
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

class RequestLogger:
    def __init__(self, log_file: str = "estimation_logs.json"):
        # Get the absolute path to the log file
        # Place it in the same directory as this file or project root
        if not os.path.isabs(log_file):
            # Get the directory where this file is located
            current_dir = Path(__file__).parent.parent
            self.log_file = os.path.join(current_dir, log_file)
        else:
            self.log_file = log_file
        
        self._ensure_log_file()
    
    def _ensure_log_file(self):
        """Create log file if it doesn't exist"""
        try:
            if not os.path.exists(self.log_file):
                # Ensure directory exists
                os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
                with open(self.log_file, 'w') as f:
                    json.dump([], f)
                print(f"Log file created at: {self.log_file}")
            else:
                print(f"Using existing log file at: {self.log_file}")
        except Exception as e:
            print(f"Error creating log file: {e}")
    
    def log_request(self, image_url: str, width_inches: float, result: Dict[str, Any] = None):
        """Log an estimation request"""
        try:
            # Read existing logs
            with open(self.log_file, 'r') as f:
                logs = json.load(f)
            
            # Create new log entry
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "url": image_url,
                "width": width_inches,
            }
            
            # Add result if available
            if result:
                log_entry["stitch_count"] = result.get("stitch_count")
                log_entry["details"] = result.get("details")
            
            # Append new entry
            logs.append(log_entry)
            
            # Write back to file
            with open(self.log_file, 'w') as f:
                json.dump(logs, f, indent=2)
            
            print(f"Logged request: {image_url} - {width_inches} inches")
                
        except Exception as e:
            print(f"Error logging request: {e}")
            import traceback
            traceback.print_exc()
    
    def get_logs(self, limit: int = None):
        """Retrieve logs, optionally limited to most recent N entries"""
        try:
            with open(self.log_file, 'r') as f:
                logs = json.load(f)
            
            if limit:
                return logs[-limit:]
            return logs
        except Exception as e:
            print(f"Error reading logs: {e}")
            return []
    
    def clear_logs(self):
        """Clear all logs"""
        try:
            with open(self.log_file, 'w') as f:
                json.dump([], f)
            print(f"Logs cleared at: {self.log_file}")
        except Exception as e:
            print(f"Error clearing logs: {e}")