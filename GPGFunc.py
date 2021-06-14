import gnupg

def decryptFile(confData):
    #C:\Users\xx\AppData\Roaming\gnupg
    gpg = gnupg.GPG(gnupghome=confData["gpgHome"])
    with open(confData["filePath"], 'rb') as f:
        status = gpg.decrypt_file(f, passphrase=confData["gpgKey"], output=confData["filePath"].strip(".asc"))
    return [status.ok, status.status]

