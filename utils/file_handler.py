import os
import csv
import json
from typing import List, Dict, Tuple
from config import INPUT_FOLDER, OUTPUT_FOLDER, DELIMITER, PROXY_FILE
from utils.logger import setup_logger

logger = setup_logger(__name__)

class FileHandler:
    def __init__(self):
        self.ensure_directories()
        self.file_results = {}  # Track results per file
        
    def ensure_directories(self):
        logger.info(f"Creating directories: {INPUT_FOLDER}, {OUTPUT_FOLDER}")
        os.makedirs(INPUT_FOLDER, exist_ok=True)
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)
        logger.info("Directories created successfully")
        
    def read_input_files(self) -> List[Tuple[str, str, str]]:  # Added filename tracking
        logger.info(f"Scanning input folder for email files: {INPUT_FOLDER}")
        all_data = []
        
        for filename in os.listdir(INPUT_FOLDER):
            # Skip proxy file - handle it separately
            if filename == PROXY_FILE:
                logger.info(f"Skipping proxy file: {filename}")
                continue
                
            if filename.endswith('.txt'):
                filepath = os.path.join(INPUT_FOLDER, filename)
                logger.info(f"Processing email file: {filename}")
                
                # Initialize file tracking
                base_filename = filename.replace('.txt', '')
                self.file_results[base_filename] = []
                
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        if not line or line.startswith('#'):
                            logger.debug(f"Skipping empty/comment line {line_num}")
                            continue
                            
                        try:
                            if DELIMITER in line:
                                email, password = line.split(DELIMITER, 1)
                                email = email.strip()
                                password = password.strip()
                                all_data.append((email, password, base_filename))
                                logger.debug(f"Parsed: {email} from {filename}")
                            else:
                                email = line.strip()
                                all_data.append((email, "", base_filename))
                                logger.debug(f"Email only: {email} from {filename}")
                        except Exception as e:
                            logger.warning(f"Malformed line {line_num} in {filename}: {line} - Error: {e}")
                            
        logger.info(f"Total email records loaded: {len(all_data)} from {len(self.file_results)} files")
        return all_data
    
    def read_proxy_file(self) -> List[str]:
        """Read proxies from proxies.txt file if it exists"""
        proxy_filepath = os.path.join(INPUT_FOLDER, PROXY_FILE)
        proxies = []
        
        if os.path.exists(proxy_filepath):
            logger.info(f"Found proxy file: {PROXY_FILE}")
            with open(proxy_filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    # Validate proxy format: username:password@ip:port
                    if '@' in line and ':' in line:
                        proxies.append(line)
                        logger.debug(f"Loaded proxy from line {line_num}")
                    else:
                        logger.warning(f"Invalid proxy format on line {line_num}: {line}")
            
            logger.info(f"Loaded {len(proxies)} proxies from {PROXY_FILE}")
        else:
            logger.info(f"No proxy file found: {PROXY_FILE}")
        
        return proxies
    
    def add_result_to_file(self, result: Dict, source_filename: str):
        """Add result to specific file tracking"""
        if source_filename not in self.file_results:
            self.file_results[source_filename] = []
        self.file_results[source_filename].append(result)
    
    def write_results(self, results: List[Dict]):
        """Write combined results and per-file results"""
        if not results:
            logger.warning("No results to write")
            return
            
        logger.info(f"Writing {len(results)} results to output files")
        
        # Write combined results (existing functionality)
        self._write_combined_results(results)
        
        # Write per-file results (new functionality)
        self._write_per_file_results()
        
        logger.info("All output files written successfully")
    
    def _write_combined_results(self, results: List[Dict]):
        """Write combined results as before"""
        # Group results by status
        valid = [r for r in results if r['status'] == 'VALID']
        invalid = [r for r in results if r['status'] == 'INVALID']
        skipped = [r for r in results if r['status'] == 'SKIPPED']
        
        logger.info(f"Combined results - Valid: {len(valid)}, Invalid: {len(invalid)}, Skipped: {len(skipped)}")
        
        # Write combined TXT files
        self._write_txt_file("valid.txt", valid)
        self._write_txt_file("invalid.txt", invalid)
        self._write_txt_file("skipped.txt", skipped)
        
        # Write combined CSV summary
        self._write_csv_file("summary.csv", results)
    
    def _write_per_file_results(self):
        """Write separate results for each input file"""
        logger.info("Writing per-file results")
        
        for filename, file_results in self.file_results.items():
            if not file_results:
                continue
                
            logger.info(f"Writing results for file: {filename} ({len(file_results)} results)")
            
            # Group by status for this file
            file_valid = [r for r in file_results if r['status'] == 'VALID']
            file_invalid = [r for r in file_results if r['status'] == 'INVALID']
            file_skipped = [r for r in file_results if r['status'] == 'SKIPPED']
            
            # Write per-file TXT files
            self._write_txt_file(f"{filename}_valid.txt", file_valid)
            self._write_txt_file(f"{filename}_invalid.txt", file_invalid)
            self._write_txt_file(f"{filename}_skipped.txt", file_skipped)
            
            # Write per-file CSV summary
            self._write_csv_file(f"{filename}_summary.csv", file_results)
            
            logger.info(f"File {filename} results - Valid: {len(file_valid)}, Invalid: {len(file_invalid)}, Skipped: {len(file_skipped)}")
    
    def _write_txt_file(self, filename: str, data: List[Dict]):
        if not data:
            logger.debug(f"No data to write for {filename}")
            return
            
        filepath = os.path.join(OUTPUT_FOLDER, filename)
        logger.debug(f"Writing {len(data)} records to {filename}")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            for item in data:
                # Use colon delimiter as per client's format
                line = f"{item['email']}{DELIMITER}{item['password']}{DELIMITER}{item['country']}{DELIMITER}{item['status']}"
                f.write(line + '\n')
        
        logger.debug(f"Successfully wrote {filename}")
    
    def _write_csv_file(self, filename: str, data: List[Dict]):
        if not data:
            logger.debug(f"No data to write for {filename}")
            return
            
        filepath = os.path.join(OUTPUT_FOLDER, filename)
        logger.debug(f"Writing {len(data)} records to {filename}")
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['email', 'password', 'country', 'status', 'details']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for item in data:
                row = item.copy()
                if isinstance(row['details'], list):
                    row['details'] = "; ".join(row['details'])
                writer.writerow(row)
        
        logger.debug(f"Successfully wrote {filename}")