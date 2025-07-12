# Email Validator & Country Detection Tool

A professional bulk email validation tool designed for processing large email lists with comprehensive validation features and advanced country detection capabilities. This tool validates email syntax, performs DNS/MX record checks, SMTP verification, provides geographic location data, and includes intelligent scoring algorithms for accurate results.

## Tech Stack

- **Python 3** - Core programming language
- **email-validator** - Advanced email syntax validation library
- **dnspython** - DNS and MX record lookup with fallback support
- **requests** - HTTP requests and proxy rotation support
- **pandas** - Data processing and CSV handling
- **concurrent.futures** - Multi-threading for high-performance bulk processing
- **smtplib** - SMTP connection testing and deliverability verification

## Project Directory Structure

```
email_validator/
├── main.py                    # Main entry point
├── config.py                  # Configuration settings
├── requirements.txt           # Python dependencies
├── README.md                  # Documentation
├── core/                      # Core validation modules
│   ├── __init__.py
│   ├── validator.py           # Advanced validation logic with scoring
│   ├── smtp_checker.py        # SMTP verification with fallback
│   ├── dns_checker.py         # DNS/MX validation with A record fallback
│   ├── geo_locator.py         # Country detection with multiple APIs
│   └── proxy_manager.py       # Advanced proxy rotation system
├── utils/                     # Utility modules
│   ├── __init__.py
│   ├── file_handler.py        # File I/O with per-file output support
│   ├── progress_tracker.py    # Progress tracking & resume capability
│   └── logger.py              # Comprehensive logging system
└── data/                      # Data directories
    ├── input/                 # Input email files and proxy configuration
    ├── output/                # Validation results (combined & per-file)
    └── progress/              # Progress tracking files
```

## How It Works (Technical Overview)

### 1. **Advanced Email Processing Pipeline**
```
Input File → Parse Email:Password → Syntax Validation → Domain Reputation Check → 
DNS Lookup → Country Detection → SMTP Verification → Quality Scoring → 
Result Classification → Multi-Format Output Generation
```

### 2. **Professional Validation Process**
- **Syntax Validation**: RFC-compliant email format checking with internationalization support
- **Domain Reputation**: Intelligent scoring for educational, government, and business domains
- **DNS Resolution**: MX record verification with A record fallback for maximum compatibility
- **SMTP Testing**: Multi-port connection testing with graceful timeout handling
- **Geolocation**: Multi-API country detection with fallback providers
- **Quality Scoring**: Professional scoring system (VALID, PROBABLY_VALID, PROBABLY_INVALID, INVALID)
- **Duplicate Detection**: Automatic deduplication with resume capability

### 3. **High-Performance Architecture**
- Processes emails in configurable batches (default: 20 emails per batch)
- Uses ThreadPoolExecutor with 10 concurrent workers for maximum speed
- Implements intelligent proxy rotation for large-scale processing
- Advanced error recovery and continuation from previous progress

### 4. **Robust Progress Tracking**
- Saves progress every batch to enable seamless resumption after interruptions
- Tracks processed emails to avoid re-validation and duplicate processing
- Maintains detailed logs for debugging, monitoring, and audit trails
- Automatic cleanup of temporary files upon completion

## Setup Instructions

### 1. Extract Source Code
```bash
# Extract the provided source code
unzip source_code.zip
cd email_validator
```

### 2. Create Virtual Environment
```bash
# Create virtual environment
python3 -m venv env

# Activate virtual environment
# On macOS/Linux:
source env/bin/activate
# On Windows:
env\Scripts\activate
```

### 3. Install Dependencies
```bash
# Install required packages
pip install -r requirements.txt
```

### 4. Run the Application
```bash
# Execute the main script
python3 main.py
```

## Input Configuration

### Email Files Location
Place your email list files in the `data/input/` directory.

