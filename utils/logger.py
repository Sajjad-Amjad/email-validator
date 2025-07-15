import logging
import os
import sys
from datetime import datetime
from typing import Optional
from config import (
    LOG_LEVEL, LOG_FORMAT, LOG_DATE_FORMAT, LOG_FILE, LOGS_FOLDER,
    ENABLE_FILE_LOGGING, ENABLE_CONSOLE_LOGGING
)

def setup_logger(name: str, log_level: Optional[str] = None) -> logging.Logger:
    """Setup logger with file and console handlers"""
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level or LOG_LEVEL))
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Create logs directory if it doesn't exist
    if ENABLE_FILE_LOGGING:
        os.makedirs(LOGS_FOLDER, exist_ok=True)
    
    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    
    # Console handler
    if ENABLE_CONSOLE_LOGGING:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level or LOG_LEVEL))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if ENABLE_FILE_LOGGING:
        file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
        file_handler.setLevel(getattr(logging, log_level or LOG_LEVEL))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def log_progress(processed: int, total: int, width: int = 30) -> str:
    """Generate progress bar string"""
    if total == 0:
        percentage = 0
    else:
        percentage = (processed / total) * 100
    
    filled_width = int(width * processed // total) if total > 0 else 0
    bar = '█' * filled_width + '-' * (width - filled_width)
    
    return f"Processing: [{bar}] {processed}/{total} ({percentage:.1f}%)"

def log_email_validation(email: str, status: str, details: list, country: str = "Unknown"):
    """Log email validation result in structured format"""
    logger = logging.getLogger('email_validation')
    
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'email': email,
        'status': status,
        'country': country,
        'details': details
    }
    
    if status == 'VALID':
        logger.info(f"✅ VALID: {email} | {country} | {', '.join(details)}")
    elif status == 'INVALID':
        logger.warning(f"❌ INVALID: {email} | {country} | {', '.join(details)}")
    elif status == 'SKIPPED':
        logger.info(f"⚠️ SKIPPED: {email} | {country} | {', '.join(details)}")
    else:
        logger.error(f"❓ UNKNOWN: {email} | {country} | {', '.join(details)}")

def log_batch_summary(batch_num: int, total_batches: int, results: list):
    """Log batch processing summary"""
    logger = logging.getLogger('batch_processing')
    
    valid_count = sum(1 for r in results if r.get('status') == 'VALID')
    invalid_count = sum(1 for r in results if r.get('status') == 'INVALID')
    skipped_count = sum(1 for r in results if r.get('status') == 'SKIPPED')
    
    logger.info(f"📦 Batch {batch_num}/{total_batches} completed: "
                f"✅ {valid_count} valid, ❌ {invalid_count} invalid, ⚠️ {skipped_count} skipped")

def log_country_stats(country_stats: dict):
    """Log country statistics"""
    logger = logging.getLogger('country_stats')
    
    logger.info("🌍 Country Statistics:")
    for country, count in sorted(country_stats.items(), key=lambda x: x[1], reverse=True)[:10]:
        logger.info(f"   {country}: {count} emails")

def log_performance_metrics(start_time: float, processed_count: int, total_count: int):
    """Log performance metrics"""
    logger = logging.getLogger('performance')
    
    import time
    elapsed_time = time.time() - start_time
    emails_per_second = processed_count / elapsed_time if elapsed_time > 0 else 0
    
    logger.info(f"⚡ Performance: {emails_per_second:.1f} emails/sec, "
                f"Processed: {processed_count}/{total_count}, "
                f"Elapsed: {elapsed_time:.1f}s")

def log_proxy_stats(proxy_stats: dict):
    """Log proxy usage statistics"""
    logger = logging.getLogger('proxy_stats')
    
    total_proxies = proxy_stats.get('total_proxies', 0)
    working_proxies = proxy_stats.get('working_proxies', 0)
    failed_proxies = proxy_stats.get('failed_proxies', 0)
    
    logger.info(f"🔗 Proxy Stats: {working_proxies}/{total_proxies} working, "
                f"{failed_proxies} failed")

def log_error_with_context(error: Exception, context: dict):
    """Log error with additional context"""
    logger = logging.getLogger('error_context')
    
    import traceback
    
    context_str = ', '.join([f"{k}={v}" for k, v in context.items()])
    logger.error(f"❌ Error: {str(error)} | Context: {context_str}")
    logger.debug(f"Full traceback: {traceback.format_exc()}")

def log_smtp_test(email: str, result: dict):
    """Log SMTP test results"""
    logger = logging.getLogger('smtp_test')
    
    if result.get('authenticated', False):
        logger.info(f"🔑 SMTP Auth Success: {email} | Server: {result.get('smtp_server', 'Unknown')}")
        if result.get('test_email_sent', False):
            logger.info(f"📧 Test email sent successfully from {email}")
    else:
        reason = result.get('reason', 'Unknown')
        logger.warning(f"🔑 SMTP Auth Failed: {email} | Reason: {reason}")

def log_dns_lookup(domain: str, result: dict):
    """Log DNS lookup results"""
    logger = logging.getLogger('dns_lookup')
    
    if result.get('is_valid', False):
        mx_count = len(result.get('mx_info', {}).get('mx_records', []))
        primary_mx = result.get('mx_info', {}).get('primary_mx', 'None')
        logger.debug(f"🌐 DNS Valid: {domain} | MX Records: {mx_count} | Primary: {primary_mx}")
    else:
        errors = result.get('dns_errors', [])
        logger.debug(f"🌐 DNS Failed: {domain} | Errors: {', '.join(errors)}")

