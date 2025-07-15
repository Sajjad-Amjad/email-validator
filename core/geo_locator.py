import requests
import socket
import time
from typing import Dict, Optional, List
from config import GEOLOCATION_APIS, TIMEOUT
from utils.logger import setup_logger

logger = setup_logger(__name__)

class GeoLocator:
    def __init__(self):
        self.timeout = TIMEOUT
        self.apis = GEOLOCATION_APIS
        logger.info("Geo locator initialized")
    
    def get_email_country(self, email: str, proxy: Optional[str] = None) -> Dict:
        """Get country information for an email address"""
        logger.debug(f"Getting country for email: {email}")
        
        result = {
            'email': email,
            'country': 'Unknown',
            'country_code': 'XX',
            'region': 'Unknown',
            'city': 'Unknown',
            'ip_address': None,
            'method': 'none'
        }
        
        try:
            # Extract domain from email
            domain = email.split('@')[1]
            
            # Step 1: Try to get IP address from domain
            ip_address = self._get_domain_ip(domain)
            if ip_address:
                result['ip_address'] = ip_address
                
                # Step 2: Get geolocation from IP
                geo_info = self._get_ip_geolocation(ip_address, proxy)
                if geo_info:
                    result.update(geo_info)
                    result['method'] = 'ip_geolocation'
                    logger.debug(f"Geolocation found for {email}: {result['country']}")
                    return result
            
            # Step 3: Try domain-based country detection
            country_info = self._get_domain_country(domain)
            if country_info:
                result.update(country_info)
                result['method'] = 'domain_analysis'
                logger.debug(f"Domain-based country for {email}: {result['country']}")
                return result
            
            # Step 4: Fallback to known provider countries
            provider_country = self._get_provider_country(domain)
            if provider_country:
                result.update(provider_country)
                result['method'] = 'provider_database'
                logger.debug(f"Provider-based country for {email}: {result['country']}")
                return result
            
        except Exception as e:
            logger.error(f"Error getting country for {email}: {e}")
        
        logger.debug(f"Could not determine country for {email}")
        return result
    
    def _get_domain_ip(self, domain: str) -> Optional[str]:
        """Get IP address for a domain"""
        try:
            ip_address = socket.gethostbyname(domain)
            logger.debug(f"IP address for {domain}: {ip_address}")
            return ip_address
        except Exception as e:
            logger.debug(f"Failed to get IP for {domain}: {e}")
            return None
    
    def _get_ip_geolocation(self, ip_address: str, proxy: Optional[str] = None) -> Optional[Dict]:
        """Get geolocation information for an IP address"""
        logger.debug(f"Getting geolocation for IP: {ip_address}")
        
        # Setup proxy if provided
        proxies = None
        if proxy:
            proxies = {
                'http': f'http://{proxy}',
                'https': f'http://{proxy}'
            }
        
        # Try multiple geolocation APIs
        for api_url in self.apis:
            try:
                logger.debug(f"Trying geolocation API: {api_url}")
                
                # Make request to geolocation API
                response = requests.get(
                    f"{api_url}{ip_address}" if not api_url.endswith('json/') else f"{api_url}",
                    proxies=proxies,
                    timeout=self.timeout,
                    headers={'User-Agent': 'Email-Validator/1.0'}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Parse response based on API format
                    geo_info = self._parse_geolocation_response(data, api_url)
                    if geo_info:
                        logger.debug(f"Geolocation successful: {geo_info}")
                        return geo_info
                
            except Exception as e:
                logger.debug(f"Geolocation API {api_url} failed: {e}")
                continue
        
        return None
    
    def _parse_geolocation_response(self, data: Dict, api_url: str) -> Optional[Dict]:
        """Parse geolocation API response"""
        try:
            if 'ip-api.com' in api_url:
                if data.get('status') == 'success':
                    return {
                        'country': data.get('country', 'Unknown'),
                        'country_code': data.get('countryCode', 'XX'),
                        'region': data.get('regionName', 'Unknown'),
                        'city': data.get('city', 'Unknown'),
                        'timezone': data.get('timezone', 'Unknown')
                    }
            
            elif 'ipapi.co' in api_url:
                if 'error' not in data:
                    return {
                        'country': data.get('country_name', 'Unknown'),
                        'country_code': data.get('country_code', 'XX'),
                        'region': data.get('region', 'Unknown'),
                        'city': data.get('city', 'Unknown'),
                        'timezone': data.get('timezone', 'Unknown')
                    }
            
            elif 'ipify.org' in api_url:
                # This API only returns IP, not geolocation
                return None
            
            # Generic parsing for other APIs
            return {
                'country': data.get('country', data.get('country_name', 'Unknown')),
                'country_code': data.get('country_code', data.get('countryCode', 'XX')),
                'region': data.get('region', data.get('regionName', 'Unknown')),
                'city': data.get('city', 'Unknown')
            }
            
        except Exception as e:
            logger.debug(f"Failed to parse geolocation response: {e}")
            return None
    
    def _get_domain_country(self, domain: str) -> Optional[Dict]:
        """Get country information from domain TLD and patterns"""
        logger.debug(f"Analyzing domain for country: {domain}")
        
        # Country code TLDs
        country_tlds = {
            '.uk': {'country': 'United Kingdom', 'country_code': 'GB'},
            '.us': {'country': 'United States', 'country_code': 'US'},
            '.ca': {'country': 'Canada', 'country_code': 'CA'},
            '.au': {'country': 'Australia', 'country_code': 'AU'},
            '.de': {'country': 'Germany', 'country_code': 'DE'},
            '.fr': {'country': 'France', 'country_code': 'FR'},
            '.jp': {'country': 'Japan', 'country_code': 'JP'},
            '.cn': {'country': 'China', 'country_code': 'CN'},
            '.ru': {'country': 'Russia', 'country_code': 'RU'},
            '.in': {'country': 'India', 'country_code': 'IN'},
            '.br': {'country': 'Brazil', 'country_code': 'BR'},
            '.it': {'country': 'Italy', 'country_code': 'IT'},
            '.es': {'country': 'Spain', 'country_code': 'ES'},
            '.nl': {'country': 'Netherlands', 'country_code': 'NL'},
            '.mx': {'country': 'Mexico', 'country_code': 'MX'},
            '.kr': {'country': 'South Korea', 'country_code': 'KR'},
            '.se': {'country': 'Sweden', 'country_code': 'SE'},
            '.no': {'country': 'Norway', 'country_code': 'NO'},
            '.dk': {'country': 'Denmark', 'country_code': 'DK'},
            '.fi': {'country': 'Finland', 'country_code': 'FI'},
            '.pl': {'country': 'Poland', 'country_code': 'PL'},
            '.ch': {'country': 'Switzerland', 'country_code': 'CH'},
            '.at': {'country': 'Austria', 'country_code': 'AT'},
            '.be': {'country': 'Belgium', 'country_code': 'BE'},
            '.pt': {'country': 'Portugal', 'country_code': 'PT'},
            '.gr': {'country': 'Greece', 'country_code': 'GR'},
            '.cz': {'country': 'Czech Republic', 'country_code': 'CZ'},
            '.hu': {'country': 'Hungary', 'country_code': 'HU'},
            '.ro': {'country': 'Romania', 'country_code': 'RO'},
            '.bg': {'country': 'Bulgaria', 'country_code': 'BG'},
            '.hr': {'country': 'Croatia', 'country_code': 'HR'},
            '.sk': {'country': 'Slovakia', 'country_code': 'SK'},
            '.si': {'country': 'Slovenia', 'country_code': 'SI'},
            '.ee': {'country': 'Estonia', 'country_code': 'EE'},
            '.lv': {'country': 'Latvia', 'country_code': 'LV'},
            '.lt': {'country': 'Lithuania', 'country_code': 'LT'},
            '.ie': {'country': 'Ireland', 'country_code': 'IE'},
            '.is': {'country': 'Iceland', 'country_code': 'IS'},
            '.za': {'country': 'South Africa', 'country_code': 'ZA'},
            '.eg': {'country': 'Egypt', 'country_code': 'EG'},
            '.ng': {'country': 'Nigeria', 'country_code': 'NG'},
            '.ma': {'country': 'Morocco', 'country_code': 'MA'},
            '.ke': {'country': 'Kenya', 'country_code': 'KE'},
            '.gh': {'country': 'Ghana', 'country_code': 'GH'},
            '.tz': {'country': 'Tanzania', 'country_code': 'TZ'},
            '.ug': {'country': 'Uganda', 'country_code': 'UG'},
            '.zm': {'country': 'Zambia', 'country_code': 'ZM'},
            '.zw': {'country': 'Zimbabwe', 'country_code': 'ZW'},
            '.ar': {'country': 'Argentina', 'country_code': 'AR'},
            '.cl': {'country': 'Chile', 'country_code': 'CL'},
            '.co': {'country': 'Colombia', 'country_code': 'CO'},
            '.pe': {'country': 'Peru', 'country_code': 'PE'},
            '.ve': {'country': 'Venezuela', 'country_code': 'VE'},
            '.uy': {'country': 'Uruguay', 'country_code': 'UY'},
            '.py': {'country': 'Paraguay', 'country_code': 'PY'},
            '.bo': {'country': 'Bolivia', 'country_code': 'BO'},
            '.ec': {'country': 'Ecuador', 'country_code': 'EC'},
            '.th': {'country': 'Thailand', 'country_code': 'TH'},
            '.sg': {'country': 'Singapore', 'country_code': 'SG'},
            '.my': {'country': 'Malaysia', 'country_code': 'MY'},
            '.id': {'country': 'Indonesia', 'country_code': 'ID'},
            '.ph': {'country': 'Philippines', 'country_code': 'PH'},
            '.vn': {'country': 'Vietnam', 'country_code': 'VN'},
            '.tw': {'country': 'Taiwan', 'country_code': 'TW'},
            '.hk': {'country': 'Hong Kong', 'country_code': 'HK'},
            '.mo': {'country': 'Macau', 'country_code': 'MO'},
            '.nz': {'country': 'New Zealand', 'country_code': 'NZ'},
            '.pk': {'country': 'Pakistan', 'country_code': 'PK'},
            '.bd': {'country': 'Bangladesh', 'country_code': 'BD'},
            '.lk': {'country': 'Sri Lanka', 'country_code': 'LK'},
            '.np': {'country': 'Nepal', 'country_code': 'NP'},
            '.mm': {'country': 'Myanmar', 'country_code': 'MM'},
            '.kh': {'country': 'Cambodia', 'country_code': 'KH'},
            '.la': {'country': 'Laos', 'country_code': 'LA'},
            '.mn': {'country': 'Mongolia', 'country_code': 'MN'},
            '.ge': {'country': 'Georgia', 'country_code': 'GE'},
            '.am': {'country': 'Armenia', 'country_code': 'AM'},
            '.az': {'country': 'Azerbaijan', 'country_code': 'AZ'},
            '.kz': {'country': 'Kazakhstan', 'country_code': 'KZ'},
            '.kg': {'country': 'Kyrgyzstan', 'country_code': 'KG'},
            '.tj': {'country': 'Tajikistan', 'country_code': 'TJ'},
            '.tm': {'country': 'Turkmenistan', 'country_code': 'TM'},
            '.uz': {'country': 'Uzbekistan', 'country_code': 'UZ'},
            '.ir': {'country': 'Iran', 'country_code': 'IR'},
            '.iq': {'country': 'Iraq', 'country_code': 'IQ'},
            '.sa': {'country': 'Saudi Arabia', 'country_code': 'SA'},
            '.ae': {'country': 'United Arab Emirates', 'country_code': 'AE'},
            '.kw': {'country': 'Kuwait', 'country_code': 'KW'},
            '.qa': {'country': 'Qatar', 'country_code': 'QA'},
            '.bh': {'country': 'Bahrain', 'country_code': 'BH'},
            '.om': {'country': 'Oman', 'country_code': 'OM'},
            '.ye': {'country': 'Yemen', 'country_code': 'YE'},
            '.jo': {'country': 'Jordan', 'country_code': 'JO'},
            '.lb': {'country': 'Lebanon', 'country_code': 'LB'},
            '.sy': {'country': 'Syria', 'country_code': 'SY'},
            '.il': {'country': 'Israel', 'country_code': 'IL'},
            '.ps': {'country': 'Palestine', 'country_code': 'PS'},
            '.tr': {'country': 'Turkey', 'country_code': 'TR'},
            '.cy': {'country': 'Cyprus', 'country_code': 'CY'},
            '.mt': {'country': 'Malta', 'country_code': 'MT'},
            '.ad': {'country': 'Andorra', 'country_code': 'AD'},
            '.sm': {'country': 'San Marino', 'country_code': 'SM'},
            '.va': {'country': 'Vatican City', 'country_code': 'VA'},
            '.mc': {'country': 'Monaco', 'country_code': 'MC'},
            '.li': {'country': 'Liechtenstein', 'country_code': 'LI'},
            '.lu': {'country': 'Luxembourg', 'country_code': 'LU'}
        }
        
        # Check for country-specific TLDs
        for tld, info in country_tlds.items():
            if domain.endswith(tld):
                return {
                    'country': info['country'],
                    'country_code': info['country_code'],
                    'region': 'Unknown',
                    'city': 'Unknown'
                }
        
        # Check for multi-level country domains
        multi_level_domains = {
            '.co.uk': {'country': 'United Kingdom', 'country_code': 'GB'},
            '.co.jp': {'country': 'Japan', 'country_code': 'JP'},
            '.co.kr': {'country': 'South Korea', 'country_code': 'KR'},
            '.co.in': {'country': 'India', 'country_code': 'IN'},
            '.co.za': {'country': 'South Africa', 'country_code': 'ZA'},
            '.com.au': {'country': 'Australia', 'country_code': 'AU'},
            '.com.br': {'country': 'Brazil', 'country_code': 'BR'},
            '.com.mx': {'country': 'Mexico', 'country_code': 'MX'},
            '.com.ar': {'country': 'Argentina', 'country_code': 'AR'},
            '.com.cn': {'country': 'China', 'country_code': 'CN'},
            '.com.tw': {'country': 'Taiwan', 'country_code': 'TW'},
            '.com.hk': {'country': 'Hong Kong', 'country_code': 'HK'},
            '.com.sg': {'country': 'Singapore', 'country_code': 'SG'},
            '.com.my': {'country': 'Malaysia', 'country_code': 'MY'},
            '.com.ph': {'country': 'Philippines', 'country_code': 'PH'},
            '.com.th': {'country': 'Thailand', 'country_code': 'TH'},
            '.com.vn': {'country': 'Vietnam', 'country_code': 'VN'},
            '.com.pk': {'country': 'Pakistan', 'country_code': 'PK'},
            '.com.bd': {'country': 'Bangladesh', 'country_code': 'BD'},
            '.com.lk': {'country': 'Sri Lanka', 'country_code': 'LK'},
            '.com.np': {'country': 'Nepal', 'country_code': 'NP'},
            '.com.mm': {'country': 'Myanmar', 'country_code': 'MM'},
            '.com.kh': {'country': 'Cambodia', 'country_code': 'KH'},
            '.com.la': {'country': 'Laos', 'country_code': 'LA'},
            '.com.mn': {'country': 'Mongolia', 'country_code': 'MN'},
            '.ne.jp': {'country': 'Japan', 'country_code': 'JP'},
            '.or.jp': {'country': 'Japan', 'country_code': 'JP'},
            '.ac.jp': {'country': 'Japan', 'country_code': 'JP'},
            '.go.jp': {'country': 'Japan', 'country_code': 'JP'},
            '.ed.jp': {'country': 'Japan', 'country_code': 'JP'},
            '.gr.jp': {'country': 'Japan', 'country_code': 'JP'},
            '.lg.jp': {'country': 'Japan', 'country_code': 'JP'},
            '.ad.jp': {'country': 'Japan', 'country_code': 'JP'}
        }
        
        for multi_tld, info in multi_level_domains.items():
            if domain.endswith(multi_tld):
                return {
                    'country': info['country'],
                    'country_code': info['country_code'],
                    'region': 'Unknown',
                    'city': 'Unknown'
                }
        
        return None
    
    def _get_provider_country(self, domain: str) -> Optional[Dict]:
        """Get country information based on known email providers"""
        logger.debug(f"Checking provider country for domain: {domain}")
        
        # Known email providers and their primary countries
        provider_countries = {
            'gmail.com': {'country': 'United States', 'country_code': 'US'},
            'yahoo.com': {'country': 'United States', 'country_code': 'US'},
            'yahoo.co.uk': {'country': 'United Kingdom', 'country_code': 'GB'},
            'yahoo.co.jp': {'country': 'Japan', 'country_code': 'JP'},
            'yahoo.de': {'country': 'Germany', 'country_code': 'DE'},
            'yahoo.fr': {'country': 'France', 'country_code': 'FR'},
            'yahoo.ca': {'country': 'Canada', 'country_code': 'CA'},
            'yahoo.com.au': {'country': 'Australia', 'country_code': 'AU'},
            'hotmail.com': {'country': 'United States', 'country_code': 'US'},
            'hotmail.co.uk': {'country': 'United Kingdom', 'country_code': 'GB'},
            'hotmail.de': {'country': 'Germany', 'country_code': 'DE'},
            'hotmail.fr': {'country': 'France', 'country_code': 'FR'},
            'outlook.com': {'country': 'United States', 'country_code': 'US'},
            'live.com': {'country': 'United States', 'country_code': 'US'},
            'live.co.uk': {'country': 'United Kingdom', 'country_code': 'GB'},
            'msn.com': {'country': 'United States', 'country_code': 'US'},
            'aol.com': {'country': 'United States', 'country_code': 'US'},
            'aol.co.uk': {'country': 'United Kingdom', 'country_code': 'GB'},
            'verizon.com': {'country': 'United States', 'country_code': 'US'},
            'verizon.net': {'country': 'United States', 'country_code': 'US'},
            'att.com': {'country': 'United States', 'country_code': 'US'},
            'att.net': {'country': 'United States', 'country_code': 'US'},
            'comcast.net': {'country': 'United States', 'country_code': 'US'},
            'cox.net': {'country': 'United States', 'country_code': 'US'},
            'charter.net': {'country': 'United States', 'country_code': 'US'},
            'earthlink.net': {'country': 'United States', 'country_code': 'US'},
            'rogers.com': {'country': 'Canada', 'country_code': 'CA'},
            'bell.ca': {'country': 'Canada', 'country_code': 'CA'},
            'telus.net': {'country': 'Canada', 'country_code': 'CA'},
            'shaw.ca': {'country': 'Canada', 'country_code': 'CA'},
            'btinternet.com': {'country': 'United Kingdom', 'country_code': 'GB'},
            'virginmedia.com': {'country': 'United Kingdom', 'country_code': 'GB'},
            'sky.com': {'country': 'United Kingdom', 'country_code': 'GB'},
            'talktalk.net': {'country': 'United Kingdom', 'country_code': 'GB'},
            'tiscali.co.uk': {'country': 'United Kingdom', 'country_code': 'GB'},
            'web.de': {'country': 'Germany', 'country_code': 'DE'},
            'gmx.de': {'country': 'Germany', 'country_code': 'DE'},
            'gmx.com': {'country': 'Germany', 'country_code': 'DE'},
            'freenet.de': {'country': 'Germany', 'country_code': 'DE'},
            't-online.de': {'country': 'Germany', 'country_code': 'DE'},
            'orange.fr': {'country': 'France', 'country_code': 'FR'},
            'free.fr': {'country': 'France', 'country_code': 'FR'},
            'wanadoo.fr': {'country': 'France', 'country_code': 'FR'},
            'laposte.net': {'country': 'France', 'country_code': 'FR'},
            'libero.it': {'country': 'Italy', 'country_code': 'IT'},
            'tiscali.it': {'country': 'Italy', 'country_code': 'IT'},
            'virgilio.it': {'country': 'Italy', 'country_code': 'IT'},
            'alice.it': {'country': 'Italy', 'country_code': 'IT'},
            'terra.es': {'country': 'Spain', 'country_code': 'ES'},
            'telefonica.net': {'country': 'Spain', 'country_code': 'ES'},
            'ya.ru': {'country': 'Russia', 'country_code': 'RU'},
            'yandex.ru': {'country': 'Russia', 'country_code': 'RU'},
            'mail.ru': {'country': 'Russia', 'country_code': 'RU'},
            'rambler.ru': {'country': 'Russia', 'country_code': 'RU'},
            'qq.com': {'country': 'China', 'country_code': 'CN'},
            'sina.com': {'country': 'China', 'country_code': 'CN'},
            'sina.cn': {'country': 'China', 'country_code': 'CN'},
            '126.com': {'country': 'China', 'country_code': 'CN'},
            '163.com': {'country': 'China', 'country_code': 'CN'},
            'sohu.com': {'country': 'China', 'country_code': 'CN'},
            'naver.com': {'country': 'South Korea', 'country_code': 'KR'},
            'daum.net': {'country': 'South Korea', 'country_code': 'KR'},
            'hanmail.net': {'country': 'South Korea', 'country_code': 'KR'},
            'docomo.ne.jp': {'country': 'Japan', 'country_code': 'JP'},
            'ezweb.ne.jp': {'country': 'Japan', 'country_code': 'JP'},
            'softbank.ne.jp': {'country': 'Japan', 'country_code': 'JP'},
            'softbank.jp': {'country': 'Japan', 'country_code': 'JP'},
            'nifty.com': {'country': 'Japan', 'country_code': 'JP'},
            'biglobe.ne.jp': {'country': 'Japan', 'country_code': 'JP'},
            'ocn.ne.jp': {'country': 'Japan', 'country_code': 'JP'},
            'so-net.ne.jp': {'country': 'Japan', 'country_code': 'JP'},
            'dion.ne.jp': {'country': 'Japan', 'country_code': 'JP'},
            'goo.ne.jp': {'country': 'Japan', 'country_code': 'JP'},
            'excite.co.jp': {'country': 'Japan', 'country_code': 'JP'},
            'rediffmail.com': {'country': 'India', 'country_code': 'IN'},
            'sify.com': {'country': 'India', 'country_code': 'IN'},
            'indiatimes.com': {'country': 'India', 'country_code': 'IN'},
            'yahoo.co.in': {'country': 'India', 'country_code': 'IN'},
            'gmail.co.in': {'country': 'India', 'country_code': 'IN'},
            'uol.com.br': {'country': 'Brazil', 'country_code': 'BR'},
            'bol.com.br': {'country': 'Brazil', 'country_code': 'BR'},
            'ig.com.br': {'country': 'Brazil', 'country_code': 'BR'},
            'globo.com': {'country': 'Brazil', 'country_code': 'BR'},
            'terra.com.br': {'country': 'Brazil', 'country_code': 'BR'},
            'telstra.com': {'country': 'Australia', 'country_code': 'AU'},
            'bigpond.com': {'country': 'Australia', 'country_code': 'AU'},
            'optusnet.com.au': {'country': 'Australia', 'country_code': 'AU'},
            'iinet.net.au': {'country': 'Australia', 'country_code': 'AU'},
            'xtra.co.nz': {'country': 'New Zealand', 'country_code': 'NZ'},
            'clear.net.nz': {'country': 'New Zealand', 'country_code': 'NZ'},
            'orcon.net.nz': {'country': 'New Zealand', 'country_code': 'NZ'},
            'slingshot.co.nz': {'country': 'New Zealand', 'country_code': 'NZ'}
        }
        
        if domain.lower() in provider_countries:
            info = provider_countries[domain.lower()]
            return {
                'country': info['country'],
                'country_code': info['country_code'],
                'region': 'Unknown',
                'city': 'Unknown'
            }
        
        return None
    
    def get_country_statistics(self, results: List[Dict]) -> Dict:
        """Generate country statistics from validation results"""
        logger.info("Generating country statistics")
        
        stats = {
            'total_emails': len(results),
            'countries_found': {},
            'country_summary': [],
            'unknown_count': 0
        }
        
        # Count emails by country
        for result in results:
            country = result.get('country', 'Unknown')
            if country == 'Unknown':
                stats['unknown_count'] += 1
            else:
                if country not in stats['countries_found']:
                    stats['countries_found'][country] = {
                        'total': 0,
                        'valid': 0,
                        'invalid': 0,
                        'skipped': 0
                    }
                
                stats['countries_found'][country]['total'] += 1
                
                status = result.get('status', 'INVALID')
                if status == 'VALID':
                    stats['countries_found'][country]['valid'] += 1
                elif status == 'INVALID':
                    stats['countries_found'][country]['invalid'] += 1
                else:
                    stats['countries_found'][country]['skipped'] += 1
        
        # Create summary sorted by total count
        for country, data in sorted(stats['countries_found'].items(), 
                                   key=lambda x: x[1]['total'], reverse=True):
            stats['country_summary'].append({
                'country': country,
                'total': data['total'],
                'valid': data['valid'],
                'invalid': data['invalid'],
                'skipped': data['skipped'],
                'percentage': (data['total'] / stats['total_emails']) * 100
            })
        
        logger.info(f"Country statistics: {len(stats['countries_found'])} countries found")
        return stats