### Email File Format
- **File Type**: `.txt` files only
- **Format**: `email:password` (colon-separated, one per line)
- **Example**:
```
john.doe@gmail.com:password123
jane.smith@yahoo.com:userpass456
admin@company.com:admin2024
support@domain.org:supportpass
```

### Proxy Configuration (Optional)
Create a `proxies.txt` file in the `data/input/` directory:
- **Format**: `username:password@ip:port` (one per line)
- **Example**:
```
proxyuser:proxypass@192.168.1.100:8080
username:password@185.199.229.156:7492
testuser:testpass@104.248.125.19:3128
```

### Multiple File Support
The tool automatically processes all `.txt` files (except proxies.txt) found in the input directory:
```
data/input/
├── proxies.txt           # Proxy configuration (optional)
├── list1.txt            # Email list 1
├── company_emails.txt   # Email list 2
├── customer_data.txt    # Email list 3
└── marketing_list.txt   # Email list 4
```

## Output Files Explanation

After processing, results are saved in the `data/output/` directory with both combined and per-file outputs:

### Combined Results:
- **valid.txt** - All valid emails from all input files
- **invalid.txt** - All invalid emails from all input files  
- **skipped.txt** - All skipped emails (disposable/duplicate)
- **summary.csv** - Comprehensive report with detailed validation results

### Per-File Results:
- **[filename]_valid.txt** - Valid emails from specific input file
- **[filename]_invalid.txt** - Invalid emails from specific input file
- **[filename]_skipped.txt** - Skipped emails from specific input file
- **[filename]_summary.csv** - Detailed results for specific input file

### Result Format Examples:

**TXT Files:**
```
email:password:country:status
sajjad.amjad@gmail.com:password123:United States:VALID
user@fakedomain.xyz:pass123:Unknown:INVALID
temp@10minutemail.com:temppass:Unknown:SKIPPED
```

**CSV Files:**
```csv
email,password,country,status,details
user@domain.com,pass123,Germany,VALID,"Valid syntax; Valid DNS records; SMTP connection successful"
bad@fake.xyz,pass456,Unknown,INVALID,"Valid syntax; No valid DNS records"
```


### Advanced Configuration Options

Edit `config.py` to customize:
- **BATCH_SIZE**: Number of emails processed per batch (default: 20)
- **MAX_WORKERS**: Number of concurrent threads (default: 10)
- **PROXY_ROTATION_COUNT**: Emails processed before proxy rotation (default: 10)
- **SMTP_TIMEOUT**: SMTP connection timeout in seconds (default: 3)
- **GEO_APIS**: Multiple geolocation API endpoints for redundancy

## Features Included

✅ **Email Syntax Validation** - RFC-compliant with international support  
✅ **Intelligent DNS/MX Validation** - MX records with A record fallback  
✅ **Professional SMTP Testing** - Multi-port with graceful timeout handling  
✅ **Accurate Country Detection** - Multi-API with fallback redundancy  
✅ **Smart Disposable Detection** - Advanced pattern recognition  
✅ **Automatic Duplicate Removal** - Resume-aware deduplication  
✅ **Advanced Proxy Support** - Automatic rotation and failure handling  
✅ **High-Performance Threading** - Optimized for large datasets  
✅ **Robust Progress Tracking** - Seamless interruption recovery  
✅ **Multiple Output Formats** - Combined and per-file results  
✅ **Professional Quality Scoring** - Industry-standard validation levels  
✅ **Comprehensive Logging** - Detailed audit trails and debugging  


## Troubleshooting

- **High invalid rates**: Normal for uncurated lists - focus on VALID and PROBABLY_VALID results
- **SMTP timeouts**: Expected behavior - most providers block validation attempts
- **Country detection failures**: Automatic fallback to multiple API providers
- **Proxy connection issues**: Script continues without proxies if all fail
- **Processing interruptions**: Automatic resume from last saved progress

The tool prioritizes **country detection** and **professional-grade validation** as core features, providing reliable geographic segmentation and email list hygiene for marketing campaigns.
