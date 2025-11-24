from collections import deque
from threading import Lock
from datetime import datetime

class ScanQueue:
    """Manages scan queue and concurrency limits"""
    
    def __init__(self, max_concurrent=3):
        self.max_concurrent = max_concurrent
        self.queue = deque()  # Pending scans
        self.lock = Lock()
    
    def add_to_queue(self, scan_id, target_id, scan_type, scanner_args, openvas_config_id=None):
        """Add scan to queue"""
        with self.lock:
            self.queue.append({
                'scan_id': scan_id,
                'target_id': target_id,
                'scan_type': scan_type,
                'scanner_args': scanner_args,
                'openvas_config_id': openvas_config_id,
                'queued_at': datetime.utcnow()
            })
            return len(self.queue)  # Return queue position
    
    def get_next(self):
        """Get next scan from queue"""
        with self.lock:
            if self.queue:
                return self.queue.popleft()
            return None
    
    def get_queue_position(self, scan_id):
        """Get position of scan in queue (1-indexed)"""
        with self.lock:
            for i, item in enumerate(self.queue, 1):
                if item['scan_id'] == scan_id:
                    return i
            return 0  # Not in queue
    
    def remove_from_queue(self, scan_id):
        """Remove scan from queue"""
        with self.lock:
            self.queue = deque([item for item in self.queue if item['scan_id'] != scan_id])
    
    def get_queue_size(self):
        """Get current queue size"""
        with self.lock:
            return len(self.queue)
    
    def get_all_queued(self):
        """Get all queued scans"""
        with self.lock:
            return list(self.queue)
