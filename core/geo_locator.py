import requests
import socket
from typing import Dict, Optional
from config import GEO_APIS, PROXY_TIMEOUT
from utils.logger import setup_logger

logger = setup_logger(__name__)

class GeoLocator:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = PROXY_TIMEOUT
        logger.info("Geo locator initialized")
        
    def get_domain_ip(self, domain: str) -> Optional[str]:
        logger.debug(f"Resolving IP for domain: {domain}")
        try:
            ip = socket.gethostbyname(domain)
            logger.debug(f"Domain {domain} resolved to IP: {ip}")
            return ip
        except socket.error as e:
            logger.debug(f"Failed to resolve IP for {domain}: {e}")
            return None
    
    def get_country_from_ip(self, ip: str, proxies: Dict = None) -> Dict:
        logger.info(f"Getting country information for IP: {ip}")
        
        for api_url in GEO_APIS:
            logger.debug(f"Trying geolocation API: {api_url}")
            try:
                response = self.session.get(
                    f"{api_url}{ip}",
                    proxies=proxies,
                    timeout=PROXY_TIMEOUT
                )
                
                if response.status_code == 200:
                    data = response.json()
                    logger.debug(f"API response from {api_url}: {data}")
                    
                    country = self._extract_country(data)
                    if country:
                        logger.info(f"Country detected for IP {ip}: {country}")
                        return {
                            'country': country,
                            'ip': ip,
                            'api_used': api_url
                        }
                else:
                    logger.debug(f"API {api_url} returned status code: {response.status_code}")
                        
            except Exception as e:
                logger.debug(f"Geo API {api_url} failed: {e}")
                continue
        
        logger.warning(f"Failed to get country for IP {ip} from all APIs")
        return {'country': 'Unknown', 'ip': ip, 'api_used': None}
    
    def _extract_country(self, data: Dict) -> Optional[str]:
        country_fields = ['country', 'country_name', 'countryName', 'country_code']
        
        for field in country_fields:
            if field in data and data[field]:
                logger.debug(f"Found country in field '{field}': {data[field]}")
                return data[field]
        
        logger.debug("No country field found in API response")
        return None
    
    def get_email_country(self, email: str, proxies: Dict = None) -> Dict:
        logger.info(f"Getting country for email: {email}")
        try:
            domain = email.split('@')[1]
            logger.debug(f"Extracted domain from email: {domain}")
            
            ip = self.get_domain_ip(domain)
            
            if not ip:
                logger.warning(f"Could not resolve IP for domain: {domain}")
                return {'country': 'Unknown', 'ip': None, 'domain': domain}
            
            geo_info = self.get_country_from_ip(ip, proxies)
            geo_info['domain'] = domain
            
            return geo_info
            
        except Exception as e:
            logger.error(f"Error getting country for {email}: {e}")
            return {'country': 'Unknown', 'ip': None, 'domain': 'Unknown'}