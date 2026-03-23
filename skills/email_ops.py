import os
import json
import imaplib
import email
from typing import List, Dict, Any, Callable
from core.skill import Skill

class EmailSkill(Skill):
    """Skill for checking emails via IMAP."""
    
    def __init__(self):
        self.email_address = os.environ.get("EMAIL_ADDRESS")
        self.email_password = os.environ.get("EMAIL_PASSWORD")
        self.imap_server = os.environ.get("EMAIL_IMAP_SERVER", "imap.gmail.com")
    
    @property
    def name(self) -> str:
        return "email_skill"

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "check_unread_emails",
                    "description": "Check the number of unread emails in the inbox",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_recent_emails",
                    "description": "Get subject lines and senders of recent emails",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "count": {
                                "type": "integer",
                                "description": "Number of recent emails to fetch (default: 5)"
                            }
                        },
                        "required": []
                    }
                }
            }
        ]

    def get_functions(self) -> Dict[str, Callable]:
        return {
            "check_unread_emails": self.check_unread_emails,
            "get_recent_emails": self.get_recent_emails
        }

    def _connect_imap(self):
        """Connect to IMAP server and return mail object."""
        if not self.email_address or not self.email_password:
            raise ValueError("Email credentials not configured. Please add EMAIL_ADDRESS and EMAIL_PASSWORD to .env file.")
        
        mail = imaplib.IMAP4_SSL(self.imap_server)
        mail.login(self.email_address, self.email_password)
        return mail

    def check_unread_emails(self) -> str:
        """
        Check the number of unread emails.
        
        Returns:
            JSON string with unread count
        """
        try:
            mail = self._connect_imap()
            mail.select('inbox')
            
            # Search for unread emails
            status, messages = mail.search(None, 'UNSEEN')
            
            if status == 'OK':
                unread_ids = messages[0].split()
                unread_count = len(unread_ids)
                
                mail.close()
                mail.logout()
                
                return json.dumps({
                    "status": "success",
                    "unread_count": unread_count,
                    "message": f"You have {unread_count} unread email(s)"
                })
            else:
                mail.logout()
                return json.dumps({
                    "status": "error",
                    "message": "Failed to check emails"
                })
                
        except ValueError as e:
            return json.dumps({
                "status": "error",
                "message": str(e)
            })
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Email check error: {str(e)}"
            })

    def get_recent_emails(self, count: int = 5) -> str:
        """
        Fetch recent emails with subject and sender.
        
        Args:
            count: Number of emails to fetch
            
        Returns:
            JSON string with email list
        """
        try:
            mail = self._connect_imap()
            mail.select('inbox')
            
            # Get all emails
            status, messages = mail.search(None, 'ALL')
            
            if status != 'OK':
                mail.logout()
                return json.dumps({
                    "status": "error",
                    "message": "Failed to fetch emails"
                })
            
            email_ids = messages[0].split()
            
            # Get the last N emails
            recent_ids = email_ids[-count:] if len(email_ids) >= count else email_ids
            recent_ids = reversed(recent_ids)  # Most recent first
            
            emails = []
            
            for email_id in recent_ids:
                status, msg_data = mail.fetch(email_id, '(RFC822)')
                
                if status == 'OK':
                    email_body = msg_data[0][1]
                    message = email.message_from_bytes(email_body)
                    
                    subject = message['subject']
                    sender = message['from']
                    
                    # Decode subject if needed
                    if subject:
                        decoded_subject = email.header.decode_header(subject)[0]
                        if isinstance(decoded_subject[0], bytes):
                            subject = decoded_subject[0].decode(decoded_subject[1] or 'utf-8')
                        else:
                            subject = decoded_subject[0]
                    
                    emails.append({
                        "from": sender,
                        "subject": subject or "(No Subject)"
                    })
            
            mail.close()
            mail.logout()
            
            return json.dumps({
                "status": "success",
                "count": len(emails),
                "emails": emails
            })
            
        except ValueError as e:
            return json.dumps({
                "status": "error",
                "message": str(e)
            })
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Error fetching emails: {str(e)}"
            })
