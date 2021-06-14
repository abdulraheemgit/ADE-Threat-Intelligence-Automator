from __future__ import print_function
import requests
import lxml
from datetime import datetime, timedelta
from lxml import html
from time import sleep
import warnings
import urllib3
import getpass
import fileFunc
import GPGFunc
import sendFiles


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)                         #disabling ssl certification warnings
fileFunc.copyRights()
print ("Reading configuration... ", end='')
try:
    confData = fileFunc.readConf()
    print ("done!")
except:
    print ("Error in configuration file")
    raw_input("Hit enter to exit the program")
    exit()

result = ""
loginErr = []
fileDict = {}
payload = {                                                 #prepare the post data
	"team_name": "<set it in the config file or during the run>", 
	"password": "<set it in the config file or during the run>",        
	"csrfmiddlewaretoken": "<CSRF_TOKEN>"
}

session_requests = requests.session()
retry = 0
while result == '' and retry<5:                             #requesting session
    result = session_requests.get(confData["homeUrl"], verify=False)
    try:
        result = session_requests.get(confData["homeUrl"], verify=False)
    except:
        print("Try again in 3 seconds...")
        retry += 1
        sleep(3)
        continue
if not result:
    print ("error in connecting")
    raw_input("Hit enter to exit the program")
    exit()

print ("obtaining csrf token... ", end='')
    
try:
    tree = html.fromstring(result.content)                  #Getting the result
    csrfToken = list(set(tree.xpath("//input[@name='csrfmiddlewaretoken']/@value")))[0]     #get the csrf token from the result
    payload["csrfmiddlewaretoken"] = csrfToken                                              #assigning it to payload
    print ("success - "+csrfToken)
except:
    print ("failed! \nlooks like cannot find csrf token...")
    raw_input("Hit enter to exit the program")
    exit()

print ("if you have set the credentials in config file, leave this blank.")
username = raw_input("enter ADE username: ")


if not username:                                            #set username and password either from config file or user input
    payload["team_name"] = confData["usernameADE"]          #set from config
    print ("Username was set from the config file - "+confData["usernameADE"])
else:
    payload["team_name"] = username                         #set from user input
##if not password:
##    payload["password"] = confData["passwordADE"]
payload["password"] = getpass.getpass("enter ADE password: ")
    
print ("attempting to login... ", end='')
result = session_requests.post(confData["loginUrl"], data = payload, headers = dict(referer=confData["loginUrl"]))  #login to the site with payload
tree = html.fromstring(result.content)
loginErr = tree.xpath("//div[@class='alert alert-error']/@id")                              #capture login error

retry = 0
while loginErr and retry<5:                                 #retry 5 times if login failed
    loginErr = ''
    result = session_requests.post(confData["loginUrl"], data = payload, headers = dict(referer=confData["loginUrl"]))
    tree = html.fromstring(result.content)
    loginErr = tree.xpath("//div[@class='alert alert-error']/@id")   
    retry += 1

if loginErr or "Login to DATA Exchanger of APCERT" in str(result.content):
    print ("login failed\n")
    raw_input("Hit enter to exit the program")
    exit()
print ("success!")

