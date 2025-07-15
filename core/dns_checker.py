import dns.resolver
import socket
from typing import Dict, List, Optional
from config import DNS_TIMEOUT
from utils.logger import setup_logger

logger = setup_logger(__name__)

class DNSChecker:
    def __init__(self):
        self.timeout = DNS_TIMEOUT
        # Configure DNS resolver
        self.resolver = dns.resolver.Resolver()
        self.resolver.timeout = self.timeout
        self.resolver.lifetime = self.timeout
        logger.info("DNS checker initialized")
    
    def validate_domain(self, domain: str) -> Dict:
        """Comprehensive domain validation with DNS checks"""
        logger.info(f"Validating domain: {domain}")
        
        result = {
            'domain': domain,
            'is_valid': False,
            'has_a_record': False,
            'has_mx_record': False,
            'ip_address': None,
            'mx_info': {
                'has_mx': False,
                'mx_records': [],
                'primary_mx': None
            },
            'dns_errors': []
        }
        
        try:
            # Step 1: Check A record (IP address)
            try:
                logger.debug(f"Checking A record for {domain}")
                a_records = self.resolver.resolve(domain, 'A')
                if a_records:
                    result['has_a_record'] = True
                    result['ip_address'] = str(a_records[0])
                    logger.debug(f"A record found for {domain}: {result['ip_address']}")
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
                logger.debug(f"No A record found for {domain}")
                result['dns_errors'].append("No A record found")
            except Exception as e:
                logger.debug(f"A record lookup failed for {domain}: {e}")
                result['dns_errors'].append(f"A record lookup error: {str(e)}")
            
            # Step 2: Check MX record (mail server)
            try:
                logger.debug(f"Checking MX record for {domain}")
                mx_records = self.resolver.resolve(domain, 'MX')
                if mx_records:
                    result['has_mx_record'] = True
                    result['mx_info']['has_mx'] = True
                    
                    # Sort MX records by priority (lower priority = higher precedence)
                    mx_list = []
                    for mx in mx_records:
                        mx_host = str(mx.exchange).rstrip('.')
                        mx_list.append({
                            'host': mx_host,
                            'priority': mx.preference
                        })
                    
                    # Sort by priority
                    mx_list.sort(key=lambda x: x['priority'])
                    result['mx_info']['mx_records'] = mx_list
                    
                    # Set primary MX server
                    if mx_list:
                        result['mx_info']['primary_mx'] = mx_list[0]['host']
                        logger.debug(f"Primary MX server for {domain}: {result['mx_info']['primary_mx']}")
                    
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
                logger.debug(f"No MX record found for {domain}")
                result['dns_errors'].append("No MX record found")
            except Exception as e:
                logger.debug(f"MX record lookup failed for {domain}: {e}")
                result['dns_errors'].append(f"MX record lookup error: {str(e)}")
            
            # Step 3: Additional DNS checks
            try:
                # Check for NS records (name servers)
                ns_records = self.resolver.resolve(domain, 'NS')
                if ns_records:
                    logger.debug(f"NS records found for {domain}")
            except Exception as e:
                logger.debug(f"NS record lookup failed for {domain}: {e}")
            
            # Step 4: Reverse DNS lookup if IP is available
            if result['ip_address']:
                try:
                    reverse_dns = socket.gethostbyaddr(result['ip_address'])
                    logger.debug(f"Reverse DNS for {result['ip_address']}: {reverse_dns[0]}")
                except Exception as e:
                    logger.debug(f"Reverse DNS lookup failed for {result['ip_address']}: {e}")
            
            # Step 5: Determine overall validity
            # Domain is valid if it has either A record or MX record
            result['is_valid'] = result['has_a_record'] or result['has_mx_record']
            
            if result['is_valid']:
                logger.info(f"Domain {domain} is valid")
            else:
                logger.warning(f"Domain {domain} is not valid")
                
        except Exception as e:
            logger.error(f"DNS validation failed for {domain}: {e}")
            result['dns_errors'].append(f"DNS validation error: {str(e)}")
        
        return result
    
    def get_mx_records(self, domain: str) -> List[Dict]:
        """Get MX records for a domain"""
        logger.debug(f"Getting MX records for {domain}")
        
        mx_records = []
        
        try:
            mx_answers = self.resolver.resolve(domain, 'MX')
            
            for mx in mx_answers:
                mx_host = str(mx.exchange).rstrip('.')
                mx_records.append({
                    'host': mx_host,
                    'priority': mx.preference,
                    'is_reachable': self._test_mx_reachability(mx_host)
                })
            
            # Sort by priority
            mx_records.sort(key=lambda x: x['priority'])
            
            logger.debug(f"Found {len(mx_records)} MX records for {domain}")
            
        except Exception as e:
            logger.error(f"Failed to get MX records for {domain}: {e}")
        
        return mx_records
    
    def _test_mx_reachability(self, mx_host: str) -> bool:
        """Test if MX server is reachable"""
        try:
            # Test common mail ports
            ports_to_test = [25, 587, 465]
            
            for port in ports_to_test:
                try:
                    sock = socket.create_connection((mx_host, port), timeout=3)
                    sock.close()
                    logger.debug(f"MX server {mx_host}:{port} is reachable")
                    return True
                except Exception:
                    continue
            
            logger.debug(f"MX server {mx_host} is not reachable on any port")
            return False
            
        except Exception as e:
            logger.debug(f"Failed to test MX reachability for {mx_host}: {e}")
            return False
    
    def check_domain_reputation(self, domain: str) -> Dict:
        """Check domain reputation using DNS-based checks"""
        logger.debug(f"Checking domain reputation for {domain}")
        
        reputation = {
            'domain': domain,
            'is_suspicious': False,
            'blacklist_status': [],
            'reputation_score': 100,  # Start with perfect score
            'warnings': []
        }
        
        try:
            # Check against common DNS blacklists
            blacklists = [
                'zen.spamhaus.org',
                'bl.spamcop.net',
                'dnsbl.sorbs.net'
            ]
            
            # Get domain IP for blacklist checking
            try:
                ip_address = socket.gethostbyname(domain)
                
                for blacklist in blacklists:
                    if self._check_blacklist(ip_address, blacklist):
                        reputation['blacklist_status'].append(blacklist)
                        reputation['reputation_score'] -= 30
                        reputation['is_suspicious'] = True
                
            except Exception as e:
                logger.debug(f"Failed to get IP for domain reputation check: {e}")
            
            # Check for suspicious domain patterns
            suspicious_patterns = [
                'temp', 'temporary', 'disposable', 'fake', 'test',
                'spam', 'trash', 'junk', 'throwaway'
            ]
            
            domain_lower = domain.lower()
            for pattern in suspicious_patterns:
                if pattern in domain_lower:
                    reputation['warnings'].append(f"Suspicious pattern detected: {pattern}")
                    reputation['reputation_score'] -= 10
                    reputation['is_suspicious'] = True
            
            # Check domain age (simplified - would need WHOIS in real implementation)
            if self._is_new_domain(domain):
                reputation['warnings'].append("Domain appears to be relatively new")
                reputation['reputation_score'] -= 5
            
        except Exception as e:
            logger.error(f"Domain reputation check failed for {domain}: {e}")
        
        return reputation
    
    def _check_blacklist(self, ip_address: str, blacklist: str) -> bool:
        """Check if IP is in DNS blacklist"""
        try:
            # Reverse IP for blacklist query
            reversed_ip = '.'.join(reversed(ip_address.split('.')))
            query_host = f"{reversed_ip}.{blacklist}"
            
            # Try to resolve the blacklist query
            socket.gethostbyname(query_host)
            return True  # If resolution succeeds, IP is blacklisted
            
        except socket.gaierror:
            return False  # If resolution fails, IP is not blacklisted
        except Exception as e:
            logger.debug(f"Blacklist check failed for {ip_address} against {blacklist}: {e}")
            return False
    
    def _is_new_domain(self, domain: str) -> bool:
        """Simple heuristic to detect potentially new domains"""
        # This is a simplified check - a real implementation would use WHOIS
        try:
            # Check if domain has minimal DNS infrastructure
            txt_records = self.resolver.resolve(domain, 'TXT')
            return len(txt_records) < 2  # New domains often have minimal TXT records
        except:
            return True  # If we can't check, assume it might be new
    
    def get_domain_info(self, domain: str) -> Dict:
        """Get comprehensive domain information"""
        logger.debug(f"Getting comprehensive domain info for {domain}")
        
        info = {
            'domain': domain,
            'validation_result': self.validate_domain(domain),
            'mx_records': self.get_mx_records(domain),
            'reputation': self.check_domain_reputation(domain),
            'dns_response_time': 0
        }
        
        # Measure DNS response time
        import time
        start_time = time.time()
        try:
            self.resolver.resolve(domain, 'A')
        except:
            pass
        info['dns_response_time'] = time.time() - start_time
        
        return info