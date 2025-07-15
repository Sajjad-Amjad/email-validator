import json
import os
import time
from typing import Dict, List, Set, Optional
from datetime import datetime
from config import PROGRESS_FILE, AUTO_RESUME_ON_RESTART, CLEANUP_PROGRESS_ON_COMPLETION
from utils.logger import setup_logger

logger = setup_logger(__name__)

class ProgressTracker:
    def __init__(self, session_id: str = 'default'):
        self.session_id = session_id
        self.progress_file = PROGRESS_FILE
        self.processed_emails: Set[str] = set()
        self.results: List[Dict] = []
        self.total_emails = 0
        self.start_time = time.time()
        self.session_info = {
            'session_id': session_id,
            'start_time': self.start_time,
            'last_update': self.start_time,
            'total_emails': 0,
            'processed_count': 0,
            'valid_count': 0,
            'invalid_count': 0,
            'skipped_count': 0
        }
        
        logger.info(f"Initializing progress tracker with session: {session_id}")
        
        # Load previous progress if auto-resume is enabled
        if AUTO_RESUME_ON_RESTART:
            self.load_progress()
        
        logger.info("Loading previous progress if exists")
    
    def load_progress(self):
        """Load progress from file if it exists"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Load session info
                if 'session_info' in data:
                    saved_session = data['session_info']
                    if saved_session.get('session_id') == self.session_id:
                        self.session_info.update(saved_session)
                        logger.info(f"Resumed session: {self.session_id}")
                
                # Load processed emails
                if 'processed_emails' in data:
                    self.processed_emails = set(data['processed_emails'])
                    logger.info(f"Loaded {len(self.processed_emails)} processed emails")
                
                # Load results
                if 'results' in data:
                    self.results = data['results']
                    logger.info(f"Loaded {len(self.results)} previous results")
                
                # Update counts
                self.total_emails = self.session_info.get('total_emails', 0)
                processed_count = len(self.processed_emails)
                
                if processed_count > 0:
                    logger.info(f"Resumed from: {processed_count}/{self.total_emails}")
                    print(f"📋 Resumed from previous session: {processed_count:,}/{self.total_emails:,} emails processed")
                
            except Exception as e:
                logger.error(f"Error loading progress: {e}")
                # Reset progress on error
                self.processed_emails.clear()
                self.results.clear()
        else:
            logger.info("No previous progress file found")
    
    def save_progress(self):
        """Save current progress to file"""
        try:
            # Update session info
            self.session_info.update({
                'last_update': time.time(),
                'total_emails': self.total_emails,
                'processed_count': len(self.processed_emails),
                'valid_count': sum(1 for r in self.results if r.get('status') == 'VALID'),
                'invalid_count': sum(1 for r in self.results if r.get('status') == 'INVALID'),
                'skipped_count': sum(1 for r in self.results if r.get('status') == 'SKIPPED')
            })
            
            # Prepare data for saving
            progress_data = {
                'session_info': self.session_info,
                'processed_emails': list(self.processed_emails),
                'results': self.results,
                'saved_at': datetime.now().isoformat()
            }
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.progress_file), exist_ok=True)
            
            # Save to file
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Progress saved: {len(self.processed_emails)} emails processed")
            
        except Exception as e:
            logger.error(f"Error saving progress: {e}")
    
    def add_processed(self, email: str):
        """Add an email to processed set"""
        self.processed_emails.add(email.lower())
        logger.debug(f"Added processed email: {email}")
    
    def is_processed(self, email: str) -> bool:
        """Check if email has been processed"""
        return email.lower() in self.processed_emails
    
    def add_result(self, result: Dict):
        """Add a validation result"""
        self.results.append(result)
        logger.debug(f"Added result for: {result.get('email', 'unknown')}")
    
    def get_results(self) -> List[Dict]:
        """Get all results"""
        return self.results
    
    def set_total(self, total: int):
        """Set total number of emails to process"""
        self.total_emails = total
        self.session_info['total_emails'] = total
        logger.info(f"Set total emails to process: {total}")
    
    def get_progress_percentage(self) -> float:
        """Get current progress as percentage"""
        if self.total_emails == 0:
            return 0.0
        return (len(self.processed_emails) / self.total_emails) * 100
    
    def get_progress_stats(self) -> Dict:
        """Get comprehensive progress statistics"""
        processed_count = len(self.processed_emails)
        progress_percentage = self.get_progress_percentage()
        
        # Calculate processing speed
        elapsed_time = time.time() - self.start_time
        emails_per_second = processed_count / elapsed_time if elapsed_time > 0 else 0
        
        # Calculate ETA
        remaining_emails = self.total_emails - processed_count
        eta_seconds = remaining_emails / emails_per_second if emails_per_second > 0 else 0
        
        # Count results by status
        valid_count = sum(1 for r in self.results if r.get('status') == 'VALID')
        invalid_count = sum(1 for r in self.results if r.get('status') == 'INVALID')
        skipped_count = sum(1 for r in self.results if r.get('status') == 'SKIPPED')
        
        # Calculate success rates
        success_rate = (valid_count / processed_count * 100) if processed_count > 0 else 0
        
        return {
            'session_id': self.session_id,
            'total_emails': self.total_emails,
            'processed_count': processed_count,
            'remaining_count': remaining_emails,
            'progress_percentage': progress_percentage,
            'valid_count': valid_count,
            'invalid_count': invalid_count,
            'skipped_count': skipped_count,
            'success_rate': success_rate,
            'elapsed_time': elapsed_time,
            'emails_per_second': emails_per_second,
            'eta_seconds': eta_seconds,
            'start_time': self.start_time,
            'last_update': time.time()
        }
    
    def get_country_stats(self) -> Dict:
        """Get statistics by country"""
        country_stats = {}
        
        for result in self.results:
            country = result.get('country', 'Unknown')
            if country not in country_stats:
                country_stats[country] = {
                    'total': 0,
                    'valid': 0,
                    'invalid': 0,
                    'skipped': 0
                }
            
            country_stats[country]['total'] += 1
            
            status = result.get('status', 'INVALID')
            if status == 'VALID':
                country_stats[country]['valid'] += 1
            elif status == 'INVALID':
                country_stats[country]['invalid'] += 1
            else:
                country_stats[country]['skipped'] += 1
        
        # Sort by total count
        sorted_countries = sorted(country_stats.items(), key=lambda x: x[1]['total'], reverse=True)
        
        return {
            'total_countries': len(country_stats),
            'countries': dict(sorted_countries),
            'top_countries': sorted_countries[:10]  # Top 10 countries
        }
    
    def get_validation_score_stats(self) -> Dict:
        """Get statistics about validation scores"""
        scores = [r.get('validation_score', 0) for r in self.results if 'validation_score' in r]
        
        if not scores:
            return {
                'total_scored': 0,
                'average_score': 0,
                'min_score': 0,
                'max_score': 0,
                'score_distribution': {}
            }
        
        # Calculate score distribution
        score_ranges = {
            '0-20': 0,
            '21-40': 0,
            '41-60': 0,
            '61-80': 0,
            '81-100': 0
        }
        
        for score in scores:
            if score <= 20:
                score_ranges['0-20'] += 1
            elif score <= 40:
                score_ranges['21-40'] += 1
            elif score <= 60:
                score_ranges['41-60'] += 1
            elif score <= 80:
                score_ranges['61-80'] += 1
            else:
                score_ranges['81-100'] += 1
        
        return {
            'total_scored': len(scores),
            'average_score': sum(scores) / len(scores),
            'min_score': min(scores),
            'max_score': max(scores),
            'score_distribution': score_ranges
        }
    
    def get_spam_trap_stats(self) -> Dict:
        """Get spam trap risk statistics"""
        spam_risks = {}
        
        for result in self.results:
            risk = result.get('spam_trap_risk', 'UNKNOWN')
            spam_risks[risk] = spam_risks.get(risk, 0) + 1
        
        return spam_risks
    
    def export_detailed_report(self, filename: str = None) -> str:
        """Export detailed progress report"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"progress_report_{timestamp}.json"
        
        report = {
            'session_info': self.session_info,
            'progress_stats': self.get_progress_stats(),
            'country_stats': self.get_country_stats(),
            'validation_score_stats': self.get_validation_score_stats(),
            'spam_trap_stats': self.get_spam_trap_stats(),
            'generated_at': datetime.now().isoformat(),
            'total_results': len(self.results)
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Detailed report exported to: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error exporting report: {e}")
            return ""
    
    def reset_progress(self):
        """Reset all progress data"""
        self.processed_emails.clear()
        self.results.clear()
        self.total_emails = 0
        self.start_time = time.time()
        self.session_info = {
            'session_id': self.session_id,
            'start_time': self.start_time,
            'last_update': self.start_time,
            'total_emails': 0,
            'processed_count': 0,
            'valid_count': 0,
            'invalid_count': 0,
            'skipped_count': 0
        }
        
        logger.info("Progress reset")
    
    def cleanup(self):
        """Clean up progress files if configured"""
        if CLEANUP_PROGRESS_ON_COMPLETION:
            try:
                if os.path.exists(self.progress_file):
                    os.remove(self.progress_file)
                    logger.info("Progress file cleaned up")
            except Exception as e:
                logger.error(f"Error cleaning up progress file: {e}")
    
    def get_time_stats(self) -> Dict:
        """Get time-related statistics"""
        elapsed_time = time.time() - self.start_time
        processed_count = len(self.processed_emails)
        
        return {
            'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
            'elapsed_time_seconds': elapsed_time,
            'elapsed_time_formatted': self._format_time(elapsed_time),
            'emails_per_second': processed_count / elapsed_time if elapsed_time > 0 else 0,
            'emails_per_minute': (processed_count / elapsed_time) * 60 if elapsed_time > 0 else 0,
            'emails_per_hour': (processed_count / elapsed_time) * 3600 if elapsed_time > 0 else 0,
            'estimated_completion': self._estimate_completion_time()
        }
    
    def _format_time(self, seconds: float) -> str:
        """Format seconds into human readable time"""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"
    
    def _estimate_completion_time(self) -> str:
        """Estimate completion time"""
        processed_count = len(self.processed_emails)
        remaining_emails = self.total_emails - processed_count
        
        if remaining_emails <= 0 or processed_count == 0:
            return "Completed"
        
        elapsed_time = time.time() - self.start_time
        emails_per_second = processed_count / elapsed_time if elapsed_time > 0 else 0
        
        if emails_per_second == 0:
            return "Unknown"
        
        eta_seconds = remaining_emails / emails_per_second
        completion_time = datetime.fromtimestamp(time.time() + eta_seconds)
        
        return completion_time.strftime('%Y-%m-%d %H:%M:%S')
    
    def get_recent_results(self, limit: int = 10) -> List[Dict]:
        """Get the most recent validation results"""
        return self.results[-limit:] if self.results else []
    
    def search_results(self, query: str, field: str = 'email') -> List[Dict]:
        """Search results by email or other field"""
        query_lower = query.lower()
        matching_results = []
        
        for result in self.results:
            if field in result:
                if query_lower in str(result[field]).lower():
                    matching_results.append(result)
        
        return matching_results
    
    def get_error_summary(self) -> Dict:
        """Get summary of errors encountered"""
        error_summary = {}
        
        for result in self.results:
            if result.get('status') == 'INVALID':
                details = result.get('details', [])
                for detail in details:
                    if 'error' in detail.lower() or 'failed' in detail.lower():
                        error_type = detail.split(':')[0] if ':' in detail else detail
                        error_summary[error_type] = error_summary.get(error_type, 0) + 1
        
        return error_summary