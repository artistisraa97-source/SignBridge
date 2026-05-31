import logging
import smtplib
import traceback
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Tuple

logger = logging.getLogger('signbridge.email')

SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USER = 'sammansedra2@gmail.com'
SMTP_PASS = 'eaxvvlpvkisncase'
FROM_EMAIL = SMTP_USER
USE_SSL = False


def render_verification_html(code: str) -> str:
    return f"""
    <html>
      <body style="font-family: Roboto, Poppins, Raleway, sans-serif; background:#fff; color:#333;">
        <div style="max-width:600px;margin:20px auto;padding:24px;border-radius:12px;border:1px solid #eee;background:#fff;">
          <h2 style="color:#ff7a00;margin:0 0 8px">SignBridge</h2>
          <p style="margin:0 0 16px">Thanks for creating an account. Use the code below to verify your email. It expires in 10 minutes.</p>
          <div style="font-size:28px;letter-spacing:6px;background:#f8f8f8;padding:12px 16px;border-radius:8px;display:inline-block;color:#ff7a00">{code}</div>
          <p style="margin-top:18px;color:#666">If you didn't request this, you can ignore this email.</p>
        </div>
      </body>
    </html>
    """


def compose_message(subject: str, to_email: str, html_body: str, from_email: str) -> MIMEMultipart:
    message = MIMEMultipart('alternative')
    message['Subject'] = subject
    message['From'] = from_email
    message['To'] = to_email
    message.attach(MIMEText(html_body, 'html'))
    return message


def send_smtp_email(message: MIMEMultipart) -> bool:
    try:
        smtp = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=20)
        smtp.starttls()
        smtp.login(SMTP_USER, SMTP_PASS)
        smtp.sendmail(message['From'], [message['To']], message.as_string())
        smtp.quit()
        return True
    except smtplib.SMTPAuthenticationError as exc:
        logger.error('SMTP authentication failed', exc_info=True)
        traceback.print_exc()
        return False
    except smtplib.SMTPException as exc:
        logger.error('SMTP error', exc_info=True)
        traceback.print_exc()
        return False
    except Exception as exc:
        logger.error('Unexpected email send error', exc_info=True)
        traceback.print_exc()
        return False


def send_verification_email(to_email: str, code: str) -> bool:
    subject = 'SignBridge Email Verification'
    html_body = render_verification_html(code)
    message = compose_message(subject, to_email, html_body, FROM_EMAIL)
    return send_smtp_email(message)
