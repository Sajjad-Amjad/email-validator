

import sys
import time
import os
from datetime import datetime
from typing import List

from config import BATCH_SIZE, TEST_EMAIL_RECIPIENT
from core.validator import EmailValidator
from utils.file_handler import FileHandler
from utils.progress_tracker import ProgressTracker
from utils.logger import setup_logger, log_progress

logger = setup_logger(__name__)

def setup_test_email():
    """Setup test email recipient for SMTP authentication testing"""
    logger.info("Setting up test email configuration for SMTP auth testing")
    
    # Import config to modify it
    import config
    
    if not config.TEST_EMAIL_RECIPIENT:
        print("\nSMTP Authentication Test Configuration (Optional)")
        print("=" * 60)
        print("For emails that can authenticate, we can send a test email to verify sending.")
        print("This is OPTIONAL - emails are marked VALID based on other validation tests.")
        print("Leave empty to skip SMTP authentication testing.")
        
        test_email = input("Enter test email recipient (optional, press Enter to skip): ").strip()
        
        if test_email and '@' in test_email and '.' in test_email:
            config.TEST_EMAIL_RECIPIENT = test_email
            logger.info(f"Test email recipient configured: {test_email}")
            print(f"SMTP auth test emails will be sent to: {test_email}")
        else:
            config.TEST_EMAIL_RECIPIENT = ""
            logger.info("No test email recipient configured")
            print("SMTP authentication testing disabled")
    else:
        logger.info(f"Test email already configured: {config.TEST_EMAIL_RECIPIENT}")
        print(f"SMTP auth tests will send to: {config.TEST_EMAIL_RECIPIENT}")

def format_time(seconds: float) -> str:
    """Format seconds into human readable time"""
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"