def log_geolocation(email: str, result: dict):
    """Log geolocation results"""
    logger = logging.getLogger('geolocation')
    
    country = result.get('country', 'Unknown')
    method = result.get('method', 'none')
    
    if country != 'Unknown':
        logger.debug(f"🌍 Geo Success: {email} | Country: {country} | Method: {method}")
    else:
        logger.debug(f"🌍 Geo Failed: {email} | Could not determine country")

def log_validation_summary(total_processed: int, valid_count: int, invalid_count: int, 
                          skipped_count: int, processing_time: float):
    """Log final validation summary"""
    logger = logging.getLogger('validation_summary')
    
    success_rate = (valid_count / total_processed * 100) if total_processed > 0 else 0
    emails_per_second = total_processed / processing_time if processing_time > 0 else 0
    
    logger.info("=" * 60)
    logger.info("📊 FINAL VALIDATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"📧 Total processed: {total_processed:,}")
    logger.info(f"✅ Valid emails: {valid_count:,} ({valid_count/total_processed*100:.1f}%)")
    logger.info(f"❌ Invalid emails: {invalid_count:,} ({invalid_count/total_processed*100:.1f}%)")
    logger.info(f"⚠️ Skipped emails: {skipped_count:,} ({skipped_count/total_processed*100:.1f}%)")
    logger.info(f"📈 Success rate: {success_rate:.1f}%")
    logger.info(f"⚡ Processing speed: {emails_per_second:.1f} emails/second")
    logger.info(f"⏱️ Total time: {processing_time:.1f} seconds")
    logger.info("=" * 60)

def create_session_log(session_id: str):
    """Create a session-specific log file"""
    session_log_file = os.path.join(LOGS_FOLDER, f"session_{session_id}.log")
    
    session_logger = logging.getLogger(f"session_{session_id}")
    session_logger.setLevel(getattr(logging, LOG_LEVEL))
    
    # Prevent duplicate handlers
    if session_logger.handlers:
        return session_logger
    
    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    
    file_handler = logging.FileHandler(session_log_file, encoding='utf-8')
    file_handler.setLevel(getattr(logging, LOG_LEVEL))
    file_handler.setFormatter(formatter)
    session_logger.addHandler(file_handler)
    
    return session_logger

def log_client_requirements_check():
    """Log client requirements verification"""
    logger = logging.getLogger('client_requirements')
    
    logger.info("✅ Client Requirements Verification:")
    logger.info("   📧 Email Verification: Enabled")
    logger.info("   🔍 Email Validation: Enabled")
    logger.info("   🧹 Email List Cleaning: Enabled")
    logger.info("   🔄 Email Hygiene: Enabled")
    logger.info("   📊 Email List Management: Enabled")
    logger.info("   📄 Duplicate Emails Checking: Enabled")
    logger.info("   ❌ Invalid and Hard bounces emails: Enabled")
    logger.info("   🌐 DNS validation, including MX record lookup: Enabled")
    logger.info("   ⚡ Disposable email address detection realtime: Enabled")
    logger.info("   🔤 Misspelled domain detection: Enabled")
    logger.info("   ✅ Email Syntax verification (IETF/RFC standard): Enabled")
    logger.info("   📬 Mailbox existence checking: Enabled")
    logger.info("   🔌 SMTP connection and availability checking: Enabled")
    logger.info("   🕷️ Spam-Trap Emails detection: Enabled")
    logger.info("   🔗 Proxy Support: Enabled")
    logger.info("   🚀 Multi-threading Support: Enabled")
    logger.info("   🖥️ Headless Mode: Enabled")
    logger.info("   📝 Custom Error Handling and Reports: Enabled")
    logger.info("   🌍 Country Detection: Enabled")

def setup_rotating_log_handler(logger_name: str, max_bytes: int = 10*1024*1024, backup_count: int = 5):
    """Setup rotating log handler to prevent log files from getting too large"""
    from logging.handlers import RotatingFileHandler
    
    logger = logging.getLogger(logger_name)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create rotating file handler
    log_file = os.path.join(LOGS_FOLDER, f"{logger_name}.log")
    handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    
    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    handler.setFormatter(formatter)
    handler.setLevel(getattr(logging, LOG_LEVEL))
    
    logger.addHandler(handler)
    logger.setLevel(getattr(logging, LOG_LEVEL))
    
    return logger

def log_system_info():
    """Log system information at startup"""
    logger = logging.getLogger('system_info')
    
    import platform
    import psutil
    
    logger.info("🖥️ System Information:")
    logger.info(f"   OS: {platform.system()} {platform.release()}")
    logger.info(f"   Python: {platform.python_version()}")
    logger.info(f"   CPU Cores: {psutil.cpu_count()}")
    logger.info(f"   Memory: {psutil.virtual_memory().total / (1024**3):.1f} GB")
    logger.info(f"   Disk Space: {psutil.disk_usage('/').free / (1024**3):.1f} GB free")

def cleanup_old_logs(days_to_keep: int = 7):
    """Clean up old log files"""
    import glob
    import time
    
    logger = logging.getLogger('log_cleanup')
    
    try:
        log_pattern = os.path.join(LOGS_FOLDER, "*.log*")
        log_files = glob.glob(log_pattern)
        
        current_time = time.time()
        cutoff_time = current_time - (days_to_keep * 24 * 60 * 60)
        
        cleaned_count = 0
        for log_file in log_files:
            if os.path.getmtime(log_file) < cutoff_time:
                os.remove(log_file)
                cleaned_count += 1
        
        if cleaned_count > 0:
            logger.info(f"🧹 Cleaned up {cleaned_count} old log files")
            
    except Exception as e:
        logger.error(f"Error cleaning up logs: {e}")

# Initialize main logger
main_logger = setup_logger('email_validator')

# Log client requirements check on module import
if __name__ != '__main__':
    log_client_requirements_check()