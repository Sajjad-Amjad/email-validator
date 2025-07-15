"""
Email Validator Configuration
All settings and parameters for the email validation system
"""

import os

# Directory Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
INPUT_FOLDER = os.path.join(DATA_DIR, 'input')
OUTPUT_FOLDER = os.path.join(DATA_DIR, 'output')
LOGS_FOLDER = os.path.join(BASE_DIR, 'logs')

# File Configuration
PROXY_FILE = 'proxies.txt'
PROGRESS_FILE = os.path.join(DATA_DIR, 'progress.json')
LOG_FILE = os.path.join(LOGS_FOLDER, 'email_validator.log')

# Processing Configuration
BATCH_SIZE = 10  # Number of emails to process in each batch
MAX_WORKERS = 5  # Maximum number of threads for concurrent processing
DELAY_BETWEEN_BATCHES = 0.5  # Delay in seconds between batches

# Network Configuration
TIMEOUT = 10  # General timeout for network operations
SMTP_TIMEOUT = 15  # SMTP-specific timeout
SMTP_PORT = 587  # Default SMTP port
DNS_TIMEOUT = 5  # DNS query timeout

# Proxy Configuration
PROXY_ROTATION_COUNT = 50  # Number of requests before rotating proxy
PROXY_TIMEOUT = 10  # Proxy connection timeout
MAX_PROXY_RETRIES = 3  # Maximum retry attempts per proxy

# Email Configuration
TEST_EMAIL_RECIPIENT = ""  # Will be set during runtime
TEST_EMAIL_SUBJECT = "Email Validation Test"
TEST_EMAIL_BODY = "This is a test email from the Email Validator tool."

# Validation Configuration
ENABLE_COUNTRY_DETECTION = True
ENABLE_SPAM_TRAP_DETECTION = True
ENABLE_MISSPELLING_DETECTION = True
ENABLE_DISPOSABLE_DETECTION = True

# Scoring Configuration
VALIDATION_SCORE_WEIGHTS = {
    'syntax': 20,
    'dns': 15,
    'smtp_connection': 20,
    'mailbox_exists': 15,
    'authentication': 25,
    'test_email': 5
}

# Logging Configuration
LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%H:%M:%S'
ENABLE_FILE_LOGGING = True
ENABLE_CONSOLE_LOGGING = True

# API Configuration (for geolocation)
GEOLOCATION_APIS = [
    'http://ip-api.com/json/',
    'https://ipapi.co/json/',
    'https://api.ipify.org?format=json'
]

# Rate Limiting
MAX_REQUESTS_PER_MINUTE = 60
RATE_LIMIT_DELAY = 1  # Delay in seconds when rate limit is hit

# Error Handling
MAX_RETRIES = 3
RETRY_DELAY = 2  # Delay between retries in seconds
CONTINUE_ON_ERROR = True

# Output Configuration
OUTPUT_FORMATS = ['csv', 'txt']
INCLUDE_DETAILED_RESULTS = True
SEPARATE_FILES_BY_STATUS = True  # Create valid.txt, invalid.txt, skipped.txt

# Security Configuration
VALIDATE_SSL_CERTIFICATES = True
ALLOW_SELF_SIGNED_CERTIFICATES = False

# Performance Configuration
MEMORY_LIMIT_MB = 500  # Maximum memory usage
CHUNK_SIZE = 1000  # Number of emails to process before saving progress

# Progress Tracking
SAVE_PROGRESS_EVERY_N_BATCHES = 5
AUTO_RESUME_ON_RESTART = True
CLEANUP_PROGRESS_ON_COMPLETION = True

# Client-Specific Requirements
SEND_TEST_EMAIL_FOR_VALID = True  # Send test email to verify working credentials
REQUIRE_TEST_EMAIL_RECIPIENT = True  # Require test email recipient to be configured
GENERATE_COUNTRY_REPORTS = True  # Generate country-based statistics
PROXY_SUPPORT_ENABLED = True  # Enable proxy rotation support

# Feature Flags
ENABLE_DUPLICATE_CHECKING = True
ENABLE_HARD_BOUNCE_DETECTION = True
ENABLE_SMTP_AVAILABILITY_CHECK = True
ENABLE_MX_RECORD_VALIDATION = True
ENABLE_MAILBOX_EXISTENCE_CHECK = True