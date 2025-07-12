#!/usr/bin/env python3
import sys
import time
from datetime import datetime
from typing import List

from config import BATCH_SIZE, TEST_EMAIL_RECIPIENT, PROXY_FILE
from core.validator import EmailValidator
from utils.file_handler import FileHandler
from utils.progress_tracker import ProgressTracker
from utils.logger import setup_logger, log_progress

logger = setup_logger(__name__)

def setup_test_email():
    logger.info("Setting up test email configuration")
    
    if not TEST_EMAIL_RECIPIENT:
        print("\nTest Email Configuration")
        test_email = input("Enter test email recipient (optional): ").strip()
        if test_email:
            import config
            config.TEST_EMAIL_RECIPIENT = test_email
            logger.info(f"Test email recipient configured")
        else:
            logger.info("No test email recipient configured")

def format_time(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"

def main():
    print("=" * 60)
    print("Email Validator - Bulk Email Verification Tool")
    print("=" * 60)
    
    logger.info("Starting email validation application")
    
    # Initialize components
    file_handler = FileHandler()
    progress_tracker = ProgressTracker()
    
    # Auto-scan for proxy file
    proxy_list = file_handler.read_proxy_file()
    
    if proxy_list:
        print(f"Loaded {len(proxy_list)} proxies")
    else:
        print("Running without proxies")
    
    # Initialize validator
    validator = EmailValidator(proxy_list)
    
    # Get test email recipient
    setup_test_email()
    
    # Read input files
    email_data = file_handler.read_input_files()
    
    if not email_data:
        print("Error: No email files found in data/input/ folder")
        return
    
    # Filter processed emails
    unprocessed_data = []
    for email, password, source_file in email_data:
        if not progress_tracker.is_processed(email):
            unprocessed_data.append((email, password, source_file))
    
    total_to_process = len(unprocessed_data)
    progress_tracker.set_total(total_to_process)
    
    print(f"Processing {total_to_process} emails from {len(set(item[2] for item in email_data))} files")
    
    if total_to_process == 0:
        print("All emails already processed")
        return
    
    # Process in batches
    processed_count = 0
    start_time = time.time()
    
    for i in range(0, total_to_process, BATCH_SIZE):
        batch = unprocessed_data[i:i + BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        total_batches = (total_to_process + BATCH_SIZE - 1) // BATCH_SIZE
        
        # Reset proxy usage
        if proxy_list:
            validator.proxy_manager.reset_usage_count()
        
        # Validate batch
        batch_emails = [(email, password) for email, password, _ in batch]
        results = validator.validate_batch(batch_emails)
        
        # Add source file info
        for i, result in enumerate(results):
            source_file = batch[i][2]
            file_handler.add_result_to_file(result, source_file)
        
        # Update progress
        for result in results:
            progress_tracker.add_processed(result['email'])
            progress_tracker.add_result(result)
        
        # Save results
        batch_results = progress_tracker.get_results()
        file_handler.write_results(batch_results)
        progress_tracker.save_progress()
        
        processed_count += len(batch)
        elapsed_time = time.time() - start_time
        avg_time_per_email = elapsed_time / processed_count
        remaining_emails = total_to_process - processed_count
        eta_seconds = remaining_emails * avg_time_per_email
        
        log_progress(processed_count, total_to_process)
        print(f" | ETA: {format_time(eta_seconds)}")
        
        time.sleep(0.5)  # Reduced from 1 second
    
    # Final summary
    total_time = time.time() - start_time
    
    # Cleanup
    progress_tracker.cleanup()
    
    print(f"\nCompleted in {format_time(total_time)}")
    print("Results saved to data/output/ folder")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProcess interrupted")
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"Error: {e}")
        sys.exit(1)