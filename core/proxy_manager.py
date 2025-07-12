import requests
import random
from typing import Dict, List, Optional
from config import PROXY_TIMEOUT, PROXY_RETRIES, PROXY_ROTATION_COUNT
from utils.logger import setup_logger

logger = setup_logger(__name__)

class ProxyManager:
    def __init__(self, proxy_list: List[str] = None):
        self.proxy_list = proxy_list or []
        self.current_proxy_index = 0
        self.failed_proxies = set()
        self.usage_count = 0
        self.rotation_count = PROXY_ROTATION_COUNT
        logger.info(f"Proxy manager initialized with {len(self.proxy_list)} proxies")
        logger.info(f"Proxy rotation set to every {self.rotation_count} requests")
        
    def get_proxy_dict(self, proxy: str) -> Dict:
        """Convert proxy string from username:password@ip:port format to requests dict"""
        logger.debug(f"Converting proxy string to dict: {proxy}")
        
        try:
            if '@' in proxy and ':' in proxy:
                # Format: username:password@ip:port
                auth_part, server_part = proxy.split('@')
                username, password = auth_part.split(':', 1)
                
                if ':' in server_part:
                    ip, port = server_part.split(':', 1)
                else:
                    ip, port = server_part, '8080'
                
                proxy_dict = {
                    'http': f'http://{username}:{password}@{ip}:{port}',
                    'https': f'http://{username}:{password}@{ip}:{port}'
                }
                logger.debug(f"Created proxy dict for username:password@ip:port format")
                return proxy_dict
            else:
                logger.warning(f"Invalid proxy format: {proxy}")
                return {}
                
        except Exception as e:
            logger.error(f"Error parsing proxy {proxy}: {e}")
            return {}
    
    def get_working_proxy(self) -> Optional[Dict]:
        """Get current working proxy, rotate if needed"""
        if not self.proxy_list:
            logger.debug("No proxies available")
            return None
        
        # Check if we need to rotate proxy
        if self.usage_count >= self.rotation_count:
            logger.info(f"Rotating proxy after {self.usage_count} uses")
            self.rotate_proxy()
            self.usage_count = 0
        
        # Get current proxy
        attempts = 0
        while attempts < len(self.proxy_list):
            proxy = self.proxy_list[self.current_proxy_index]
            
            if proxy in self.failed_proxies:
                logger.debug(f"Skipping failed proxy: {proxy}")
                self.rotate_proxy()
                attempts += 1
                continue
                
            proxy_dict = self.get_proxy_dict(proxy)
            if proxy_dict and self.test_proxy(proxy_dict):
                logger.debug(f"Using working proxy: {proxy}")
                self.usage_count += 1
                return proxy_dict
            else:
                logger.warning(f"Proxy failed test: {proxy}")
                self.failed_proxies.add(proxy)
                self.rotate_proxy()
                attempts += 1
        
        logger.warning("No working proxies found")
        return None
    
    def rotate_proxy(self):
        """Move to next proxy in the list"""
        if self.proxy_list:
            self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_list)
            logger.debug(f"Rotated to proxy index: {self.current_proxy_index}")
    
    def test_proxy(self, proxy_dict: Dict) -> bool:
        """Test if proxy is working"""
        logger.debug("Testing proxy connectivity")
        try:
            response = requests.get(
                'http://httpbin.org/ip',
                proxies=proxy_dict,
                timeout=PROXY_TIMEOUT
            )
            success = response.status_code == 200
            logger.debug(f"Proxy test result: {'PASS' if success else 'FAIL'}")
            return success
        except Exception as e:
            logger.debug(f"Proxy test failed: {e}")
            return False
    
    def reset_failed_proxies(self):
        """Reset failed proxies list"""
        logger.info("Resetting failed proxies list")
        self.failed_proxies.clear()
    
    def reset_usage_count(self):
        """Reset usage count for new batch"""
        self.usage_count = 0
        logger.debug("Reset proxy usage count")