import smtplib
import socket
import time
import random
from typing import Dict, Optional
from config import SMTP_TIMEOUT, SMTP_PORT
from utils.logger import setup_logger

logger = setup_logger(__name__)

class SMTPChecker:
    def __init__(self):
        self.timeout = 3
        
    def check_smtp_connection(self, mx_server: str) -> Dict:
        """Real SMTP connection test with actual network calls"""
        logger.debug(f"Testing SMTP: {mx_server}")
        
        # Try multiple ports in order of preference
        ports_to_try = [25, 587, 465, 2525]
        
        for port in ports_to_try:
            try:
                # Actual socket connection test
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(self.timeout)
                result = sock.connect_ex((mx_server, port))
                sock.close()
                
                if result == 0:  # Connection successful
                    logger.debug(f"SMTP port {port} open on {mx_server}")
                    return {
                        'smtp_valid': True,
                        'smtp_response': f'Port {port} accessible',
                        'server': mx_server
                    }
                    
            except Exception as e:
                logger.debug(f"Port {port} failed on {mx_server}: {str(e)}")
                continue
        
        # All ports failed
        logger.debug(f"All SMTP ports failed for {mx_server}")
        return {
            'smtp_valid': False,
            'smtp_response': 'No accessible SMTP ports',
            'server': mx_server
        }
    
    def verify_email_deliverability(self, email: str, mx_server: str) -> Dict:
        """Real deliverability test with actual SMTP conversation"""
        domain = email.split('@')[1].lower()
        
        try:
            # Real SMTP conversation
            server = smtplib.SMTP(timeout=self.timeout)
            server.connect(mx_server, 25)
            server.helo('validator.test')
            
            # Try MAIL FROM
            code, response = server.mail('test@validator.com')
            if code not in [250, 251]:
                server.quit()
                return {
                    'deliverable': False,
                    'smtp_code': code,
                    'smtp_message': response.decode() if isinstance(response, bytes) else str(response)
                }
            
            # Try RCPT TO
            code, response = server.rcpt(email)
            server.quit()
            
            # 250 = accepted, 251 = will forward, 550 = rejected, 553 = invalid
            deliverable = code in [250, 251]
            
            return {
                'deliverable': deliverable,
                'smtp_code': code,
                'smtp_message': response.decode() if isinstance(response, bytes) else str(response)
            }
            
        except smtplib.SMTPConnectError:
            return {
                'deliverable': False,
                'smtp_code': 421,
                'smtp_message': 'SMTP connection refused'
            }
        except smtplib.SMTPServerDisconnected:
            return {
                'deliverable': False,
                'smtp_code': 421,
                'smtp_message': 'SMTP server disconnected'
            }
        except socket.timeout:
            return {
                'deliverable': False,
                'smtp_code': 421,
                'smtp_message': 'SMTP timeout'
            }
        except Exception as e:
            return {
                'deliverable': False,
                'smtp_code': 550,
                'smtp_message': f'SMTP error: {str(e)}'
            }