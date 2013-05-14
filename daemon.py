#!/usr/bin/env python2.7
# Creadted by Adam Melton (.dok) referenceing https://bitmessage.org/wiki/API_Reference for API documentation
# Distributed under the MIT/X11 software license. See the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

# This is an example of a daemon client for PyBitmessage 0.3.0, by .dok (Version 0.1.2)


import ConfigParser
import xmlrpclib
import datetime
import hashlib
import getopt
import json
import time
import sys
import os

api = ''
keysPath = 'keys.dat'
usrPrompt = 0 #0 = First Start, 1 = prompt, 2 = no prompt if the program is starting up

#Begin keys.dat interactions
def lookupAppdataFolder(): #gets the appropriate folders for the .dat files depending on the OS. Taken from bitmessagemain.py
    APPNAME = "PyBitmessage"
    from os import path, environ
    if sys.platform == 'darwin':
        if "HOME" in environ:
            dataFolder = path.join(os.environ["HOME"], "Library/Application support/", APPNAME) + '/'
        else:
            print 'Could not find home folder, please report this message and your OS X version to the Daemon Github.'
            os.exit()

    elif 'win32' in sys.platform or 'win64' in sys.platform:
        dataFolder = path.join(environ['APPDATA'], APPNAME) + '\\'
    else:
        dataFolder = path.expanduser(path.join("~", "." + APPNAME + "/"))
    return dataFolder

def apiInit(apiEnabled):
    global keysPath
    config = ConfigParser.SafeConfigParser()
    config.read(keysPath)

    
    if (apiEnabled == False): #API information there but the api is disabled.
        uInput = raw_input("The API is not enabled. Would you like to do that now?(y/n):")

        if uInput == "y": #
            config.set('bitmessagesettings','apienabled','true') #Sets apienabled to true in keys.dat
            with open(keysPath, 'wb') as configfile:
                config.write(configfile)
                
            apiEnabled = config.getboolean('bitmessagesettings','apienabled') # Retrieves the value from the file.
            print 'Done'
            print ' '
            print '***********************************************************'
            print 'WARNING: If bitmessage is running, you must restart it now.'
            print '***********************************************************'
            print ' '
            
        elif uInput == "n":
            print ' '
            print '************************************************************'
            print 'daemon will not work when the API is disabled.'
            print 'Please refer to the Bitmessage Wiki on how to setup the API.'
            print '************************************************************'
            print ' '
            usrPrompt = 1
            main()
        else:
            print 'Invalid entry'
            usrPrompt = 1
            main()

    else: #API information was not present.
        print 'keys.dat not properly configured!'
        uInput = raw_input("Would you like to do this now?(y/n):")

        if uInput == "y": #User said yes, initalize the api by writing these values to the keys.dat file
            print '-----------------------------------'
            apiUsr = raw_input("API Username:")
            apiPwd = raw_input("API Password:")
            print '-----------------------------------'
                
            config.set('bitmessagesettings','apienabled','true')
            config.set('bitmessagesettings', 'apiport', '8444')
            config.set('bitmessagesettings', 'apiinterface', '127.0.0.1')
            config.set('bitmessagesettings', 'apiusername', apiUsr)
            config.set('bitmessagesettings', 'apipassword', apiPwd)
            with open(keysPath, 'wb') as configfile:
                config.write(configfile)
            
            print 'Finished configuring the keys.dat file with API information.'
            print ' '
            print '***********************************************************'
            print 'WARNING: If bitmessage is running, you must restart it now.'
            print '***********************************************************'
            print ' '
            
        elif uInput == "n":
            print ' '
            print '***********************************************************'
            print 'Please refer to the Bitmessage Wiki on how to setup the API.'
            print '***********************************************************'
            print ' '
            usrPrompt = 1
            main()
        else:
            print 'Invalid entry'
            usrPrompt = 1
            main()


