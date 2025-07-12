import json
import os
from typing import Dict, List, Set
from config import PROGRESS_FOLDER
from utils.logger import setup_logger

logger = setup_logger(__name__)

class ProgressTracker:
    def __init__(self, session_id: str = None):
        self.session_id = session_id or "default"
        self.progress_file = os.path.join(PROGRESS_FOLDER, f"{self.session_id}_progress.json")
        self.processed_emails_file = os.path.join(PROGRESS_FOLDER, f"{self.session_id}_processed.json")
        
        logger.info(f"Initializing progress tracker with session: {self.session_id}")
        os.makedirs(PROGRESS_FOLDER, exist_ok=True)
        
        self.processed_count = 0
        self.total_count = 0
        self.processed_emails = set()
        self.current_results = []
        
        self.load_progress()
    
    def load_progress(self):
        logger.info("Loading previous progress if exists")
        try:
            if os.path.exists(self.progress_file):
                with open(self.progress_file, 'r') as f:
                    data = json.load(f)
                    self.processed_count = data.get('processed_count', 0)
                    self.total_count = data.get('total_count', 0)
                    logger.info(f"Loaded progress: {self.processed_count}/{self.total_count} emails")
            
            if os.path.exists(self.processed_emails_file):
                with open(self.processed_emails_file, 'r') as f:
                    self.processed_emails = set(json.load(f))
                    logger.info(f"Loaded {len(self.processed_emails)} processed email records")
                    
        except Exception as e:
            logger.error(f"Error loading progress: {e}")
    
    def save_progress(self):
        logger.debug("Saving current progress")
        try:
            progress_data = {
                'processed_count': self.processed_count,
                'total_count': self.total_count,
                'session_id': self.session_id
            }
            
            with open(self.progress_file, 'w') as f:
                json.dump(progress_data, f)
            
            with open(self.processed_emails_file, 'w') as f:
                json.dump(list(self.processed_emails), f)
                
            logger.debug("Progress saved successfully")
                
        except Exception as e:
            logger.error(f"Error saving progress: {e}")
    
    def is_processed(self, email: str) -> bool:
        return email.lower() in self.processed_emails
    
    def add_processed(self, email: str):
        self.processed_emails.add(email.lower())
        self.processed_count += 1
        logger.debug(f"Marked email as processed: {email}")
    
    def add_result(self, result: Dict):
        self.current_results.append(result)
        logger.debug(f"Added result to current batch")
    
    def get_results(self) -> List[Dict]:
        results = self.current_results.copy()
        self.current_results.clear()
        logger.debug(f"Retrieved {len(results)} results from current batch")
        return results
    
    def set_total(self, total: int):
        self.total_count = total
        logger.info(f"Set total count to: {total}")
        self.save_progress()
    
    def get_progress_percentage(self) -> float:
        if self.total_count == 0:
            return 0
        return (self.processed_count / self.total_count) * 100
    
    def cleanup(self):
        logger.info("Cleaning up progress files")
        try:
            if os.path.exists(self.progress_file):
                os.remove(self.progress_file)
                logger.debug("Removed progress file")
            if os.path.exists(self.processed_emails_file):
                os.remove(self.processed_emails_file)
                logger.debug("Removed processed emails file")
        except Exception as e:
            logger.error(f"Error cleaning up progress files: {e}")