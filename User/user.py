import os
from os import path
import socket                               # Import socket module

"""

Notes
==============

socket.gethostname() gets the current machines hostname, for example "DESKTOP-1337PBJ"

string.encode('UTF-8') encodes the given string into a 'bytes' literal object using the UTF-8 standard that is required
bytes.decode("UTF-8") decodes some 'bytes' literal object using the UTF-8 standard that information gets sent over the internet in

all the b'string here' are converting a string into binary format. Hence the B

"""

connected = False
socketObject = socket.socket()              # Create a socket object
# host = socket.gethostname()
# host = "localhost"                          # Get local machine name
# port = 60000                                # Reserve a port for your service.
bufferSize = 1024


def SendPayload(socketBoi, toSend: str):
    payload = "".join([toSend, "\0"])
    socketBoi.send(payload.encode("UTF-8"))
def RecvPayload(socketBoi):
    global bufferSize

    returnString = ""
    reachedEOF = False

    while not reachedEOF:
        # Receiving data in 1 KB chunks
        data = socketBoi.recv(bufferSize)
        if(not data):
            reachedEOF = True
            break

        # If there was no data in the latest chunk, then break out of our loop
        decodedString = data.decode("UTF-8")
        if(len(decodedString) >= 2 and decodedString[len(decodedString) - 1: len(decodedString)] == "\0"):
            reachedEOF = True
            decodedString = decodedString[0:len(decodedString) - 1]

        returnString += decodedString
    
    return returnString

# Connect to a central server
def Connect(address, port: int):
    global connected
    global socketObject
    global bufferSize

    try:
        socketObject.connect((address, int(port)))

        # data = socketObject.recv(bufferSize)
        # connectionStatus = data.decode("UTF-8")
        connectionStatus = RecvPayload(socketObject)
        
        # Make sure we were accepted (server hasn't hit limit)
        print("ConnectionStatus: ", connectionStatus)
        if(int(connectionStatus) != 200):
            raise ConnectionRefusedError
        else:
            print("\nSuccessfully connected to\nAddress: ", address, "\tPort: ", int(port))
        
        usernameAccepted = False
        while(not usernameAccepted):
            username = input("Username: ")
            SendPayload(socketObject, username)
            response = RecvPayload(socketObject)
            if(response == "200"):
                usernameAccepted = True
                break
            else:
                print("Username not accepted. Please try another")

        hostNameAccepted = False
        while(not hostNameAccepted):
            hostname = socket.gethostname()
            SendPayload(socketObject, hostname)
            response = RecvPayload(socketObject)
            if(response == "200"):
                hostNameAccepted = True
                break
        
        connectionSpeedAccepted = False
        while(not connectionSpeedAccepted):
            connectionSpeed = input("Connection Speed: ")
            SendPayload(socketObject, connectionSpeed)
            response = RecvPayload(socketObject)
            if(response == "200"):
                hostNameAccepted = True
                break

        connected = True

    except ConnectionRefusedError:
        print("\Server has reached it's user capacity. Please try again later.")
        socketObject = socket.socket()
        connected = False
    except:
        print("\nFailed to connect to\nAddress: ", address, "\tPort: ", int(port), "\nPlease Try Again")
        socketObject = socket.socket()
        connected = False

# Disconnect from the central server
def Disconnect(commandArgs):
    global connected
    global socketObject
    try:
        # command = " "
        # socketObject.send(command.join(commandArgs).encode("UTF-8"))
        SendPayload(socketObject, " ".join(commandArgs))

        socketObject.close()
        socketObject = socket.socket()
        print("Successfully disconnected")
        connected = False
    except:
        print("Failed to disconnect! Please try again")
    return

# Ask server for available files
def List(commandArgs):
    global socketObject
    global bufferSize

    # command = " "
    # socketObject.send(command.join(commandArgs).encode("UTF-8"))
    SendPayload(socketObject, " ".join(commandArgs))

    # Receiving List of Strings
    listOutput = ""
    reachedEOF = False

    while not reachedEOF:
        # Receiving data in 1 KB chunks
        data = RecvPayload(socketObject)

        # Check of the data is a signifier of the end of transmission
        responseCode = 0
        try:
            responseCode = int(data)
            print("ResponseCode: ", str(responseCode))
        except:
            responseCode = 0
        if(not data or data == "" or responseCode == 205):
            reachedEOF = True
            break
        
        # Not the end of the transmission
        listOutput += data
        # Send confirmation that we received, back to the server
        SendPayload(socketObject, "201")

    print(listOutput)
    return

