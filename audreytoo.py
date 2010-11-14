#! /usr/bin/env python
#
# Audreytoo
#
# A simple script to pick a random photo from a directory and email it to a group of
# people. See http://micropipes.com/blog/2009/07/20/automating-thinking-of-you/
#
# @author Wil Clouser <clouserw@gmail.com>

from datetime import date
import os
import random
import smtplib
import sys

from email.MIMEImage import MIMEImage
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

# Email address that will be notified about any problems or when you've got less than 10 photos remaining
ADMIN = ""

# From email address
FROM = ""

# List of To email addresses
TO   = []

# List of file extensions that are valid
VALID_FILES = ['.jpg', '.png']

# SMTP server stuff.  If you don't need this you can just remove all the vars and
# delete the s.login() lines.
SMTP_SERVER = ''
SMTP_USER = ''
SMTP_PASS = ''

def mail_admin(subject,body=''):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = FROM
    msg['To'] = ADMIN

    s = smtplib.SMTP(SMTP_SERVER)
    s.login(SMTP_USER,SMTP_PASS)
    s.sendmail(FROM, [ADMIN], msg.as_string())
    s.close()

def main():

    if not len(sys.argv) == 2:
        print >> sys.stderr, "Usage: ./audreytoo.py /path/to/images/"
        sys.exit(1)

    image_directory = sys.argv[1]

    if not os.path.isdir(image_directory):
        print >> sys.stderr, "%s is not readable.  Aborting." % (image_directory)
        sys.exit(1)

    today = date.today()

    # Build Message
    outer = MIMEMultipart()
    outer['Subject'] = 'Picture of the week: %s Edition' % today.strftime("%B %d")
    outer['To'] = ", ".join(TO)
    outer['From'] = FROM
    outer.preamble = 'Picture of the week: %s Edition\n' % today.strftime("%B %d")
    # To guarantee the message ends with a newline.  I stole this from somewhere on the net.
    outer.epilogue = ''

    highpriority = []
    lowpriority = []

    for filename in os.listdir(image_directory):
        if not os.path.isfile(os.path.join(image_directory, filename)) or os.path.splitext(filename)[1].lower() not in VALID_FILES:
            continue

        # If the file starts with next-, we'll send that right away.  note that
        # next-01 is a higher priority than next-02, etc.
        if filename.startswith('next-'):
            highpriority.append(filename)
        else:
            lowpriority.append(filename)

    if not len(highpriority) and not len(lowpriority):
        mail_admin("You're all out of pictures. :(")
        sys.exit(1)

    if len(highpriority):
        highpriority.sort()
        filename = highpriority.pop(0)
    else:
        filename = random.choice(lowpriority)

    try:
        path = os.path.join(image_directory, filename)
        fp = open(path, 'rb')
        msg = MIMEImage(fp.read())
        fp.close()

        # Set the filename parameter
        msg.add_header('Content-Disposition', 'attachment', filename=filename)
        outer.attach(msg)

        # Now send the message
        s = smtplib.SMTP(SMTP_SERVER)
        s.login(SMTP_USER,SMTP_PASS)
        s.sendmail(FROM, TO, outer.as_string())
        s.close()

        os.remove(path)

        total_remaining = len(highpriority) + len(lowpriority) - 1
        if total_remaining < 10:
            # Total number of pictures is less than 10, give ADMIN a heads up
            mail_admin("Only %s pictures left in the pool" % (total_remaining), "Need more pictures!")
    except:
        mail_admin("Something is broken!", "Output:\n\n%s" % (sys.exc_info()[0]))

if __name__ == '__main__':
    main()
