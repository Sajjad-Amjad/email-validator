import os

# File paths
INPUT_FOLDER = "data/input/"
OUTPUT_FOLDER = "data/output/"
PROGRESS_FOLDER = "data/progress/"

# Processing settings
BATCH_SIZE = 10
MAX_WORKERS = 5
DELIMITER = ":"  # Changed from "|" to ":" as per client's data format

# Proxy settings
PROXY_FILE = "proxies.txt"  # Auto-scan for this file in input folder
PROXY_ROTATION_COUNT = 5  # Number of emails to process before rotating proxy
PROXY_TIMEOUT = 5
PROXY_RETRIES = 3

# SMTP settings
SMTP_TIMEOUT = 10
SMTP_PORT = 587

# Geolocation APIs
GEO_APIS = [
    "http://ip-api.com/json/",
    "https://ipapi.co/json/",
    "https://freegeoip.app/json/"
]

# Test email settings
TEST_EMAIL_RECIPIENT = None
TEST_EMAIL_SUBJECT = "Email Validation Test"
TEST_EMAIL_BODY = "This is a test email for validation purposes."

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "validator.log"