def apiData():
    global keysPath
    
    config = ConfigParser.SafeConfigParser()
    keysPath = 'keys.dat'
    config.read(keysPath) #First try to load the config file (the keys.dat file) from the program directory

    try:
        config.get('bitmessagesettings','settingsversion')
        appDataFolder = ''
    except:
        #Could not load the keys.dat file in the program directory. Perhaps it is in the appdata directory.
        appDataFolder = lookupAppdataFolder()
        keysPath = appDataFolder + 'keys.dat'
        config = ConfigParser.SafeConfigParser()
        config.read(keysPath)

        try:
            config.get('bitmessagesettings','settingsversion')
        except:
            #keys.dat was not there either, something is wrong.
            print ' '
            print '******************************************************************'
            print 'There was a problem trying to access the Bitmessage keys.dat file.'
            print 'Make sure that daemon is in the same directory as Bitmessage.'
            print '******************************************************************'
            print ' '
            print config
            print ' '
            usrPrompt = 1
            main()

    try:
        apiConfigured = config.getboolean('bitmessagesettings','apienabled') #Look for 'apienabled'
        apiEnabled = apiConfigured
    except:
        apiConfigured = False #If not found, set to false since it still needs to be configured

    if (apiConfigured == False):#If the apienabled == false or is not present in the keys.dat file, notify the user and set it up
        apiInit(apiEnabled) #Initalize the keys.dat file with API information

    #keys.dat file was found or appropriately configured, allow information retrieval
    apiEnabled = config.getboolean('bitmessagesettings','apienabled')
    apiPort = config.getint('bitmessagesettings', 'apiport')
    apiInterface = config.get('bitmessagesettings', 'apiinterface')
    apiUsername = config.get('bitmessagesettings', 'apiusername')
    apiPassword = config.get('bitmessagesettings', 'apipassword')
            
    print 'API data successfully imported.'
    print ' '
    return "http://" + apiUsername + ":" + apiPassword + "@" + apiInterface+ ":" + str(apiPort) + "/" #Build the api credentials

def apiTest(): #Tests the API connection to bitmessage. Returns true if it is connected.
    if (api.add(2,3) == 5):
        return True
    else:
        return False

#End keys.dat interactions

ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

def decodeBase58(string, alphabet=ALPHABET): #Taken from addresses.py
    """Decode a Base X encoded string into the number

    Arguments:
    - `string`: The encoded string
    - `alphabet`: The alphabet to use for encoding
    """
    base = len(alphabet)
    strlen = len(string)
    num = 0

    try:
        power = strlen - 1
        for char in string:
            num += alphabet.index(char) * (base ** power)
            power -= 1
    except:
        #character not found (like a space character or a 0)
        return 0
    return num

def decodeAddress(address):
    #returns true if valid, false if not a valid address. - taken from addresses.py

    address = str(address).strip()

    if address[:3] == 'BM-':
        integer = decodeBase58(address[3:])
    else:
        integer = decodeBase58(address)
        
    if integer == 0:
        print 'invalidcharacters'
        return False
    #after converting to hex, the string will be prepended with a 0x and appended with a L
    hexdata = hex(integer)[2:-1]

    if len(hexdata) % 2 != 0:
        hexdata = '0' + hexdata

    #print 'hexdata', hexdata

    data = hexdata.decode('hex')
    checksum = data[-4:]

    sha = hashlib.new('sha512')
    sha.update(data[:-4])
    currentHash = sha.digest()
    #print 'sha after first hashing: ', sha.hexdigest()
    sha = hashlib.new('sha512')
    sha.update(currentHash)
    #print 'sha after second hashing: ', sha.hexdigest()

    if checksum != sha.digest()[0:4]:
        print 'checksumfailed'
        return False

    return True


def listAdd(): #Lists all of the addresses and their info
    jsonAddresses = json.loads(api.listAddresses())
    numAddresses = len(jsonAddresses['addresses']) #Number of addresses
    print ' '
    print 'Address Number,Label,Address,Stream,Enabled'
    print ' '

    for addNum in range (0, numAddresses): #processes all of the addresses and lists them out
        label = jsonAddresses['addresses'][addNum]['label']
        address = jsonAddresses['addresses'][addNum]['address']
        stream = jsonAddresses['addresses'][addNum]['stream']
        enabled = jsonAddresses['addresses'][addNum]['enabled']

        print addNum, label, address, stream, enabled

    print ' '

def genAdd(lbl,deterministic, passphrase, numOfAdd, addVNum, streamNum, ripe): #Generate address
    if deterministic == False: #Generates a new address with the user defined label. non-deterministic
        addressLabel = lbl.encode('base64')
        return api.createRandomAddress(addressLabel)
    
    elif deterministic == True: #Generates a new deterministic address with the user inputs.
        passphrase = passphrase.encode('base64')
        return api.createDeterministicAddresses(passphrase, numOfAdd, addVNum, streamNum, ripe)
    else:
        return 'Entry Error'

