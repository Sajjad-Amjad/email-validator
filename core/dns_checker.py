import dns.resolver
import dns.exception
import socket
from typing import Dict, Optional
from utils.logger import setup_logger

logger = setup_logger(__name__)

class DNSChecker:
    def __init__(self):
        self.resolver = dns.resolver.Resolver()
        self.resolver.timeout = 3
        self.resolver.lifetime = 3
        
    def check_mx_record(self, domain: str) -> Dict:
        logger.debug(f"Checking MX records for: {domain}")
        
        try:
            mx_records = self.resolver.resolve(domain, 'MX')
            
            if not mx_records:
                return {'has_mx': False, 'mx_servers': [], 'primary_mx': None}
            
            mx_servers = []
            for mx in mx_records:
                mx_str = str(mx).split()[-1].rstrip('.')
                mx_servers.append(mx_str)
            
            primary_mx = mx_servers[0] if mx_servers else None
            
            return {
                'has_mx': True,
                'mx_servers': mx_servers,
                'primary_mx': primary_mx
            }
            
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
            return {'has_mx': False, 'mx_servers': [], 'primary_mx': None}
        except Exception as e:
            logger.debug(f"DNS error for {domain}: {e}")
            return {'has_mx': False, 'mx_servers': [], 'primary_mx': None}
    
    def check_a_record(self, domain: str) -> Dict:
        try:
            a_records = self.resolver.resolve(domain, 'A')
            ips = [str(ip) for ip in a_records]
            return {'has_a': True, 'ips': ips}
        except:
            return {'has_a': False, 'ips': []}
    
    def validate_domain(self, domain: str) -> Dict:
        """Balanced domain validation - MX preferred but A records acceptable"""
        logger.info(f"Validating domain: {domain}")
        
        mx_result = self.check_mx_record(domain)
        a_result = self.check_a_record(domain)
        
        # Accept domain if it has MX records OR A records
        is_valid = mx_result['has_mx'] or a_result['has_a']
        
        if mx_result['has_mx']:
            details = 'Valid domain with MX records'
        elif a_result['has_a']:
            details = 'Valid domain with A records (MX fallback)'
        else:
            details = 'Domain not found'
        
        return {
            'domain': domain,
            'is_valid': is_valid,
            'mx_info': mx_result,
            'a_info': a_result,
            'details': details
        }