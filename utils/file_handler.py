import os
import csv
import re
from typing import List, Tuple, Dict, Optional
from datetime import datetime

from config import INPUT_FOLDER, OUTPUT_FOLDER, PROXY_FILE
from utils.logger import setup_logger

logger = setup_logger(__name__)

class FileHandler:
    def __init__(self):
        self.input_folder = INPUT_FOLDER
        self.output_folder = OUTPUT_FOLDER
        self.proxy_file = PROXY_FILE
        self.per_file_results = {}
        
        # Create necessary directories
        self.create_directories()
        logger.info("FileHandler initialized")
    
    def create_directories(self):
        """Create input and output directories if they don't exist"""
        logger.info(f"Creating directories: {self.input_folder}, {self.output_folder}")
        
        os.makedirs(self.input_folder, exist_ok=True)
        os.makedirs(self.output_folder, exist_ok=True)
        
        logger.info("Directories created successfully")
    
    def read_proxy_file(self) -> List[str]:
        """Read proxy list from proxies.txt file"""
        proxy_file_path = os.path.join(self.input_folder, 'proxies.txt')
        
        if not os.path.exists(proxy_file_path):
            logger.info(f"No proxy file found: {proxy_file_path}")
            return []
        
        try:
            with open(proxy_file_path, 'r', encoding='utf-8') as f:
                proxies = []
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Validate proxy format: username:password@ip:port
                        if self._validate_proxy_format(line):
                            proxies.append(line)
                        else:
                            logger.warning(f"Invalid proxy format at line {line_num}: {line}")
                
                logger.info(f"Loaded {len(proxies)} valid proxies from {proxy_file_path}")
                return proxies
                
        except Exception as e:
            logger.error(f"Error reading proxy file {proxy_file_path}: {e}")
            return []
    
    def _validate_proxy_format(self, proxy: str) -> bool:
        """
        Validate proxy format: username:password@host:port
        (host can be domain or IP)
        """
        pattern = r'^[^:]+:[^@]+@[^:]+:\d+$'
        return bool(re.match(pattern, proxy))

    
    def read_input_files(self) -> List[Tuple[str, str, str]]:
        """Read all .txt files from input folder, supporting email:password, email, and domain"""
        logger.info(f"Reading files from: {self.input_folder}")
        data = []

        txt_files = [f for f in os.listdir(self.input_folder) if f.endswith('.txt') and f != 'proxies.txt']
        if not txt_files:
            logger.warning("No .txt files found in input folder")
            return data

        for filename in txt_files:
            filepath = os.path.join(self.input_folder, filename)
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    # Email:Password
                    if ':' in line:
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            email_or_domain = parts[0].strip()
                            password = parts[1].strip()
                            data.append((email_or_domain, password, filename))
                        else:
                            logger.warning(f"Invalid line format at {filename}:{line_num}: {line}")
                    else:
                        # Could be email or domain
                        if '@' in line and '.' in line:
                            # Email without password
                            data.append((line, '', filename))
                        elif '.' in line:
                            # Domain only
                            data.append((line, '', filename))
                        else:
                            logger.warning(f"Unknown line format at {filename}:{line_num}: {line}")
            if filename not in self.per_file_results:
                self.per_file_results[filename] = []

        logger.info(f"Total records loaded: {len(data)} from {len(txt_files)} files")
        return data

    
    def add_result_to_file(self, result: Dict, source_file: str):
        """Add validation result to per-file tracking"""
        if source_file not in self.per_file_results:
            self.per_file_results[source_file] = []
        
        self.per_file_results[source_file].append(result)
    
    def write_results(self, all_results: List[Dict]):
        """Write results to multiple output formats as per client requirements"""
        logger.info(f"Writing {len(all_results)} results to output files")
        
        # Write combined results
        self._write_combined_results(all_results)
        
        # Write per-file results
        self._write_per_file_results()
        
        # Write categorized results (valid.txt, invalid.txt, skipped.txt)
        self._write_categorized_results(all_results)
        
        # Write SMTP authentication results separately
        self._write_smtp_auth_results(all_results)

        self._write_geo_country_output(all_results)

        
        logger.info("All output files written successfully")
    
    def _write_combined_results(self, results: List[Dict]):
        """Write combined results to CSV and summary files"""
        # Combined CSV file
        csv_file = os.path.join(self.output_folder, "all_results.csv")
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                'email', 'password', 'status', 'country', 'validation_score',
                'spam_trap_risk', 'smtp_auth_result', 'details', 'mx_records', 'smtp_response'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in results:
                # Format MX records properly
                mx_records = result.get('mx_records', [])
                mx_records_str = ''
                if mx_records:
                    if isinstance(mx_records[0], dict):
                        mx_records_str = ', '.join([f"{mx['host']}:{mx['priority']}" for mx in mx_records])
                    else:
                        mx_records_str = ', '.join(mx_records)
                
                writer.writerow({
                    'email': result['email'],
                    'password': result['password'],
                    'status': result['status'],
                    'country': result.get('country', 'Unknown'),
                    'validation_score': result.get('validation_score', 0),
                    'spam_trap_risk': result.get('spam_trap_risk', 'UNKNOWN'),
                    'smtp_auth_result': result.get('smtp_auth_result', 'NOT_TESTED'),
                    'details': ' | '.join(result.get('details', [])),
                    'mx_records': mx_records_str,
                    'smtp_response': result.get('smtp_response', '')
                })
        
        # Summary CSV file
        summary_file = os.path.join(self.output_folder, "summary.csv")
        
        with open(summary_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['email', 'status', 'country', 'validation_score', 'smtp_auth_result']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in results:
                writer.writerow({
                    'email': result['email'],
                    'status': result['status'],
                    'country': result.get('country', 'Unknown'),
                    'validation_score': result.get('validation_score', 0),
                    'smtp_auth_result': result.get('smtp_auth_result', 'NOT_TESTED')
                })
        
        # Count statistics
        valid_count = sum(1 for r in results if r['status'] == 'VALID')
        invalid_count = sum(1 for r in results if r['status'] == 'INVALID')
        skipped_count = sum(1 for r in results if r['status'] == 'SKIPPED')
        
        # SMTP Auth statistics
        smtp_success = sum(1 for r in results if r.get('smtp_auth_result') == 'SUCCESS')
        smtp_failed = sum(1 for r in results if r.get('smtp_auth_result') == 'FAILED')
        smtp_not_tested = sum(1 for r in results if r.get('smtp_auth_result') == 'NOT_TESTED')
        
        logger.info(f"Combined results - Valid: {valid_count}, Invalid: {invalid_count}, Skipped: {skipped_count}")
        logger.info(f"SMTP Auth results - Success: {smtp_success}, Failed: {smtp_failed}, Not tested: {smtp_not_tested}")
    
    def _write_per_file_results(self):
        """Write results for each input file separately"""
        logger.info("Writing per-file results")
        
        for filename, results in self.per_file_results.items():
            if not results:
                continue
            
            # Remove .txt extension and add results suffix
            base_name = filename.replace('.txt', '')
            
            # CSV file for this input file
            csv_file = os.path.join(self.output_folder, f"{base_name}_results.csv")
            
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                fieldnames = [
                    'email', 'password', 'status', 'country', 'validation_score',
                    'spam_trap_risk', 'smtp_auth_result', 'details'
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for result in results:
                    writer.writerow({
                        'email': result['email'],
                        'password': result['password'],
                        'status': result['status'],
                        'country': result.get('country', 'Unknown'),
                        'validation_score': result.get('validation_score', 0),
                        'spam_trap_risk': result.get('spam_trap_risk', 'UNKNOWN'),
                        'smtp_auth_result': result.get('smtp_auth_result', 'NOT_TESTED'),
                        'details': ' | '.join(result.get('details', []))
                    })
            
            # Count statistics for this file
            valid_count = sum(1 for r in results if r['status'] == 'VALID')
            invalid_count = sum(1 for r in results if r['status'] == 'INVALID')
            skipped_count = sum(1 for r in results if r['status'] == 'SKIPPED')
            
            logger.info(f"File {filename} results - Valid: {valid_count}, Invalid: {invalid_count}, Skipped: {skipped_count}")
    
    def _write_categorized_results(self, results: List[Dict]):
        """Write categorized results to separate txt files (client requirement)"""
        logger.info("Writing categorized results")
        
        # Categorize results
        valid_results = [r for r in results if r['status'] == 'VALID']
        invalid_results = [r for r in results if r['status'] == 'INVALID']
        skipped_results = [r for r in results if r['status'] == 'SKIPPED']
        
        # Write valid.txt
        if valid_results:
            valid_file = os.path.join(self.output_folder, "valid.txt")
            with open(valid_file, 'w', encoding='utf-8') as f:
                for result in valid_results:
                    country = result.get('country', 'Unknown')
                    score = result.get('validation_score', 0)
                    smtp_auth = result.get('smtp_auth_result', 'NOT_TESTED')
                    f.write(f"{result['email']}:{result['password']} | {country} | Score: {score} | SMTP Auth: {smtp_auth}\n")
        
        # Write invalid.txt
        if invalid_results:
            invalid_file = os.path.join(self.output_folder, "invalid.txt")
            with open(invalid_file, 'w', encoding='utf-8') as f:
                for result in invalid_results:
                    country = result.get('country', 'Unknown')
                    reason = result.get('details', ['Unknown reason'])[0] if result.get('details') else 'Unknown reason'
                    f.write(f"{result['email']}:{result['password']} | {country} | {reason}\n")
        
        # Write skipped.txt
        if skipped_results:
            skipped_file = os.path.join(self.output_folder, "skipped.txt")
            with open(skipped_file, 'w', encoding='utf-8') as f:
                for result in skipped_results:
                    country = result.get('country', 'Unknown')
                    reason = result.get('details', ['Unknown reason'])[0] if result.get('details') else 'Unknown reason'
                    f.write(f"{result['email']}:{result['password']} | {country} | {reason}\n")
        
        logger.info(f"Categorized files written - Valid: {len(valid_results)}, Invalid: {len(invalid_results)}, Skipped: {len(skipped_results)}")
    
    def _write_smtp_auth_results(self, results: List[Dict]):
        """Write SMTP authentication results to separate file"""
        logger.info("Writing SMTP authentication results")
        
        smtp_file = os.path.join(self.output_folder, "smtp_auth_results.txt")
        
        # Categorize SMTP results
        smtp_success = [r for r in results if r.get('smtp_auth_result') == 'SUCCESS']
        smtp_failed = [r for r in results if r.get('smtp_auth_result') == 'FAILED']
        smtp_not_tested = [r for r in results if r.get('smtp_auth_result') == 'NOT_TESTED']
        smtp_error = [r for r in results if r.get('smtp_auth_result') == 'ERROR']
        
        with open(smtp_file, 'w', encoding='utf-8') as f:
            
            # Write successful SMTP authentications
            if smtp_success:
                for result in smtp_success:
                    country = result.get('country', 'Unknown')
                    f.write(f"{result['email']}:{result['password']} | {country} | ✅ Can send emails\n")
                f.write("\n")
            
            # Write failed SMTP authentications
            if smtp_failed:
                for result in smtp_failed:
                    country = result.get('country', 'Unknown')
                    # Find SMTP-related details
                    smtp_details = [d for d in result.get('details', []) if 'SMTP authentication' in d]
                    reason = smtp_details[0] if smtp_details else 'Authentication failed'
                    f.write(f"{result['email']}:{result['password']} | {country} | {reason}\n")
                f.write("\n")
            
            # Write not tested
            if smtp_not_tested:
                for result in smtp_not_tested:
                    country = result.get('country', 'Unknown')
                    status = result.get('status', 'UNKNOWN')
                    f.write(f"{result['email']}:{result['password']} | {country} | Status: {status}\n")
                f.write("\n")
        
        logger.info(f"SMTP auth results written - Success: {len(smtp_success)}, Failed: {len(smtp_failed)}, Not tested: {len(smtp_not_tested)}, Error: {len(smtp_error)}")
    
    def remove_duplicates(self, email_data: List[Tuple[str, str, str]]) -> List[Tuple[str, str, str]]:
        """Remove duplicate emails from the input data"""
        seen_emails = set()
        unique_data = []
        duplicates_count = 0
        
        for email, password, source_file in email_data:
            if email.lower() not in seen_emails:
                seen_emails.add(email.lower())
                unique_data.append((email, password, source_file))
            else:
                duplicates_count += 1
        
        if duplicates_count > 0:
            logger.info(f"Removed {duplicates_count} duplicate emails")
        
        return unique_data
    
    def get_file_stats(self) -> Dict:
        """Get statistics about processed files"""
        stats = {
            'total_files': len(self.per_file_results),
            'per_file_stats': {}
        }
        
        for filename, results in self.per_file_results.items():
            valid_count = sum(1 for r in results if r['status'] == 'VALID')
            invalid_count = sum(1 for r in results if r['status'] == 'INVALID')
            skipped_count = sum(1 for r in results if r['status'] == 'SKIPPED')
            
            # SMTP auth stats
            smtp_success = sum(1 for r in results if r.get('smtp_auth_result') == 'SUCCESS')
            smtp_failed = sum(1 for r in results if r.get('smtp_auth_result') == 'FAILED')
            
            stats['per_file_stats'][filename] = {
                'total': len(results),
                'valid': valid_count,
                'invalid': invalid_count,
                'skipped': skipped_count,
                'smtp_auth_success': smtp_success,
                'smtp_auth_failed': smtp_failed
            }
        
        return stats
    
    def _write_geo_country_output(self, all_results: List[Dict]):
        """
        Write each domain/email to country-based output files, e.g. output/countries/UK.txt
        Only 'VALID' status entries are considered.
        """
        country_folder = os.path.join(self.output_folder, "countries")
        os.makedirs(country_folder, exist_ok=True)

        country_map = {}
        for result in all_results:
            if result['status'] == 'VALID':
                country = result.get('country', 'Unknown')
                if country not in country_map:
                    country_map[country] = []
                # Output just the domain for domains, or email for emails
                country_map[country].append(result['email'])

        for country, items in country_map.items():
            safe_country = country.replace(" ", "_").replace("/", "-")
            out_path = os.path.join(country_folder, f"{safe_country}.txt")
            with open(out_path, 'w', encoding='utf-8') as f:
                for item in items:
                    f.write(item + '\n')
        logger.info(f"Wrote geo/country output to {country_folder}")