def sendMsg(toAddress, fromAddress, subject, message): #With no arguments sent, sendMsg fills in the blanks. subject and message must be encoded before they are passed.
    if (toAddress == ''):
        while True:
            toAddress = raw_input("To Address:")

            if (decodeAddress(toAddress)== False):
                print 'Invalid. "c" to cancel. Please try again.'
            else:
                break
        
        
    if (fromAddress == ''):
        jsonAddresses = json.loads(api.listAddresses())
        numAddresses = len(jsonAddresses['addresses']) #Number of addresses
        
        if (numAddresses > 1): #Ask what address to send from if multiple addresses
            labelOrAddress = 'label'
            while True:
                print ' '
                fromAddress = raw_input("Enter an Address or Address Label to send from:") # todo: add ability to type in label instead of full address

                if (labelOrAddress == 'label'):
                    for addNum in range (0, numAddresses): #processes all of the addresses
                        label = jsonAddresses['addresses'][addNum]['label']
                        address = jsonAddresses['addresses'][addNum]['address']
                        #stream = jsonAddresses['addresses'][addNum]['stream']
                        #enabled = jsonAddresses['addresses'][addNum]['enabled']
                        if (fromAddress == label): #address entered was a label and is found
                            fromAddress = address
                            labelOrAddress = 'label'
                            break
                        else:
                            labelOrAddress = 'address'
                    
                if (labelOrAddress == 'address'):
                    if (decodeAddress(fromAddress)== False):
                        print 'Invalid Address. Please try again.'
                    else: #Address was valid so use it
                        for addNum in range (0, numAddresses): #processes all of the addresses
                            #label = jsonAddresses['addresses'][addNum]['label']
                            address = jsonAddresses['addresses'][addNum]['address']
                            #stream = jsonAddresses['addresses'][addNum]['stream']
                            #enabled = jsonAddresses['addresses'][addNum]['enabled']
                            if (fromAddress == address): #address entered was a found in our addressbook.
                                labelOrAddress = 'address'
                                break
                            else:
                                print 'The address entered is not one of yours. Please try again.'
                                break
                else:
                    break #Address was the label :)
        
        else: #Only one address in address book
            print 'Using the only address in the addressbook to send from.'
            fromAddress = jsonAddresses['addresses'][0]['address']

    if (subject == ''):
            subject = raw_input("Subject:")
            subject = subject.encode('base64')
    if (message == ''):
            message = raw_input("Message:")
            message = message.encode('base64')

    ackData = api.sendMessage(toAddress, fromAddress, subject, message)
    print 'The ackData is: ', ackData #.decode("hex")
    print ' '


def sendBrd(fromAddress, subject, message): #sends a broadcast
    if (fromAddress == ''):
        jsonAddresses = json.loads(api.listAddresses())
        numAddresses = len(jsonAddresses['addresses']) #Number of addresses
        
        if (numAddresses > 1): #Ask what address to send from if multiple addresses
            labelOrAddress = 'label'
            while True:
                print ' '
                fromAddress = raw_input("Enter an Address or Address Label to send from:") # todo: add ability to type in label instead of full address

                if (labelOrAddress == 'label'):
                    for addNum in range (0, numAddresses): #processes all of the addresses
                        label = jsonAddresses['addresses'][addNum]['label']
                        address = jsonAddresses['addresses'][addNum]['address']
                        #stream = jsonAddresses['addresses'][addNum]['stream']
                        #enabled = jsonAddresses['addresses'][addNum]['enabled']
                        if (fromAddress == label): #address entered was a label and is found
                            fromAddress = address
                            labelOrAddress = 'label'
                            break
                        else:
                            labelOrAddress = 'address'
                    
                if (labelOrAddress == 'address'):
                    if (decodeAddress(fromAddress)== False):
                        print 'Invalid Address. Please try again.'
                    else: #Address was valid so use it
                        for addNum in range (0, numAddresses): #processes all of the addresses
                            #label = jsonAddresses['addresses'][addNum]['label']
                            address = jsonAddresses['addresses'][addNum]['address']
                            #stream = jsonAddresses['addresses'][addNum]['stream']
                            #enabled = jsonAddresses['addresses'][addNum]['enabled']
                            if (fromAddress == address): #address entered was a found in our addressbook.
                                labelOrAddress = 'address'
                                break
                            else:
                                print 'The address entered is not one of yours. Please try again.'
                                break
                else:
                    break #Address was the label :)
        
        else: #Only one address in address book
            print 'Using the only address in the addressbook to send from.'
            fromAddress = jsonAddresses['addresses'][0]['address']

    if (subject == ''):
            subject = raw_input("Subject:")
            subject = subject.encode('base64')
    if (message == ''):
            message = raw_input("Message:")
            message = message.encode('base64')

    ackData = api.sendBroadcast(fromAddress, subject, message)
    print 'The ackData is: ', ackData #.decode("hex")
    print ' '

