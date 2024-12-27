"""
The main sender module, this does the whole job of fetch, generate, email.
If configs are not up to snuff, it will yell at you to use  GUI.Py for first.
To automate this, you'll need to create a cron job, or a Windows schedule, or whatever your OS uses.
"""
import os
import sys
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import date

from feedhandler import FeedHandler
from generator import EpubGenerator
from logger import _setup_logger

def main():
    """
    Generate an EPUB file from RSS feeds and send it via email.

    Steps:
        1. Verify configuration files exist; if not, prompt the user to create them.
        2. Use configuration settings to generate an EPUB newspaper.
        3. Email the generated EPUB file to the specified recipient.

    Raises:
        SystemExit: If any critical error occurs during execution.
    """
    logger = _setup_logger("Sender")
    settings_path = "configs/settings.json"
    os.makedirs("configs", exist_ok=True)

    # Verify settings.json exists and is valid
    if not os.path.isfile(settings_path):
        logger.error("Settings file not found")
        print("Please run the GUI to configure settings first")
        sys.exit(1)

    with open(settings_path, 'r', encoding='utf-8') as f:
        try:
            settings = json.load(f)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse settings.json: %s", e)
            print("Error in settings.json. Please run the GUI to configure settings again.")
            sys.exit(1)

    # Verify feeds.json exists and create if necessary
    feeds_path = "configs/feeds.json"
    if not os.path.isfile(feeds_path):
        with open(feeds_path, 'w', encoding='utf-8') as f:
            json.dump([], f)
        logger.error("Feeds file not found")
        print("Please run the GUI to configure settings first")
        sys.exit(1)

    handler = FeedHandler(feeds_path)
    generator = EpubGenerator()
    output_file = f"newspapers/newspaper_{date.today().isoformat()}.epub"

    os.makedirs("newspapers", exist_ok=True)

    # Generate the EPUB file
    try:
        generator.generate_epub(
            feeds=handler.feeds_data,
            handler=handler,
            output_file=output_file,
            article_type=settings['article_type']
        )
    # pylint: disable=broad-exception-caught
    except Exception as e:
        logger.error("Failed to generate EPUB: %s", e)
        print("Error generating EPUB. Please check the logs for details.")
        sys.exit(1)

    if not os.path.exists(output_file):
        logger.error("Generated EPUB file not found")
        print("Generated EPUB file not found. Please check the logs for details.")
        sys.exit(1)

    # Send the EPUB via email
    try:
        msg = MIMEMultipart()
        msg['Subject'] = f'Your Daily EPUB Newspaper - {date.today().isoformat()}'
        msg['From'] = settings['smtp_username']
        msg['To'] = settings['target_email']

        with open(output_file, 'rb') as f:
            attachment = MIMEApplication(f.read(), _subtype='epub')
            attachment.add_header(
                'Content-Disposition',
                'attachment',
                filename=os.path.basename(output_file)
            )
            msg.attach(attachment)

        try:
            with smtplib.SMTP(settings['smtp_server'], settings['smtp_port']) as smtp:
                smtp.starttls()
                smtp.login(settings['smtp_username'], settings['smtp_password'].strip())
                smtp.send_message(msg)

            logger.info("EPUB sent successfully via email")
        except (smtplib.SMTPException, ConnectionError) as e:
            logger.error("SMTP connection failed: %s", e)
            print("Error sending email. Please verify your SMTP settings in the GUI and try again.")
            sys.exit(1)
    # pylint: disable=broad-exception-caught
    except Exception as e:
        logger.error("Failed to send email: %s", e)
        print("Failed to send email. Please check the logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