# Send our available files to the central server
def RefreshServer(commandArgs=[]):

    # If this is the initial connection, we don't need to inform the Server we're sending files, as it's already expecting them
    if(commandArgs):
        SendPayload(socketObject, " ".join(commandArgs))
    
    # Give ourselves some space
    print("\n")

    # Gather descriptions for each file we have, and tell the server about them
    for fileFound in os.listdir("."):
        responseCode = 0
        while(responseCode != 201):
            descriptionPrompt = ""
            if(responseCode == 301):
                descriptionPrompt = "".join(["Something went wrong on the server. Please try again.\n", "Description [", fileFound, "]: "])
            else:
                descriptionPrompt = "".join(["Description [", fileFound, "]: "])
            # print(descriptionPrompt)
            fileDescription = input(descriptionPrompt)
            payload = "|".join([fileFound, fileDescription])

            # Send that info to the server
            SendPayload(socketObject, payload)
            # Wait for servers acceptance code (success or failure)
            response = RecvPayload(socketObject)
            responseCode = int(response)

    # Tell the server we're done
    SendPayload(socketObject, "205")

# Ask server to retrieve a requested file
def Retrieve(commandArgs):
    global socketObject
    global bufferSize

    # command = " "
    # socketObject.send(command.join(commandArgs).encode("UTF-8"))
    SendPayload(socketObject, " ".join(commandArgs))

    # First listen for status code
    # statusData = socketObject.recv(bufferSize)
    # statusCode = statusData.decode("UTF-8")
    statusCode = "300"
    statusCode = RecvPayload(socketObject)
    if(int(statusCode) == 300):
        print("File does not exist")
        return
    if(int(statusCode) != 200):
        print("Error in downloading file")
        return

    # Prepping a fileStream for us to write into
    try:
        receivedFile = open(commandArgs[1], 'wb')
    except:
        print("Error in downloading file")
        return

    # Reading the file in from the server
    reachedEOF = False

    while not reachedEOF:
        print('Downloading file from server...')

        # Receiving data in 1 KB chunks
        data = socketObject.recv(bufferSize)
        if(not data):
            reachedEOF = True
            break

        # If there was no data in the latest chunk, then break out of our loop
        decodedString = data.decode("UTF-8")
        if(len(decodedString) >= 2 and decodedString[len(decodedString) - 1: len(decodedString)] == "\0"):
            reachedEOF = True
            decodedString = decodedString[0: len(decodedString) - 1]

        # Write data to a file
        receivedFile.write(data)

    receivedFile.close()
    print("Successfully downloaded and saved: ", commandArgs[1])
    return

# Send a requested file
def Store(commandArgs):
    global socketObject
    global bufferSize

    # Sending status code for if the file exists
    fileName = commandArgs[1]
    try:
        fileItself = open(fileName, "rb")
    except:
        print("Failed to open file: ", fileName)
        return

    # command = " "
    # socketObject.send(command.join(commandArgs).encode("UTF-8"))
    SendPayload(socketObject, " ".join(commandArgs))

    # Breaking the file down into smaller data chunks
    fileInBytes = fileItself.read(bufferSize)
    while fileInBytes:
        socketObject.send(fileInBytes)

        # Reading in the next chunk of data
        fileInBytes = fileItself.read(bufferSize)
    fileItself.close()

    print("Sent: ", commandArgs[1])

    # Let the client know we're done sending the file
    SendPayload(socketObject, "205")
    return

# Shutdown the server
def Shutdown_Server(commandArgs):
    global socketObject

    # command = " "
    # socketObject.send(command.join(commandArgs).encode("UTF-8"))
    SendPayload(socketObject, " ".join(commandArgs))
    return


def Main():
    global connected
    print("You must first connect to a server before issuing any commands.")

    while True:
        userInput = input("\nEnter Command: ")
        commandArgs = userInput.split()
        commandGiven = commandArgs[0]

        if(commandGiven.upper() == "CONNECT" and len(commandArgs) == 3):
            if connected:
                Disconnect(commandArgs)
                Connect(commandArgs[1], commandArgs[2])
                if(connected):
                    RefreshServer()
            else:
                Connect(commandArgs[1], commandArgs[2])
                if(connected):
                    RefreshServer()
            continue
        else:
            if not connected:
                print("You must first connect to a server before issuing any commands.")
                continue

        if(commandGiven.upper() == "REFRESH_USER_FILES" and len(commandArgs) == 1):
            RefreshServer(commandArgs)
            continue
        elif(commandGiven.upper() == "LIST" and len(commandArgs) == 1):
            List(commandArgs)
            continue
        elif(commandGiven.upper() == "SEARCH" and len(commandArgs) == 2):
            List(commandArgs)
            continue
        elif(commandGiven.upper() == "RETRIEVE" and len(commandArgs) == 2):
            Retrieve(commandArgs)
            continue
        elif(commandGiven.upper() == "STORE" and len(commandArgs) == 2):
            Store(commandArgs)
            continue
        elif(commandGiven.upper() == "DISCONNECT" and len(commandArgs) == 1):
            Disconnect(commandArgs)
            continue
        elif(commandGiven.upper() == "QUIT" and len(commandArgs) == 1):
            Disconnect(commandArgs)
            break
        elif(commandGiven.upper() == "SHUTDOWN_SERVER" and len(commandArgs) == 1):
            Disconnect(commandArgs)
            break
        else:
            print("Invalid Command. Please try again.")
            continue


Main()
print("Program Closing")
