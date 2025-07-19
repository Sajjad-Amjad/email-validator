import re
from typing import Dict, Tuple, Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from email_validator import validate_email, EmailNotValidError
except ImportError:
    print("email-validator not installed")
    
from config import MAX_WORKERS, BATCH_SIZE, TEST_EMAIL_RECIPIENT
from core.dns_checker import DNSChecker
from core.smtp_checker import SMTPChecker
from core.geo_locator import GeoLocator
from core.proxy_manager import ProxyManager
from utils.logger import setup_logger

logger = setup_logger(__name__)

class EmailValidator:
    def __init__(self, proxy_list: List[str] = None):
        self.dns_checker = DNSChecker()
        self.smtp_checker = SMTPChecker()
        self.geo_locator = GeoLocator()
        self.proxy_manager = ProxyManager(proxy_list)
        
        # Extended disposable domains list
        self.disposable_domains = {
            '10minutemail.com', 'tempmail.org', 'guerrillamail.com',
            'mailinator.com', 'yopmail.com', 'throwaway.email',
            'temp-mail.org', 'emailondeck.com', 'sharklasers.com',
            'getnada.com', 'maildrop.cc', 'guerrillamail.info',
            'guerrillamail.biz', 'guerrillamail.de', 'guerrillamail.net',
            'guerrillamail.org', 'guerrillamailblock.com', 'inboxalias.com',
            'jetable.org', 'mailtemp.info', 'mytemp.email',
            'spambox.us', 'tempmailaddress.com', 'mailnesia.com',
            'mohmal.com', 'burnermail.io', 'dropmail.me'
        }
        
        logger.info("EmailValidator initialized successfully")
        
    def validate_email_syntax(self, email: str) -> Dict:
        """Validate email syntax according to IETF/RFC standards"""
        logger.debug(f"Validating syntax for: {email}")
        try:
            # Use email_validator for RFC compliance
            valid = validate_email(email)
            local_part = email.split('@')[0]
            domain_part = valid.domain if hasattr(valid, 'domain') else email.split('@')[1]
            
            result = {
                'valid': True,
                'normalized': valid.email,
                'local': local_part,
                'domain': domain_part
            }
            logger.debug(f"Syntax validation passed for: {email}")
            return result
        except EmailNotValidError as e:
            result = {
                'valid': False,
                'error': str(e),
                'normalized': None,
                'local': None,
                'domain': None
            }
            logger.debug(f"Syntax validation failed for {email}: {e}")
            return result
    
    def is_disposable_email(self, domain: str) -> bool:
        """Check if domain is disposable/temporary email"""
        is_disposable = domain.lower() in self.disposable_domains
        logger.debug(f"Disposable check for {domain}: {is_disposable}")
        return is_disposable
    
    def detect_misspelled_domain(self, domain: str) -> Dict:
        """Detect common domain misspellings"""
        common_domains = {
            'gmail.com': ['gmai.com', 'gmail.co', 'gmial.com', 'gmaill.com'],
            'yahoo.com': ['yaho.com', 'yahoo.co', 'yhoo.com', 'yahooo.com'],
            'hotmail.com': ['hotmai.com', 'hotmial.com', 'homail.com'],
            'outlook.com': ['outlok.com', 'outloo.com', 'outlookk.com'],
            'aol.com': ['aol.co', 'ao.com', 'aoll.com'],
        }
        
        domain_lower = domain.lower()
        
        for correct_domain, misspellings in common_domains.items():
            if domain_lower in misspellings:
                return {
                    'is_misspelled': True,
                    'suggested_domain': correct_domain,
                    'confidence': 0.9
                }
        
        # Check for similar domains using basic string similarity
        for correct_domain in common_domains.keys():
            if self._similarity_score(domain_lower, correct_domain) > 0.8:
                return {
                    'is_misspelled': True,
                    'suggested_domain': correct_domain,
                    'confidence': 0.7
                }
        
        return {'is_misspelled': False, 'suggested_domain': None, 'confidence': 0.0}
    
    def _similarity_score(self, s1: str, s2: str) -> float:
        """Simple similarity score between two strings"""
        if len(s1) == 0 or len(s2) == 0:
            return 0.0
        
        # Simple character-based similarity
        common_chars = set(s1) & set(s2)
        all_chars = set(s1) | set(s2)
        
        return len(common_chars) / len(all_chars) if all_chars else 0.0
    
    def validate_single_email(self, email_or_domain: str, password: str = "") -> Dict:
        """
        Validates email or domain.
        For emails: full validation + optional SMTP auth.
        For domains: DNS/MX/country only.
        """
        logger.info(f"Validating: {email_or_domain}")

        result = {
            'email': email_or_domain,
            'password': password,
            'status': 'INVALID',
            'country': 'Unknown',
            'details': [],
            'validation_score': 0,
            'spam_trap_risk': 'UNKNOWN',
            'smtp_auth_result': 'NOT_TESTED'
        }

        try:
            # Check if it's a domain (no @ symbol)
            if '@' not in email_or_domain:
                # Domain validation
                domain = email_or_domain
                dns_result = self.dns_checker.validate_domain(domain)
                
                if not dns_result['is_valid']:
                    result['details'].append("Domain does not exist or DNS lookup failed")
                    logger.info(f"Validation completed for {domain}: INVALID (domain/DNS)")
                    return result
                    
                if not dns_result['mx_info']['has_mx']:
                    result['details'].append("No MX record for domain")
                    logger.info(f"Validation completed for {domain}: INVALID (no MX)")
                    return result
                
                # Country detection for domain
                proxy = self.proxy_manager.get_working_proxy()
                geo_result = self.geo_locator.get_email_country(f"info@{domain}", proxy)
                result['country'] = geo_result.get('country', 'Unknown')
                
                result['status'] = 'VALID'
                result['validation_score'] = 70
                result['details'].append("Domain is valid (DNS/MX/country checked)")
                logger.info(f"Validation completed for {domain}: VALID (domain only)")
                return result

            # Email validation
            syntax_result = self.validate_email_syntax(email_or_domain)
            if not syntax_result['valid']:
                result['details'].append(f"Invalid syntax: {syntax_result.get('error', 'Unknown')}")
                logger.info(f"Validation completed for {email_or_domain}: INVALID (syntax)")
                return result

            domain = syntax_result['domain']
            result['validation_score'] += 20

            # Disposable check
            if self.is_disposable_email(domain):
                result['details'].append("Disposable email domain")
                result['status'] = "SKIPPED"
                logger.info(f"Validation completed for {email_or_domain}: SKIPPED (disposable)")
                return result

            # DNS/MX check
            dns_result = self.dns_checker.validate_domain(domain)
            if not dns_result['is_valid']:
                result['details'].append("Domain does not exist or DNS lookup failed")
                logger.info(f"Validation completed for {email_or_domain}: INVALID (domain/DNS)")
                return result

            result['validation_score'] += 20

            if not dns_result['mx_info']['has_mx']:
                result['details'].append("No MX record for domain")
                logger.info(f"Validation completed for {email_or_domain}: INVALID (no MX)")
                return result

            result['validation_score'] += 20

            primary_mx = dns_result['mx_info']['primary_mx']
            if not primary_mx:
                result['details'].append("No primary MX server found")
                logger.info(f"Validation completed for {email_or_domain}: INVALID (no primary MX)")
                return result

            # SMTP connection
            smtp_result = self.smtp_checker.check_smtp_connection(primary_mx)
            if not smtp_result['smtp_valid']:
                result['details'].append("SMTP server not reachable or port closed")
                logger.info(f"Validation completed for {email_or_domain}: INVALID (SMTP conn)")
                return result

            result['validation_score'] += 20

            # Mailbox existence check
            delivery_result = self.smtp_checker.verify_email_deliverability(email_or_domain, primary_mx)
            if not delivery_result['deliverable']:
                msg = delivery_result.get('smtp_message', 'Mailbox rejected')
                result['details'].append(f"Mailbox rejected: {msg}")
                logger.info(f"Validation completed for {email_or_domain}: INVALID (RCPT TO fail)")
                return result

            result['validation_score'] += 20

            # Country detection
            proxy = self.proxy_manager.get_working_proxy()
            geo_result = self.geo_locator.get_email_country(email_or_domain, proxy)
            result['country'] = geo_result.get('country', 'Unknown')

            # SMTP Authentication test (if password provided)
            if password and password.strip():
                try:
                    auth_result = self.smtp_checker.test_smtp_authentication(email_or_domain, password)
                    if auth_result.get('authenticated', False):
                        result['smtp_auth_result'] = 'SUCCESS'
                        result['details'].append("SMTP authentication successful")
                        result['validation_score'] += 20
                    else:
                        result['smtp_auth_result'] = 'FAILED'
                        result['details'].append(f"SMTP authentication failed: {auth_result.get('reason', 'Unknown')}")
                except Exception as e:
                    result['smtp_auth_result'] = 'ERROR'
                    result['details'].append(f"SMTP auth error: {str(e)}")

            # Calculate spam trap risk
            result['spam_trap_risk'] = self.assess_spam_trap_risk(
                email_or_domain, domain, result['validation_score']
            )

            # All checks passed
            result['details'].append("All checks passed, mailbox exists")
            result['status'] = "VALID"
            logger.info(f"Validation completed for {email_or_domain}: VALID")
            return result

        except Exception as e:
            result['details'].append(f"Validation error: {str(e)}")
            logger.error(f"Error validating {email_or_domain}: {e}")
            result['status'] = "INVALID"
            return result
    
    def assess_spam_trap_risk(self, email: str, domain: str, validation_score: int) -> str:
        """Assess spam trap risk based on various factors"""
        risk_score = 0
        
        # Check for suspicious patterns
        local_part = email.split('@')[0] if '@' in email else ''
        
        # Common spam trap patterns
        spam_patterns = [
            'test', 'admin', 'info', 'support', 'sales', 'marketing',
            'webmaster', 'postmaster', 'noreply', 'no-reply',
            'abuse', 'spam', 'trap', 'honeypot'
        ]
        
        if local_part.lower() in spam_patterns:
            risk_score += 30
        
        # Check for random character patterns
        if len(local_part) > 15 and any(char.isdigit() for char in local_part):
            random_chars = sum(1 for char in local_part if char.isdigit())
            if random_chars > len(local_part) * 0.4:
                risk_score += 20
        
        # Domain reputation check
        suspicious_domains = [
            'example.com', 'test.com', 'invalid.com',
            'fake.com', 'dummy.com', 'sample.com'
        ]
        
        if domain.lower() in suspicious_domains:
            risk_score += 40
        
        # Validation score factor
        if validation_score < 30:
            risk_score += 20
        elif validation_score < 50:
            risk_score += 10
        
        # Determine risk level
        if risk_score >= 50:
            return 'HIGH'
        elif risk_score >= 25:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def validate_batch(self, email_list: List[Tuple[str, str]]) -> List[Dict]:
        """Validate batch of emails with multi-threading"""
        logger.info(f"Starting batch validation for {len(email_list)} emails")
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
                    logger.debug(f"Batch item completed: {result['email']} -> {result['status']} (SMTP: {result.get('smtp_auth_result', 'N/A')})")
                except Exception as e:
                    email, password = future_to_email[future]
                    logger.error(f"Batch error for {email}: {e}")
                    results.append({
                        'email': email,
                        'password': password,
                        'status': 'INVALID',
                        'country': 'Unknown',
                        'details': [f"Processing error: {str(e)}"],
                        'validation_score': 0,
                        'spam_trap_risk': 'HIGH',
                        'smtp_auth_result': 'ERROR'
                    })
        
        logger.info(f"Batch validation completed: {len(results)} results")
        return results