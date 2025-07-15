import random
import time
import requests
from typing import List, Optional, Dict
from config import PROXY_ROTATION_COUNT, PROXY_TIMEOUT, MAX_PROXY_RETRIES
from utils.logger import setup_logger

logger = setup_logger(__name__)

class ProxyManager:
    def __init__(self, proxy_list: List[str] = None):
        self.proxy_list = proxy_list or []
        self.current_proxy_index = 0
        self.usage_count = 0
        self.rotation_count = PROXY_ROTATION_COUNT
        self.timeout = PROXY_TIMEOUT
        self.max_retries = MAX_PROXY_RETRIES
        self.failed_proxies = set()
        self.proxy_stats = {}
        
        # Initialize proxy statistics
        for proxy in self.proxy_list:
            self.proxy_stats[proxy] = {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'last_used': None,
                'is_working': True
            }
        
        logger.info(f"Proxy manager initialized with {len(self.proxy_list)} proxies")
    
    def get_working_proxy(self) -> Optional[str]:
        """Get a working proxy with automatic rotation"""
        if not self.proxy_list:
            logger.debug("No proxies available, returning None")
            return None
        
        # Check if we need to rotate proxy
        if self.usage_count >= self.rotation_count:
            self.rotate_proxy()
        
        # Get current proxy
        current_proxy = self._get_current_proxy()
        
        if current_proxy:
            self.usage_count += 1
            self.proxy_stats[current_proxy]['total_requests'] += 1
            self.proxy_stats[current_proxy]['last_used'] = time.time()
            logger.debug(f"Using proxy: {current_proxy} (usage: {self.usage_count}/{self.rotation_count})")
        
        return current_proxy
    
    def _get_current_proxy(self) -> Optional[str]:
        """Get current proxy, skipping failed ones"""
        if not self.proxy_list:
            return None
        
        attempts = 0
        while attempts < len(self.proxy_list):
            current_proxy = self.proxy_list[self.current_proxy_index]
            
            # Check if proxy is marked as failed
            if current_proxy not in self.failed_proxies:
                if self.proxy_stats[current_proxy]['is_working']:
                    return current_proxy
            
            # Move to next proxy
            self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_list)
            attempts += 1
        
        # If all proxies failed, reset failed proxies and try again
        if self.failed_proxies:
            logger.warning("All proxies failed, resetting failed proxy list")
            self.failed_proxies.clear()
            for proxy in self.proxy_stats:
                self.proxy_stats[proxy]['is_working'] = True
            return self.proxy_list[self.current_proxy_index]
        
        return None
    
    def rotate_proxy(self):
        """Rotate to next proxy"""
        if not self.proxy_list:
            return
        
        old_index = self.current_proxy_index
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_list)
        self.usage_count = 0
        
        logger.debug(f"Proxy rotated: {old_index} -> {self.current_proxy_index}")
    
    def mark_proxy_failed(self, proxy: str):
        """Mark a proxy as failed"""
        if proxy in self.proxy_list:
            self.failed_proxies.add(proxy)
            self.proxy_stats[proxy]['is_working'] = False
            self.proxy_stats[proxy]['failed_requests'] += 1
            logger.warning(f"Proxy marked as failed: {proxy}")
            
            # Rotate to next proxy if current one failed
            if proxy == self.proxy_list[self.current_proxy_index]:
                self.rotate_proxy()
    
    def mark_proxy_success(self, proxy: str):
        """Mark a proxy as successful"""
        if proxy in self.proxy_list:
            self.proxy_stats[proxy]['successful_requests'] += 1
            logger.debug(f"Proxy marked as successful: {proxy}")
    
    def test_proxy(self, proxy: str) -> bool:
        """Test if a proxy is working"""
        logger.debug(f"Testing proxy: {proxy}")
        
        try:
            # Parse proxy format: username:password@ip:port
            if '@' in proxy:
                auth_part, server_part = proxy.split('@')
                username, password = auth_part.split(':')
                ip, port = server_part.split(':')
                
                proxy_dict = {
                    'http': f'http://{username}:{password}@{ip}:{port}',
                    'https': f'http://{username}:{password}@{ip}:{port}'
                }
            else:
                # Simple ip:port format
                proxy_dict = {
                    'http': f'http://{proxy}',
                    'https': f'http://{proxy}'
                }
            
            # Test proxy with a simple request
            response = requests.get(
                'http://httpbin.org/ip',
                proxies=proxy_dict,
                timeout=self.timeout,
                headers={'User-Agent': 'Email-Validator/1.0'}
            )
            
            if response.status_code == 200:
                logger.debug(f"Proxy test successful: {proxy}")
                return True
            else:
                logger.debug(f"Proxy test failed with status {response.status_code}: {proxy}")
                return False
                
        except Exception as e:
            logger.debug(f"Proxy test failed: {proxy} - {e}")
            return False
    
    def test_all_proxies(self) -> List[str]:
        """Test all proxies and return working ones"""
        logger.info("Testing all proxies")
        working_proxies = []
        
        for proxy in self.proxy_list:
            if self.test_proxy(proxy):
                working_proxies.append(proxy)
                self.proxy_stats[proxy]['is_working'] = True
            else:
                self.mark_proxy_failed(proxy)
        
        logger.info(f"Proxy test completed: {len(working_proxies)}/{len(self.proxy_list)} working")
        return working_proxies
    
    def get_proxy_for_request(self, url: str) -> Optional[Dict]:
        """Get proxy configuration for requests library"""
        proxy = self.get_working_proxy()
        
        if not proxy:
            return None
        
        try:
            # Parse proxy format: username:password@ip:port
            if '@' in proxy:
                auth_part, server_part = proxy.split('@')
                username, password = auth_part.split(':')
                ip, port = server_part.split(':')
                
                proxy_url = f'http://{username}:{password}@{ip}:{port}'
            else:
                # Simple ip:port format
                proxy_url = f'http://{proxy}'
            
            return {
                'http': proxy_url,
                'https': proxy_url
            }
            
        except Exception as e:
            logger.error(f"Error parsing proxy {proxy}: {e}")
            self.mark_proxy_failed(proxy)
            return None
    
    def reset_usage_count(self):
        """Reset usage count for current proxy"""
        self.usage_count = 0
        logger.debug("Proxy usage count reset")
    
    def get_proxy_stats(self) -> Dict:
        """Get statistics about proxy usage"""
        if not self.proxy_list:
            return {'total_proxies': 0, 'working_proxies': 0, 'failed_proxies': 0}
        
        working_count = sum(1 for stats in self.proxy_stats.values() if stats['is_working'])
        failed_count = len(self.failed_proxies)
        
        stats = {
            'total_proxies': len(self.proxy_list),
            'working_proxies': working_count,
            'failed_proxies': failed_count,
            'current_proxy_index': self.current_proxy_index,
            'current_usage_count': self.usage_count,
            'rotation_threshold': self.rotation_count,
            'proxy_details': []
        }
        
        # Add detailed stats for each proxy
        for proxy, proxy_stats in self.proxy_stats.items():
            success_rate = 0
            if proxy_stats['total_requests'] > 0:
                success_rate = (proxy_stats['successful_requests'] / proxy_stats['total_requests']) * 100
            
            stats['proxy_details'].append({
                'proxy': proxy,
                'is_working': proxy_stats['is_working'],
                'total_requests': proxy_stats['total_requests'],
                'successful_requests': proxy_stats['successful_requests'],
                'failed_requests': proxy_stats['failed_requests'],
                'success_rate': success_rate,
                'last_used': proxy_stats['last_used']
            })
        
        return stats
    
    def shuffle_proxies(self):
        """Shuffle proxy list for random selection"""
        if self.proxy_list:
            random.shuffle(self.proxy_list)
            self.current_proxy_index = 0
            logger.debug("Proxy list shuffled")
    
    def add_proxy(self, proxy: str):
        """Add a new proxy to the list"""
        if proxy not in self.proxy_list:
            self.proxy_list.append(proxy)
            self.proxy_stats[proxy] = {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'last_used': None,
                'is_working': True
            }
            logger.info(f"Added new proxy: {proxy}")
    
    def remove_proxy(self, proxy: str):
        """Remove a proxy from the list"""
        if proxy in self.proxy_list:
            self.proxy_list.remove(proxy)
            if proxy in self.proxy_stats:
                del self.proxy_stats[proxy]
            if proxy in self.failed_proxies:
                self.failed_proxies.remove(proxy)
            
            # Adjust current index if needed
            if self.current_proxy_index >= len(self.proxy_list) and self.proxy_list:
                self.current_proxy_index = 0
            
            logger.info(f"Removed proxy: {proxy}")
    
    def get_best_proxy(self) -> Optional[str]:
        """Get the proxy with the highest success rate"""
        if not self.proxy_list:
            return None
        
        best_proxy = None
        best_success_rate = -1
        
        for proxy, stats in self.proxy_stats.items():
            if not stats['is_working']:
                continue
            
            if stats['total_requests'] == 0:
                # New proxy, give it a chance
                success_rate = 100
            else:
                success_rate = (stats['successful_requests'] / stats['total_requests']) * 100
            
            if success_rate > best_success_rate:
                best_success_rate = success_rate
                best_proxy = proxy
        
        return best_proxy
    
    def cleanup_failed_proxies(self):
        """Remove permanently failed proxies"""
        proxies_to_remove = []
        
        for proxy, stats in self.proxy_stats.items():
            if not stats['is_working'] and stats['failed_requests'] > 10:
                proxies_to_remove.append(proxy)
        
        for proxy in proxies_to_remove:
            self.remove_proxy(proxy)
        
        if proxies_to_remove:
            logger.info(f"Cleaned up {len(proxies_to_remove)} failed proxies")
    
    def has_working_proxies(self) -> bool:
        """Check if there are any working proxies"""
        return any(stats['is_working'] for stats in self.proxy_stats.values())
    
    def get_random_proxy(self) -> Optional[str]:
        """Get a random working proxy"""
        working_proxies = [proxy for proxy, stats in self.proxy_stats.items() 
                          if stats['is_working']]
        
        if working_proxies:
            return random.choice(working_proxies)
        
        return None