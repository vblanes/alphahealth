import hashlib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import ssl

logging.basicConfig(level=logging.INFO)

'''
Refactored to be a general utils class
MD5 was moved here in order to be more general
'''


def md5(id_user):
    """
    Hashes id_user usign MD5. Ensures anonimity.
    """
    return hashlib.md5(str(id_user).encode('utf-8')).hexdigest()


def send_mail(sender, receivers, subject, body, smtp_server, smtp_port, password):
    # Create the container (outer) email message.
    msg = MIMEMultipart()
    msg['Subject'] = subject
    # me == the sender's email address
    # family = the list of all recipients' email addresses
    msg['From'] = sender
    msg['To'] = ', '.join(receivers)
    # convert the body to a MIME compatible string
    body = MIMEText(body)
    msg.attach(body)

    context = ssl.create_default_context()
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.ehlo()
        # Secure the connection
        server.starttls(context=context)
        server.ehlo()
        server.login(sender, password)
        server.sendmail(sender, receivers, msg.as_string())
        server.quit()
    except Exception as e:
        logging.error(e)
        logging.error('Error sending mail')