def main():
    """Main validation process"""
    print("=" * 70)
    print("EMAIL VALIDATOR - BULK EMAIL VERIFICATION TOOL")
    print("=" * 70)
    print("=" * 70)
    
    logger.info("Starting email validation")
    
    # Initialize components
    file_handler = FileHandler()
    progress_tracker = ProgressTracker()
    
    # Auto-scan for proxy file
    proxy_list = file_handler.read_proxy_file()
    
    if proxy_list:
        print(f"🔗 Loaded {len(proxy_list)} proxies from proxies.txt")
        logger.info(f"Loaded {len(proxy_list)} proxies from file")
    else:
        print("Running without proxies (using direct connection)")
        logger.info("No proxies loaded - running with direct connection")
    
    # Initialize validator
    validator = EmailValidator(proxy_list)
    
    # Setup test email recipient (optional for SMTP auth testing)
    setup_test_email()
    
    # Read input files
    email_data = file_handler.read_input_files()
    
    if not email_data:
        print("\nERROR: No email files found in data/input/ folder")
        print("Please add .txt files with email:password format")
        print("Example: user@domain.com:password123")
        return
    
    # Filter already processed emails
    unprocessed_data = []
    for email, password, source_file in email_data:
        if not progress_tracker.is_processed(email):
            unprocessed_data.append((email, password, source_file))
    
    total_to_process = len(unprocessed_data)
    total_files = len(set(item[2] for item in email_data))
    
    print(f"\nPROCESSING SUMMARY:")
    print(f"Total emails to process: {total_to_process:,}")
    print(f"Input files: {total_files}")
    print(f"Batch size: {BATCH_SIZE}")
    
    # Import config to get current test email
    import config
    current_test_recipient = getattr(config, 'TEST_EMAIL_RECIPIENT', 'Not configured')
    if current_test_recipient:
        print(f"SMTP auth test recipient: {current_test_recipient}")
    else:
        print(f"SMTP auth testing: Disabled")
    
    
    if total_to_process == 0:
        print("\n✅ All emails already processed!")
        return
    
    progress_tracker.set_total(total_to_process)
    
    # Process in batches
    processed_count = 0
    start_time = time.time()
    
    print(f"\n🔄 Starting validation process...")
    print("-" * 70)
    
    for i in range(0, total_to_process, BATCH_SIZE):
        batch = unprocessed_data[i:i + BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        total_batches = (total_to_process + BATCH_SIZE - 1) // BATCH_SIZE
        
        print(f"\n📦 Processing batch {batch_num:,}/{total_batches:,} ({len(batch)} emails)")
        logger.info(f"Processing batch {batch_num}/{total_batches} with {len(batch)} emails")
        
        # Reset proxy usage for each batch
        if proxy_list:
            validator.proxy_manager.reset_usage_count()
        
        # Validate batch
        batch_emails = [(email, password) for email, password, _ in batch]
        results = validator.validate_batch(batch_emails)
        
        # Add source file info and update progress
        for j, result in enumerate(results):
            source_file = batch[j][2]
            file_handler.add_result_to_file(result, source_file)
            progress_tracker.add_processed(result['email'])
            progress_tracker.add_result(result)
        
        # Save results
        batch_results = progress_tracker.get_results()
        file_handler.write_results(batch_results)
        progress_tracker.save_progress()
        
        # Update progress display
        processed_count += len(batch)
        elapsed_time = time.time() - start_time
        avg_time_per_email = elapsed_time / processed_count if processed_count > 0 else 0
        remaining_emails = total_to_process - processed_count
        eta_seconds = remaining_emails * avg_time_per_email if avg_time_per_email > 0 else 0
        
        # Show progress
        progress_bar = log_progress(processed_count, total_to_process)
        print(f"\r{progress_bar} | ETA: {format_time(eta_seconds)}", end='')
        
        # Brief pause between batches
        time.sleep(0.5)
    
    print("\n")  # New line after progress bar
    
    # Calculate final stats
    total_time = time.time() - start_time
    emails_per_second = processed_count / total_time if total_time > 0 else 0
    
    # Show final summary
    show_final_summary(file_handler, progress_tracker)
    
    # Cleanup
    progress_tracker.cleanup()
    
    logger.info(f"Processing completed in {format_time(total_time)}")

def show_final_summary(file_handler, progress_tracker):
    """Show detailed final validation summary"""
    print("\n" + "=" * 70)
    print("FINAL VALIDATION SUMMARY")
    print("=" * 70)
    
    try:
        # Get summary from progress tracker
        results = progress_tracker.get_results()
        
        valid_count = sum(1 for r in results if r['status'] == 'VALID')
        invalid_count = sum(1 for r in results if r['status'] == 'INVALID')
        skipped_count = sum(1 for r in results if r['status'] == 'SKIPPED')
        
        total_processed = valid_count + invalid_count + skipped_count
        
        # Calculate percentages
        valid_pct = (valid_count / total_processed * 100) if total_processed > 0 else 0
        invalid_pct = (invalid_count / total_processed * 100) if total_processed > 0 else 0
        skipped_pct = (skipped_count / total_processed * 100) if total_processed > 0 else 0
        
        print(f"VALID emails: {valid_count:,} ({valid_pct:.1f}%)")
        print(f"INVALID emails: {invalid_count:,} ({invalid_pct:.1f}%)")
        print(f"SKIPPED emails: {skipped_count:,} ({skipped_pct:.1f}%)")
        print(f"OTAL processed: {total_processed:,}")
        
        # SMTP Authentication Summary
        smtp_success = sum(1 for r in results if r.get('smtp_auth_result') == 'SUCCESS')
        smtp_failed = sum(1 for r in results if r.get('smtp_auth_result') == 'FAILED')
        smtp_not_tested = sum(1 for r in results if r.get('smtp_auth_result') == 'NOT_TESTED')
        smtp_error = sum(1 for r in results if r.get('smtp_auth_result') == 'ERROR')
        
        print(f"\n📬 SMTP AUTHENTICATION SUMMARY:")
        print(f"✅ Can send emails: {smtp_success:,}")
        print(f"❌ Cannot send emails: {smtp_failed:,}")
        print(f"⚠️  Not tested: {smtp_not_tested:,}")
        print(f"💥 Errors: {smtp_error:,}")
        
        # Show country breakdown for valid emails
        if valid_count > 0:
            print(f"\n🌍 COUNTRY BREAKDOWN (Valid emails only):")
            country_stats = {}
            for result in results:
                if result['status'] == 'VALID':
                    country = result.get('country', 'Unknown')
                    country_stats[country] = country_stats.get(country, 0) + 1
            
            for country, count in sorted(country_stats.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"   🌐 {country}: {count}")
        
        # Show validation score distribution
        if results:
            scores = [r.get('validation_score', 0) for r in results]
            avg_score = sum(scores) / len(scores) if scores else 0
            print(f"\nVALIDATION SCORES:")
            print(f"Average score: {avg_score:.1f}/100")
            print(f"Score distribution:")
            
            score_ranges = {
                '81-100': sum(1 for s in scores if s >= 81),
                '61-80': sum(1 for s in scores if 61 <= s <= 80),
                '41-60': sum(1 for s in scores if 41 <= s <= 60),
                '21-40': sum(1 for s in scores if 21 <= s <= 40),
                '0-20': sum(1 for s in scores if s <= 20)
            }
            
            for score_range, count in score_ranges.items():
                if count > 0:
                    print(f"   📊 {score_range}: {count} emails")
        
        
        logger.info(f"Final summary - Valid: {valid_count}, Invalid: {invalid_count}, Skipped: {skipped_count}")
        logger.info(f"SMTP auth summary - Success: {smtp_success}, Failed: {smtp_failed}, Not tested: {smtp_not_tested}")
        
    except Exception as e:
        logger.error(f"Error showing summary: {e}")
        print("Error generating summary")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user")
        logger.info("Process interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        print(f"\n Unexpected error: {e}")
        print("Check logs for details")
        sys.exit(1)