result = session_requests.post(                             #get unread alerts
	confData["ScrapUrl"],
        data = {"csrfmiddlewaretoken": csrfToken},
	headers = dict(referer = confData["ScrapUrl"])
)
print ("spidering the website...\n")
tree = html.fromstring(result.content)
fileId = list(set(tree.xpath("//tr[@class='info']")))
##confData["filePath"] = "Downloads/2017-12-21/e94af8fb-8553-4919-a59e-6dd22b3e5bd7-2017-12-20.csv"       #test file
i = 0
x = 0
dataType = ''
filePath = []
newFile = False
confData["gpgKey"] = ''
for files in fileId:
    row = html.fromstring(str(files))    
    fileName = files.xpath("//input[@name='fileid']/@value")[i]                             #get the file id
    date = files.xpath("//td/text()")[x].split(",")                                         #get the file date
    dataType = files.xpath("//td/text()")[x+1].strip()                                      #get the data type
    i+=1; x+=6
    chngDate = datetime.strptime(str(''.join(date[0:2])), '%b %d %Y').strftime('%Y-%m-%d')  #converts the file date to python date format
    fileDate = datetime.strptime(chngDate, '%Y-%m-%d')
    if datetime.now() - timedelta(days=int(confData["latestDays"])) <= fileDate:            #check the file date if its the leatest
        newFile = True
        fileDict[fileName] = fileDate
        confData["fileName"] = fileName
        confData["fileDate"] = fileDate
        confData["dataType"] = dataType
        
        if 'phishing' in dataType:continue                  #skip phishing files
        else: flag = fileFunc.download(confData)            #downloading the file
        
        if flag[0] == 1:
            if not confData["gpgKey"]:
                confData["gpgKey"] = getpass.getpass("Enter GPG key to decrypt file : ")                
            print ("decrypting downloaded file... ", end='')
            confData["filePath"] = flag[1]
            filePath.append(flag[1].strip(".asc"))
            if GPGFunc.decryptFile(confData)[0]:            #decrypting the file
                print ("done!")
                print ("deleting downloaded file... ", end='')
                if fileFunc.deleteFile(confData):           #deleting the downloaded file
                    confData["filePath"] = flag[1].strip(".asc")
                    print ("done!\n")
                else:
                    print ("failed!")
                    print ("cannot delete file. please delete it manually.")            
            else:
                print ("failed!")
                raw_input("press enter to exit the program")
                exit()
    else:
        continue
if not newFile:
    print ("no new files to download")
else:
    print ("note : files older than "+confData["latestDays"]+" days were not downloaded\n")
    results = fileFunc.createFile(confData, filePath)    
    sendFrom = confData['username']
    subject = confData['subject']                                                           #email subject
    msgBody = ""    
    server = confData['mailServer']                                                         #mail server
    port = confData['port']
    username = confData['username']                                                         #email
    password = confData['password']
    dataFile = ''
    sentMailStatus = {}
    isp = results[0]                                        #{isp : [totalcount,contact,email,file path]}
    ipIsp = results[1]                                      #{ip : [subnet,isp,found/notfound, datacount]}
    unknownIp = results[2]                                  #unknown ip for report generation

    print ("change the email body (in emailBody.txt) before sending the email!")
    send = raw_input("proceed and send emails (y/n) ")
    print ("")
    if send.upper() == 'Y':     
         for ispKey,items in isp.iteritems():         
             to = []
             cc = []
             bcc = []
             msgBody = ""
             toMails = items[2].split(',')
             dataFile = items[3]
             if items[0] > 0:
                 if toMails[0].upper() == "NONE" and len(toMails)<2:                        #check for contact email availability
                     sentMailStatus[ispKey] = ['Not sent','No email(s) found']            
                     continue
                 else:
                     to.append(items[2].split(',')[0])                                      #set to email addresses
                     for mail in items[2].split(','):
                         if items[2].index(mail) == 0:
                             continue
                         else:
                             cc.append(mail)                      
                     if confData['cc'].strip():                                             #set cc email addresses
                         for mail1 in confData['cc'].split(','):
                             cc.append(mail1)
                     if confData['bcc'].strip():
                         for mail2 in confData['bcc'].split(','):                           #set bcc email addresses
                             bcc.append(mail2)
                             
                 name = items[1].split()[0]
                 with open(confData['emailBody'], "rb") as f:                               #set email body
                     for line in f.readlines():
                         if line.startswith('//'):
                             continue
                         flag = line.strip().upper()                
                         if flag == 'HI':
                             msgBody += line.strip("\r\n") + " " + name+"\n"
                         else:
                             msgBody += line
                     f.close()
                 
                 result = sendFiles.sendMail(username, password, to, cc, bcc, subject, msgBody, server, port, dataFile)          #send email   
                 sentMailStatus[ispKey] = result
         print ('file sending completed!\n')
    else:
         for ispKey,items in isp.iteritems():                                            
             result = ['Not sent','Denied by the user']
             sentMailStatus[ispKey] = result
    print ('generating reports.')
    try:
         fileFunc.generateReport(isp, ipIsp, unknownIp, sentMailStatus, confData)           #generating reports
         print ('Report successfully generated\n')
    except:
        print ("error in generating report")
        raw_input("please close all the opened files and try again")

raw_input("press enter to exit the program")