def inbox(): #Lists the messages by: Message Number, To Address Label, From Address Label, Subject, Received Time)
    inboxMessages = json.loads(api.getAllInboxMessages())
    numMessages = len(inboxMessages['inboxMessages'])
    print ' '

    for msgNum in range (0, numMessages): #processes all of the messages in the inbox
        print '-----------------------------------'
        print ' '
        print 'Message Number:',msgNum #Message Number
        print 'To:', inboxMessages['inboxMessages'][msgNum]['toAddress'] #Get the to address
        print 'From:', inboxMessages['inboxMessages'][msgNum]['fromAddress'] #Get the from address
        print 'Subject:', inboxMessages['inboxMessages'][msgNum]['subject'].decode('base64') #Get the subject
        print datetime.datetime.fromtimestamp(float(inboxMessages['inboxMessages'][msgNum]['receivedTime'])).strftime('%Y-%m-%d %H:%M:%S')
        print ' '
    print 'There are ',numMessages,' messages in the inbox.'
    print '-----------------------------------'
    print ' '

def readMsg(msgNum): #Opens a message for reading
    
    inboxMessages = json.loads(api.getAllInboxMessages())
    print ' '
    print 'To:', inboxMessages['inboxMessages'][msgNum]['toAddress'] #Get the to address
    print 'From:', inboxMessages['inboxMessages'][msgNum]['fromAddress'] #Get the from address
    print 'Subject:', inboxMessages['inboxMessages'][msgNum]['subject'].decode('base64') #Get the subject
    print datetime.datetime.fromtimestamp(float(inboxMessages['inboxMessages'][msgNum]['receivedTime'])).strftime('%Y-%m-%d %H:%M:%S')
    print 'Message:'
    print inboxMessages['inboxMessages'][msgNum]['message'].decode('base64')

def replyMsg(msgNum): #Allows you to reply to the message you are currently on. Saves typing in the addresses and subject.

    inboxMessages = json.loads(api.getAllInboxMessages())
    
    fromAdd = inboxMessages['inboxMessages'][msgNum]['toAddress']#Address it was sent To, now the From address
    toAdd = inboxMessages['inboxMessages'][msgNum]['fromAddress'] #Address it was From, now the To address
    
    subject = inboxMessages['inboxMessages'][msgNum]['subject']
    subject = subject.decode('base64')
    subject = "Re: " + subject
    subject = subject.encode('base64')
    
    message = raw_input("Message:")
    message = message.encode('base64')

    sendMsg(toAdd, fromAdd, subject, message) 
    
    main()

def delMsg(msgNum): #Deletes a specified message from the inbox
    inboxMessages = json.loads(api.getAllInboxMessages())
    msgId = inboxMessages['inboxMessages'][int(msgNum)]['msgid'] #gets the message ID via the message index number
    return api.trashMessage(msgId)

