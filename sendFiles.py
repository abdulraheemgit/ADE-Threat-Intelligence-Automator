from __future__ import print_function
import smtplib
import itertools, sys, time, copy, os
from os.path import basename
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate

def sendMail(username, password, to, cc, bcc, subject, msgBody, serverIP, port, files=None):
    status = ''
    reply = ''
    server = None
    msg = MIMEMultipart()
    msg['From'] = username                                              #set the mail headers
    msg['To'] = to[0]
    msg['CC'] = ", ".join(cc)
    msg['BCC'] = ", ".join(bcc)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject
    msg.attach(MIMEText(msgBody))
    
    for root, subdirs, files1 in os.walk(files):    
        for filename in files1:
            with open(files+'/'+filename, "rb") as fil:                 #attacching the files
                part = MIMEApplication(fil.read(),Name=basename(filename))
            # After the file is closed
            part['Content-Disposition'] = 'attachment; filename="%s"' % basename(filename)
            msg.attach(part)
            print ('attaching file '+ basename(filename)+"...")
    print ('sending file(s) to '+to[0]+"... ", end='')
    try:
        server = smtplib.SMTP(serverIP, int(port))                      #connecting to mail server
        server.starttls()
        server.login(username,password)                 
        server.sendmail(username, to+cc+bcc , msg.as_string())          #sending email
        print ('done!\n')
        status = 'Sent' 
        reply = 'Email successfully sent'
        server.quit()
    except (smtplib.SMTPException):
        print ('failed...')
        status = 'Not sent'
        reply = 'Error in sending emails'
    return [status, reply]
