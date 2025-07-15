import smtplib
import socket
import time
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Optional, List
from config import SMTP_TIMEOUT, SMTP_PORT, TEST_EMAIL_RECIPIENT, TEST_EMAIL_SUBJECT, TEST_EMAIL_BODY
from utils.logger import setup_logger

logger = setup_logger(__name__)

class SMTPChecker:
    def __init__(self):
        self.timeout = SMTP_TIMEOUT
        logger.info("SMTP checker initialized")
        
    def check_smtp_connection(self, mx_server: str) -> Dict:
        """Test SMTP connection to server with multiple port attempts"""
        logger.debug(f"Testing SMTP connection to: {mx_server}")
        
        # Try multiple ports in order of preference
        ports_to_try = [587, 25, 465, 2525]
        
        for port in ports_to_try:
            try:
                logger.debug(f"Trying port {port} on {mx_server}")
                
                # Create socket connection with timeout
                sock = socket.create_connection((mx_server, port), timeout=self.timeout)
                sock.close()
                
                logger.debug(f"SMTP port {port} accessible on {mx_server}")
                return {
                    'smtp_valid': True,
                    'smtp_response': f'Port {port} accessible',
                    'server': mx_server,
                    'port': port
                }
            except Exception as e:
                logger.debug(f"Port {port} failed on {mx_server}: {e}")
                continue
        
        logger.debug(f"All SMTP ports failed for {mx_server}")
        return {
            'smtp_valid': False,
            'smtp_response': 'All SMTP ports unreachable',
            'server': mx_server
        }
    
    def verify_email_deliverability(self, email: str, mx_server: str) -> Dict:
        """Test if email can receive messages using SMTP commands"""
        logger.debug(f"Testing deliverability for: {email} via {mx_server}")
        
        try:
            # Try multiple ports for deliverability check
            ports_to_try = [25, 587, 465]
            
            for port in ports_to_try:
                try:
                    with smtplib.SMTP(timeout=self.timeout) as server:
                        # Connect and identify
                        logger.debug(f"Connecting to {mx_server}:{port}")
                        server.connect(mx_server, port)
                        server.helo('validator.test')
                        
                        # Test MAIL FROM
                        logger.debug(f"Testing MAIL FROM for {email}")
                        code, response = server.mail('test@validator.com')
                        logger.debug(f"MAIL FROM response: {code} {response}")
                        
                        if code not in [250, 251]:
                            continue
                        
                        # Test RCPT TO
                        logger.debug(f"Testing RCPT TO for {email}")
                        code, response = server.rcpt(email)
                        logger.debug(f"RCPT TO response: {code} {response}")
                        
                        deliverable = code in [250, 251]
                        message = response.decode() if isinstance(response, bytes) else str(response)
                        
                        result = {
                            'deliverable': deliverable,
                            'smtp_code': code,
                            'smtp_message': message,
                            'port_used': port
                        }
                        
                        logger.debug(f"Deliverability test result for {email}: {deliverable}")
                        return result
                        
                except Exception as e:
                    logger.debug(f"Port {port} failed for deliverability test: {e}")
                    continue
            
            # If all ports failed
            return {
                'deliverable': False,
                'smtp_code': 550,
                'smtp_message': 'All SMTP ports failed for deliverability test'
            }
                
        except Exception as e:
            logger.debug(f"SMTP deliverability test failed for {email}: {e}")
            return {
                'deliverable': False,
                'smtp_code': 550,
                'smtp_message': f'SMTP error: {str(e)}'
            }
    
    def test_smtp_authentication(self, email: str, password: str) -> Dict:
        """Test SMTP authentication with comprehensive provider support"""
        logger.info(f"🔑 Testing SMTP authentication for: {email}")
        
        try:
            domain = email.split('@')[1].lower()
            
            # Comprehensive SMTP server configurations
            smtp_configs = {
                # Gmail
                'gmail.com': {'server': 'smtp.gmail.com', 'port': 587, 'use_tls': True},
                
                # Yahoo variations
                'yahoo.com': {'server': 'smtp.mail.yahoo.com', 'port': 587, 'use_tls': True},
                'yahoo.co.uk': {'server': 'smtp.mail.yahoo.com', 'port': 587, 'use_tls': True},
                'yahoo.co.jp': {'server': 'smtp.mail.yahoo.co.jp', 'port': 587, 'use_tls': True},
                'yahoo.ca': {'server': 'smtp.mail.yahoo.com', 'port': 587, 'use_tls': True},
                'yahoo.de': {'server': 'smtp.mail.yahoo.com', 'port': 587, 'use_tls': True},
                
                # Microsoft variations
                'hotmail.com': {'server': 'smtp-mail.outlook.com', 'port': 587, 'use_tls': True},
                'hotmail.co.uk': {'server': 'smtp-mail.outlook.com', 'port': 587, 'use_tls': True},
                'outlook.com': {'server': 'smtp-mail.outlook.com', 'port': 587, 'use_tls': True},
                'live.com': {'server': 'smtp-mail.outlook.com', 'port': 587, 'use_tls': True},
                'live.co.uk': {'server': 'smtp-mail.outlook.com', 'port': 587, 'use_tls': True},
                'msn.com': {'server': 'smtp-mail.outlook.com', 'port': 587, 'use_tls': True},
                
                # AOL
                'aol.com': {'server': 'smtp.aol.com', 'port': 587, 'use_tls': True},
                'aol.co.uk': {'server': 'smtp.aol.com', 'port': 587, 'use_tls': True},
                
                # Verizon
                'verizon.com': {'server': 'smtp.verizon.net', 'port': 587, 'use_tls': True},
                'verizon.net': {'server': 'smtp.verizon.net', 'port': 587, 'use_tls': True},
                
                # AT&T
                'att.com': {'server': 'outbound.att.net', 'port': 587, 'use_tls': True},
                'att.net': {'server': 'outbound.att.net', 'port': 587, 'use_tls': True},
                
                # Japanese providers
                'docomo.ne.jp': {'server': 'mail.docomo.ne.jp', 'port': 587, 'use_tls': True},
                'ezweb.ne.jp': {'server': 'mail.ezweb.ne.jp', 'port': 587, 'use_tls': True},
                'softbank.ne.jp': {'server': 'mail.softbank.ne.jp', 'port': 587, 'use_tls': True},
                'softbank.jp': {'server': 'mail.softbank.jp', 'port': 587, 'use_tls': True},
                'nifty.com': {'server': 'mail.nifty.com', 'port': 587, 'use_tls': True},
                'excite.co.jp': {'server': 'mail.excite.co.jp', 'port': 587, 'use_tls': True},
                
                # Chinese providers
                'qq.com': {'server': 'smtp.qq.com', 'port': 587, 'use_tls': True},
                'sina.com': {'server': 'smtp.sina.com', 'port': 587, 'use_tls': True},
                '126.com': {'server': 'smtp.126.com', 'port': 587, 'use_tls': True},
                '163.com': {'server': 'smtp.163.com', 'port': 587, 'use_tls': True},
                
                # Korean providers
                'naver.com': {'server': 'smtp.naver.com', 'port': 587, 'use_tls': True},
                'daum.net': {'server': 'smtp.daum.net', 'port': 587, 'use_tls': True},
                
                # European providers
                'web.de': {'server': 'smtp.web.de', 'port': 587, 'use_tls': True},
                'gmx.de': {'server': 'smtp.gmx.de', 'port': 587, 'use_tls': True},
                'gmx.com': {'server': 'smtp.gmx.com', 'port': 587, 'use_tls': True},
                'freenet.de': {'server': 'smtp.freenet.de', 'port': 587, 'use_tls': True},
                't-online.de': {'server': 'smtp.t-online.de', 'port': 587, 'use_tls': True},
                
                # Other major providers
                'mail.com': {'server': 'smtp.mail.com', 'port': 587, 'use_tls': True},
                'inbox.com': {'server': 'smtp.inbox.com', 'port': 587, 'use_tls': True},
                'zoho.com': {'server': 'smtp.zoho.com', 'port': 587, 'use_tls': True},
                'protonmail.com': {'server': 'smtp.protonmail.com', 'port': 587, 'use_tls': True},
            }
            
            # Get SMTP config or attempt discovery
            smtp_config = smtp_configs.get(domain)
            
            if not smtp_config:
                logger.debug(f"No predefined config for {domain}, attempting discovery")
                smtp_config = self._discover_smtp_server(domain)
            
            if not smtp_config:
                logger.warning(f"Could not find SMTP server for domain: {domain}")
                return {'authenticated': False, 'reason': f'No SMTP server found for domain: {domain}'}
            
            logger.debug(f"Using SMTP config for {domain}: {smtp_config}")
            
            # Test authentication with multiple methods
            auth_methods = [
                {'port': smtp_config['port'], 'use_tls': smtp_config.get('use_tls', False), 'use_ssl': False},
                {'port': 465, 'use_tls': False, 'use_ssl': True},  # SSL
                {'port': 587, 'use_tls': True, 'use_ssl': False},  # TLS
                {'port': 25, 'use_tls': False, 'use_ssl': False},  # Plain
            ]
            
            for method in auth_methods:
                try:
                    logger.debug(f"Trying authentication method: {method}")
                    
                    # Create SMTP connection
                    if method['use_ssl']:
                        server = smtplib.SMTP_SSL(smtp_config['server'], method['port'], timeout=self.timeout)
                    else:
                        server = smtplib.SMTP(smtp_config['server'], method['port'], timeout=self.timeout)
                    
                    # Start TLS if needed
                    if method['use_tls'] and not method['use_ssl']:
                        server.starttls()
                    
                    # Attempt authentication
                    logger.debug(f"Authenticating {email}")
                    server.login(email, password)
                    
                    # Authentication successful
                    logger.info(f"✅ AUTHENTICATION SUCCESS: {email}")
                    
                    # Send test email if recipient configured
                    test_email_sent = False
                    if TEST_EMAIL_RECIPIENT:
                        try:
                            test_email_sent = self._send_test_email(server, email, TEST_EMAIL_RECIPIENT)
                        except Exception as e:
                            logger.warning(f"Test email failed but auth succeeded: {e}")
                    
                    server.quit()
                    
                    return {
                        'authenticated': True,
                        'smtp_server': smtp_config['server'],
                        'method': method,
                        'test_email_sent': test_email_sent,
                        'reason': 'Authentication successful'
                    }
                    
                except smtplib.SMTPAuthenticationError as e:
                    logger.debug(f"Authentication failed with method {method}: {e}")
                    # For Gmail, provide specific guidance
                    if domain == 'gmail.com':
                        return {
                            'authenticated': False,
                            'reason': f'Gmail authentication failed: {str(e)}. Note: Gmail requires App Password for SMTP. Regular passwords won\'t work.'
                        }
                    continue
                except Exception as e:
                    logger.debug(f"Connection failed with method {method}: {e}")
                    continue
            
            # All methods failed
            logger.warning(f"All authentication methods failed for {email}")
            if domain == 'gmail.com':
                return {
                    'authenticated': False,
                    'reason': 'Gmail authentication failed: All methods failed. Gmail requires App Password for SMTP authentication.'
                }
            return {'authenticated': False, 'reason': 'All authentication methods failed'}
            
        except Exception as e:
            logger.error(f"Unexpected error testing {email}: {e}")
            return {'authenticated': False, 'reason': f'Unexpected error: {str(e)}'}
    
    def _discover_smtp_server(self, domain: str) -> Optional[Dict]:
        """Attempt to discover SMTP server for unknown domains"""
        possible_servers = [
            f'smtp.{domain}',
            f'mail.{domain}',
            f'smtp.mail.{domain}',
            f'send.{domain}',
            f'outbound.{domain}',
            f'mx.{domain}'
        ]
        
        ports_to_try = [587, 25, 465, 2525]
        
        for server in possible_servers:
            for port in ports_to_try:
                try:
                    logger.debug(f"Testing SMTP server discovery: {server}:{port}")
                    
                    # Test connection
                    sock = socket.create_connection((server, port), timeout=3)
                    sock.close()
                    
                    # If connection successful, return config
                    use_tls = port in [587, 2525]
                    smtp_config = {
                        'server': server,
                        'port': port,
                        'use_tls': use_tls
                    }
                    
                    logger.debug(f"Discovered SMTP server: {smtp_config}")
                    return smtp_config
                    
                except Exception:
                    continue
        
        return None
    
    def _send_test_email(self, server: smtplib.SMTP, from_email: str, to_email: str) -> bool:
        """Send test email through established SMTP connection"""
        try:
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = to_email
            msg['Subject'] = f"✅ Valid Email Verified - {from_email}"
            
            # Get country info for email
            country_info = "Unknown"
            try:
                # This would be populated from the geo_locator in the main validator
                country_info = "Detected during validation"
            except:
                pass
            
            body = f"""
🎉 EMAIL VALIDATION SUCCESS!

✅ Email: {from_email}
🔑 Authentication: PASSED
🌍 Country: {country_info}
📅 Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}
✉️ Status: VALID

This email confirms that {from_email} can successfully authenticate and send emails!

This message was sent by the Email Validator tool to verify working credentials.
"""
            
            msg.attach(MIMEText(body, 'plain'))
            server.send_message(msg)
            
            logger.info(f"📧 Test email sent from {from_email} to {to_email}")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to send test email: {e}")
            return False