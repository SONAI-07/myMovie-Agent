import asyncio
import email
from email.header import decode_header
import imaplib
import logging
import re
from typing import Any, Dict, List, Optional

from agent.infra_agent import run_pipeline
from app.config import get_settings
from app.database import save_recommendation
from app.services.bms_html_parser import extract_movie_from_bms_email

logger = logging.getLogger("bingeWatch.gmail")


def clean_header(header_val: Optional[str]) -> str:
    """Decodes email header parts to a clean string."""
    if not header_val:
        return ""
    decoded_parts = decode_header(header_val)
    result = []
    for part, enc in decoded_parts:
        if isinstance(part, bytes):
            result.append(part.decode(enc or "utf-8", errors="ignore"))
        else:
            result.append(str(part))
    return "".join(result).strip()


class GmailWatcher:
    def __init__(self):
        self.settings = get_settings()
        self._running = False
        self._task: Optional[asyncio.Task] = None

    @property
    def is_configured(self) -> bool:
        return bool(self.settings.gmail_user and self.settings.gmail_app_password)

    def connect(self) -> imaplib.IMAP4_SSL:
        """Connects to Gmail IMAP server using SSL."""
        if not self.is_configured:
            raise ValueError("GMAIL_USER and GMAIL_APP_PASSWORD are not configured in settings/.env")

        mail = imaplib.IMAP4_SSL(self.settings.gmail_imap_server, self.settings.gmail_imap_port)
        mail.login(self.settings.gmail_user, self.settings.gmail_app_password)
        return mail

    async def check_and_process_emails(self) -> List[Dict[str, Any]]:
        """
        Polls Gmail for unread BookMyShow emails, extracts movie tickets,
        triggers the agent pipeline, and stores recommendations in the database.
        """
        if not self.is_configured:
            logger.info("Gmail watcher not active: credentials not set.")
            return []

        logger.info("🔍 Checking Gmail for unread BookMyShow ticket emails...")
        processed = []

        # Run synchronous IMAP operations in threadpool to keep event loop responsive
        loop = asyncio.get_running_loop()

        def fetch_unseen() -> List[Dict[str, str]]:
            emails_data = []
            try:
                mail = self.connect()
                mail.select("INBOX")

                # Search unread emails from bookmyshow or subject ticket
                search_queries = [
                    '(UNSEEN FROM "bookmyshow.com")',
                    '(UNSEEN FROM "bookmyshow")',
                    '(UNSEEN SUBJECT "BookMyShow")'
                ]

                all_msg_ids = set()
                for query in search_queries:
                    status, messages = mail.search(None, query)
                    if status == "OK" and messages[0]:
                        all_msg_ids.update(messages[0].split())

                for msg_id in all_msg_ids:
                    status, data = mail.fetch(msg_id, "(RFC822)")
                    if status != "OK":
                        continue

                    raw_email = data[0][1]
                    msg = email.message_from_bytes(raw_email)

                    subject = clean_header(msg.get("Subject", ""))
                    sender = clean_header(msg.get("From", ""))

                    # Extract body content
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            if content_type in ["text/plain", "text/html"]:
                                try:
                                    body += part.get_payload(decode=True).decode("utf-8", errors="ignore")
                                except Exception:
                                    pass
                    else:
                        try:
                            body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
                        except Exception:
                            pass

                    movie = extract_movie_from_bms_email(subject, body)
                    if movie:
                        emails_data.append({"movie": movie, "subject": subject, "sender": sender})
                        # Mark email as read/seen
                        mail.store(msg_id, "+FLAGS", "\\Seen")

                mail.close()
                mail.logout()
            except Exception as e:
                logger.error("Error reading Gmail: %s", e)

            return emails_data

        unseen_emails = await loop.run_in_executor(None, fetch_unseen)

        for item in unseen_emails:
            movie = item["movie"]
            logger.info("🎟️ Detected BookMyShow ticket for movie: '%s'. Triggering agent pipeline...", movie)
            result = await run_pipeline(movie)
            saved = save_recommendation(movie, result, source="gmail")
            processed.append(saved)

        return processed

    async def simulate_incoming_ticket(self, movie_name: str) -> Dict[str, Any]:
        """
        Simulates an incoming BookMyShow confirmation email for testing or quick ingestion.
        """
        logger.info("Simulating BookMyShow email ticket arrival for '%s'", movie_name)
        result = await run_pipeline(movie_name)
        saved = save_recommendation(movie_name, result, source="gmail-simulated")
        return saved

    async def start_loop(self):
        """Background monitoring loop."""
        self._running = True
        logger.info("Gmail watcher background daemon started.")
        while self._running:
            try:
                if self.is_configured:
                    await self.check_and_process_emails()
            except Exception as e:
                logger.error("Unexpected error in Gmail watcher loop: %s", e)
            await asyncio.sleep(self.settings.gmail_check_interval)

    def stop_loop(self):
        self._running = False
        if self._task:
            self._task.cancel()


gmail_watcher = GmailWatcher()
