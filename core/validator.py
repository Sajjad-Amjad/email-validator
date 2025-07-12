import re
from typing import Dict, Tuple, Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from email_validator import validate_email, EmailNotValidError
except ImportError:
    print("email-validator not installed")
    
from config import MAX_WORKERS, BATCH_SIZE
from core.dns_checker import DNSChecker
from core.smtp_checker import SMTPChecker
from core.geo_locator import GeoLocator
from core.proxy_manager import ProxyManager
from utils.logger import setup_logger

logger = setup_logger(__name__)

class EmailValidator:
    def __init__(self, proxy_list: List[str] = None):
        logger.info("Initializing EmailValidator")
        self.dns_checker = DNSChecker()
        self.smtp_checker = SMTPChecker()
        self.geo_locator = GeoLocator()
        self.proxy_manager = ProxyManager(proxy_list)
        
        self.disposable_domains = {
            '10minutemail.com', 'tempmail.org', 'guerrillamail.com',
            'mailinator.com', 'yopmail.com', 'throwaway.email'
        }
        
    def validate_email_syntax(self, email: str) -> Dict:
        try:
            valid = validate_email(email)
            local_part = email.split('@')[0]
            domain_part = valid.domain if hasattr(valid, 'domain') else email.split('@')[1]
            
            return {
                'valid': True,
                'normalized': valid.email,
                'local': local_part,
                'domain': domain_part
            }
        except EmailNotValidError as e:
            return {
                'valid': False,
                'error': str(e),
                'normalized': None,
                'local': None,
                'domain': None
            }
    
    def is_disposable_email(self, domain: str) -> bool:
        return domain.lower() in self.disposable_domains
    
    def calculate_email_score(self, checks: Dict) -> str:
        """Calculate quality score based on multiple validation checks"""
        score = 0
        max_score = 100
        
        # Syntax check (20 points)
        if checks.get('syntax_valid', False):
            score += 20
        
        # Domain existence (25 points)
        if checks.get('domain_exists', False):
            score += 25
        
        # MX records (25 points) 
        if checks.get('has_mx_records', False):
            score += 25
        elif checks.get('has_a_records', False):
            score += 15  # Fallback to A records
        
        # SMTP connectivity (20 points)
        if checks.get('smtp_connectable', False):
            score += 20
        elif checks.get('smtp_attempted', False):
            score += 10  # Partial credit for attempt
        
        # Domain reputation (10 points)
        if checks.get('trusted_domain', False):
            score += 10
        elif checks.get('business_domain', False):
            score += 5
        
        # Determine quality based on score
        percentage = (score / max_score) * 100
        
        if percentage >= 80:
            return 'VALID'
        elif percentage >= 60:
            return 'PROBABLY_VALID'
        elif percentage >= 40:
            return 'PROBABLY_INVALID'
        else:
            return 'INVALID'
    
    def check_domain_reputation(self, domain: str) -> Dict:
        """Check domain reputation and type"""
        domain_lower = domain.lower()
        
        # Major email providers
        major_providers = {
            'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
            'live.com', 'aol.com', 'icloud.com', 'protonmail.com'
        }
        
        # Educational domains
        edu_patterns = ['.edu', '.ac.uk', '.ac.', '.sch.uk', '.edu.au']
        
        # Government domains  
        gov_patterns = ['.gov', '.gov.uk', '.gov.au']
        
        # Business indicators
        business_patterns = ['.com', '.co.uk', '.org', '.net', '.biz']
        
        reputation = {
            'trusted_domain': domain_lower in major_providers,
            'educational': any(pattern in domain_lower for pattern in edu_patterns),
            'government': any(pattern in domain_lower for pattern in gov_patterns),
            'business_domain': any(domain_lower.endswith(pattern) for pattern in business_patterns)
        }
        
        return reputation
    
    def validate_single_email(self, email: str, password: str = "") -> Dict:
        """Professional email validation with scoring system"""
        logger.info(f"Validating: {email}")
        
        result = {
            'email': email,
            'password': password,
            'status': 'INVALID',
            'country': 'Unknown',
            'details': []
        }
        
        checks = {}
        
        try:
            # Step 1: Syntax validation
            syntax_result = self.validate_email_syntax(email)
            checks['syntax_valid'] = syntax_result['valid']
            
            if not syntax_result['valid']:
                result['details'].append(f"Invalid syntax: {syntax_result.get('error', 'Unknown')}")
                result['status'] = self.calculate_email_score(checks)
                return result
            
            domain = syntax_result['domain']
            result['details'].append("Valid syntax")
            
            # Step 2: Disposable check
            if self.is_disposable_email(domain):
                result['details'].append("Disposable email domain")
                result['status'] = 'SKIPPED'
                return result
            
            # Step 3: Domain reputation check
            reputation = self.check_domain_reputation(domain)
            checks.update(reputation)
            
            # Step 4: DNS validation (more lenient)
            dns_result = self.dns_checker.validate_domain(domain)
            checks['domain_exists'] = True  # If we got here, domain exists
            checks['has_mx_records'] = dns_result['mx_info']['has_mx']
            checks['has_a_records'] = dns_result['a_info']['has_a']
            
            if dns_result['is_valid']:
                result['details'].append("Valid DNS records")
            else:
                result['details'].append("Limited DNS records")
            
            # Step 5: Country detection
            proxy = self.proxy_manager.get_working_proxy()
            geo_result = self.geo_locator.get_email_country(email, proxy)
            result['country'] = geo_result['country']
            
            # Step 6: SMTP validation (attempt but don't fail hard)
            checks['smtp_attempted'] = True
            
            if dns_result['mx_info']['has_mx']:
                primary_mx = dns_result['mx_info']['primary_mx']
                if primary_mx:
                    smtp_result = self.smtp_checker.check_smtp_connection(primary_mx)
                    checks['smtp_connectable'] = smtp_result['smtp_valid']
                    
                    if smtp_result['smtp_valid']:
                        result['details'].append("SMTP connection successful")
                        
                        # Deliverability test (lenient)
                        delivery_result = self.smtp_checker.verify_email_deliverability(email, primary_mx)
                        if delivery_result['deliverable']:
                            result['details'].append("Email deliverable")
                        else:
                            result['details'].append("SMTP accessible but delivery uncertain")
                    else:
                        result['details'].append("SMTP connection timeout")
                else:
                    result['details'].append("No primary MX server")
            else:
                # Check if domain has A records as fallback
                if checks['has_a_records']:
                    result['details'].append("Domain accessible via A records")
                else:
                    result['details'].append("No MX or A records")
            
            # Calculate final score
            result['status'] = self.calculate_email_score(checks)
            
            logger.info(f"Validation completed for {email}: {result['status']}")
            return result
            
        except Exception as e:
            result['details'].append(f"Validation error: {str(e)}")
            logger.error(f"Error validating {email}: {e}")
            return result
    
    def validate_batch(self, email_list: List[Tuple[str, str]]) -> List[Dict]:
        logger.info(f"Batch validation: {len(email_list)} emails")
        results = []
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_email = {
                executor.submit(self.validate_single_email, email, password): (email, password)
                for email, password in email_list
            }
            
            for future in as_completed(future_to_email):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    email, password = future_to_email[future]
                    logger.error(f"Batch error for {email}: {e}")
                    results.append({
                        'email': email,
                        'password': password,
                        'status': 'INVALID',
                        'country': 'Unknown',
                        'details': [f"Processing error: {str(e)}"]
                    })
        
        return results