def UI(usrInput): #Main user menu
    global usrPrompt
    
    if usrInput == "help" or usrInput == "h":
        print ' '
	print 'Possible Commands:'
	print '-----------------------------------'
	print 'help or h - This help file.'
	print 'apiTest - Tests the API'
	print 'exit - Exits the program'
	print '-----------------------------------'
	print 'listAddresses - Lists all of the users addresses'
	print 'generateAddress - Generates a new address'
	print '-----------------------------------'
	print 'sendMessage - Sends a message'
	print 'sendBroadcast - Sends a broadcast'
	print 'inbox - Lists the message information in the inbox'
	print 'open - Opens a message'
	print 'delete - Deletes a message'
	print '-----------------------------------'
	print ' '
	main()
        
    elif usrInput == "apiTest": #tests the API Connection.
	if (apiTest() == True):
            print 'API connection test has: PASSED'
        else:
            print 'API connection test has: FAILED'
            
	print ' '
        main()

    elif usrInput == "exit": #Exits the application
        print 'Bye'
        sys.exit()
        os.exit()
        
    elif usrInput == "listAddresses": #Lists all of the identities in the addressbook
        listAdd()
        main()
        
    elif usrInput == "generateAddress": #Generates a new address
        print ' '
        uInput = raw_input('Would you like to create a deterministic address?(y/n):')

        if uInput == "y": #Creates a deterministic address
            deterministic = True

            #lbl = raw_input('Label the new address:') #currently not possible via the api
            passphrase = raw_input('Passphrase:').encode('base64')
            numOfAdd = int(raw_input('Number of addresses to generate:'))
            addVNum = int(raw_input('Address version number (default "0"):'))
            streamNum = int(raw_input('Stream number (default "0"):'))
            isRipe = raw_input('Shorten the address?(y/n):')

            if isRipe == "y":
                ripe = True
                print genAdd(lbl,deterministic, passphrase, numOfAdd, addVNum, streamNum, ripe)
                main()
            elif isRipe == "n":
                ripe = False
                print genAdd(lbl,deterministic, passphrase, numOfAdd, addVNum, streamNum, ripe)
                main()
                
            else:
                print 'Invalid input'
                main()

            
        elif uInput == "n": #Creates a random address with user-defined label
            deterministic = False
            null = ''
            lbl = raw_input('Label the new address:')
            
            print genAdd(lbl,deterministic, null,null, null, null, null)
            main()
            
        else:
            print 'Invalid input'
            main()
        
    elif usrInput == "sendMessage": #Send Message
        null = ''
        sendMsg(null,null,null,null)
        
	main()
        
    elif usrInput == "sendBroadcast": #Send Broadcast from address
        null = ''
        sendBrd(null,null,null)
	main()
        
    elif usrInput == "inbox":
        inbox()
        main()
        
    elif usrInput == "open": #Opens a message from the inbox for viewing. 

        msgNum = int(raw_input("message number to open:"))

        readMsg(msgNum)

        print ' '
        uInput = raw_input("Would you like to reply to this message?(y/n):")#Gives the user the option to reply to the message

        if uInput == "y":
            replyMsg(msgNum)
            usrPrompt = 1
            main()
                
        elif uInput == "n":
            uInput = raw_input("Would you like to delete this message?(y/n):")#Gives the user the option to delete the message

            if uInput == "y":
                print 'Are you sure(y/n)?' #Prevent accidental deletion
                uInput = raw_input(">")

                if uInput == "y":
                    delMsg(msgNum)
                    print 'Done'
                    print ' '
                    usrPrompt = 1
                    main()
                else:
                    usrPrompt = 1
                    main()
            
            elif uInput == "n":
                usrPrompt = 1
                main()
            else:
                print 'Invalid entry'
                usrPrompt = 1
                main()
        else:
            print 'Invalid entry'
            usrPrompt = 1
            main()
        
    elif usrInput == "delete": #will delete a message from the system, not reflected on the UI.
        msgNum = int(raw_input("Message number to delete:"))
        uInput = raw_input("Are you sure?(y/n):")#Prevent accidental deletion

        if uInput == "y":
            delMsg(msgNum)
            print ' '
            print 'Notice: Message numbers may have changed.'
            print ' '
            main()
        else:
            usrPrompt = 1
            main()

	main()
        
    else:
	print 'unknown command'
	usrPrompt = 1
	main()
    
def main():
    global api
    global usrPrompt
    
    if (usrPrompt == 0):
        print 'Bitmessage daemon by .dok'
        api = xmlrpclib.ServerProxy(apiData()) #Connect to BitMessage using these api credentials    
        print ' '
        print 'Type "help" or "h" for a list of commands' #Startup message
        usrPrompt = 2
        
        #if (apiTest() == False):#Preform a connection test #taken out until I get the error handler working
        #    print '*************************************'
        #    print 'WARNING: No connection to Bitmessage.'
        #    print '*************************************'
        #    print ' '
    elif (usrPrompt == 1):
        print ' '
        print 'Type "help" or "h" for a list of commands' #Startup message
        usrPrompt = 2
        
    UI(raw_input('>'))
      
main()
