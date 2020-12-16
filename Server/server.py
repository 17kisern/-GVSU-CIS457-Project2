import os
from os import path
import socket                   # Import socket module
import asyncio

port = 60000                    # Reserve a port for your service.
maxConnections = 5
bufferSize = 1024
responseBuffer = []
queueShutdown = False
usersTable = {}                 # Key is Username. Value is Tuple (connection, hostname, internetSpeed)
filesTable = {}                 # Key is Tuple (fileName, Username). Value is File Description

"""

Notes
==============

socket.gethostname() gets the current machines hostname, for example "DESKTOP-1337PBJ"

string.encode('UTF-8') encodes the given string into a 'bytes' literal object using the UTF-8 standard that is required
bytes.decode("UTF-8") decodes some 'bytes' object using the UTF-8 standard that information gets sent over the internet in

all the b'string here' are converting a string into binary format. Hence the B

asyncio is just a library that allows us to run parallel operations without stressing about all the bullshit that comes with multithreading. It allows us to run multiple connections simultaneously

"""

def SendPayload(socketBoi, toSend: str):
    payload = "".join([toSend, "\0"])
    socketBoi.send(payload.encode("UTF-8"))
def RecvPayload(socketBoi):
    # If we have shit in our respnse buffer, just use that
    if(len(responseBuffer) > 0):
        return responseBuffer.pop(0)

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
    
    # In case we received multiple responses, split everything on our EOT notifier (NULL \0), and cache into our response buffer
    response = returnString.split("\0")
    for entry in response:
        responseBuffer.append(entry)
    
    # Return the 0th index in the response buffer, and remove it from the response buffer
    return responseBuffer.pop(0)


# Send a list of all available files to a given user
def List(connection, commandArgs):
    global bufferSize

    connectionAddress = connection[1]
    connectionSocket = connection[0]

    SendPayload(connectionSocket, "\nFiles on Server: \n")
    while(int(RecvPayload(connectionSocket)) != 201):
        print("[", connectionAddress, "]", "User failed to receive payload. Trying again.")
        SendPayload(connectionSocket, "\nFiles on Server: \n")

    for fileEntry in filesTable:

        SendPayload(connectionSocket, "".join(["\n - ", fileEntry[0], "\n"]))
        while(int(RecvPayload(connectionSocket)) != 201):
            print("[", connectionAddress, "]", "User failed to receive payload. Trying again.")
            SendPayload(connectionSocket, "".join(["\n - ", fileEntry[0], "\n"]))
        
        SendPayload(connectionSocket, "".join(["   - Host: ", fileEntry[1], "\n"]))
        while(int(RecvPayload(connectionSocket)) != 201):
            print("[", connectionAddress, "]", "User failed to receive payload. Trying again.")
            SendPayload(connectionSocket, "".join(["   - Host: ", fileEntry[1], "\n"]))
        
        SendPayload(connectionSocket, "".join(["   - Description: \"", filesTable[fileEntry], "\""]))
        while(int(RecvPayload(connectionSocket)) != 201):
            print("[", connectionAddress, "]", "User failed to receive payload. Trying again.")
            SendPayload(connectionSocket, "".join(["   - Description: \"", filesTable[fileEntry], "\""]))

    SendPayload(connectionSocket, "205")
    return

# Send a list of specific keymatching files to a given user
def Search(connection, commandArgs):
    global bufferSize

    connectionAddress = connection[1]
    connectionSocket = connection[0]

    stringToSend = "".join(["\nFiles matching \"", commandArgs[1], "\": \n"])
    SendPayload(connectionSocket, stringToSend)

    for fileEntry in filesTable:
        # If file doesn't match our keyword, then it's skipped
        if(commandArgs[1] not in filesTable[fileEntry]):
            continue

        SendPayload(connectionSocket, "".join(["\n - ", fileEntry[0], "\n"]))
        while(int(RecvPayload(connectionSocket)) != 201):
            SendPayload(connectionSocket, "".join(["\n - ", fileEntry[0], "\n"]))
        
        SendPayload(connectionSocket, "".join(["   - Host: ", fileEntry[1], "\n"]))
        while(int(RecvPayload(connectionSocket)) != 201):
            SendPayload(connectionSocket, "".join(["   - Host: ", fileEntry[1], "\n"]))
        
        SendPayload(connectionSocket, "".join(["   - Description: \"", filesTable[fileEntry], "\""]))
        while(int(RecvPayload(connectionSocket)) != 201):
            SendPayload(connectionSocket, "".join(["   - Description: \"", filesTable[fileEntry], "\""]))

    SendPayload(connectionSocket, "205")
    return

# Receives a list of all the available files associated with a given user
def RefreshUser(connection, username, commandArgs):
    global bufferSize

    connectionAddress = connection[1]
    connectionSocket = connection[0]

    # Receiving multiple Strings
    debugString = ""
    reachedEOF = False

    print("[", connectionAddress, "]", "Receiving User's FileTable")

    while not reachedEOF:
        # Receiving data in 1 KB chunks
        data = RecvPayload(connectionSocket)
        transmissionEnded = False
        statusCode = 0
        try:
            statusCode = int(data)
            transmissionEnded = True
        except:
            transmissionEnded = False

        if(not data or data == "" or statusCode == 205):
            reachedEOF = True
            break

        # If there was no data in the latest chunk, then break out of our loop
        decodedString = data

        # If this is our final payload, then make sure this is our last iteration of info
        if(len(decodedString) >= 2 and decodedString[len(decodedString) - 1: len(decodedString)] == "\0"):
            reachedEOF = True
            decodedString = decodedString[0:len(decodedString) - 1]
        
        try:
            # Parse info about this specific file
            fileInfo = decodedString.split("|")
            fileName = fileInfo[0]
            fileDescription = fileInfo[1]
            fileEntry = (fileName, username)
        except:
            # Failed to parse info, tell the user we need them to try again
            print("[", connectionAddress, "]", "Error in receiving file")
            SendPayload(connectionSocket, "301")
            continue

        # Add entry to our files table
        filesTable[fileEntry] = fileDescription
        debugString += "".join(["\n - ", fileName, "\n", "   - Host: ", username, "\n", "   - Description: \"", fileDescription, "\""])

        # Inform user that we successfully recorded that file
        print("[", connectionAddress, "]", "Received file info [", fileName, "]")
        SendPayload(connectionSocket, "201")
    
    print(debugString)
    print("\n")

# Send a file to a given user
def Retrieve(connection, commandArgs):
    connectionAddress = connection[1]
    connectionSocket = connection[0]

    # Sending status code for if the file exists
    fileName = commandArgs[1]
    try:
        fileItself = open(fileName, "rb")
        # connectionSocket.send("200".encode("UTF-8"))
        SendPayload(connectionSocket, "200")
    except:
        # connectionSocket.send("300".encode("UTF-8"))
        SendPayload(connectionSocket, "300")
        return

    # Breaking the file down into smaller data chunks
    fileInBytes = fileItself.read(bufferSize)

    while fileInBytes:
        connectionSocket.send(fileInBytes)

        # Reading in the next chunk of data
        fileInBytes = fileItself.read(bufferSize)

    print("[", connectionAddress, "] Sent: ", commandArgs[1])

    # Let the client know we're done sending the file
    SendPayload(connectionSocket, "205")
    fileItself.close()
    return

# Receive & save a file that was sent to us
def Store(connection, commandArgs):
    global bufferSize

    connectionAddress = connection[1]
    connectionSocket = connection[0]

    try:
        joiner = ""
        receivedFile = open(commandArgs[1], 'wb')
    except:
        print("[", connectionAddress, "] Error in downloading file")
        return

    reachedEOF = False

    while not reachedEOF:
        print("[", connectionAddress, "] Downloading file from client...")

        # Receiving data in 1 KB chunks
        # data = connectionSocket.recv(bufferSize)
        data = RecvPayload(connectionSocket)
        if(not data):
            reachedEOF = True
            break

        # If we reached the end of the file in the latest chunk, then break out of our loop
        # decodedString = data.decode("UTF-8")
        decodedString = data
        if(len(decodedString) >= 2 and decodedString[len(decodedString) - 1: len(decodedString)] == "\0"):
            reachedEOF = True
            decodedString = decodedString[0: len(decodedString) - 1]

        # Write data to a file
        receivedFile.write(data)

    receivedFile.close()
    print("[", connectionAddress, "] Successfully downloaded and saved: ", commandArgs[1])
    return

# End a connection with a specific user
def ShutdownConnection(connection, username):
    global activeConnections
    connectionAddress = connection[1]
    connectionSocket = connection[0]

    print("[", connectionAddress, "] Ending Connection with user [", username, "]")
    usersTable.pop(username)

    # Remove all files associated with that user
    toRemove = []
    for entry in filesTable:
        # 'entry' is the Key. It's a Tuple (fileName, username)
        if(entry[1] == username):
            toRemove.append(entry)
    for entry in toRemove:
        filesTable.pop(entry)

    # For every send from one device, we need to have another device listening otherwise the program will hang
    connectionSocket.close()

# End all connections and shutdown the server
def ShutdownServer():
    global activeConnections
    global queueShutdown

    for entry in usersTable:
        ShutdownConnection(usersTable[entry][0], entry)
    queueShutdown = True
    return

# Manage the connect/commands from a specific connection
async def ManageConnection(connection):
    print("Inside ManageConnection")
    global bufferSize
    
    connectionAddress = connection[1]
    connectionSocket = connection[0]

    print("[", connectionAddress, "] Received Connection")
    print("[", connectionAddress, "] Waiting on User's login info")

    # Receiving the user's UserName
    usernameAccepted = False
    while(not usernameAccepted):
        try:
            username = RecvPayload(connectionSocket)
            print("[", connectionAddress, "]", "Username: ", username)
            if(username in usersTable):
                SendPayload(connectionSocket, "300")
                usernameAccepted = False
            else:
                SendPayload(connectionSocket, "200")
                usernameAccepted = True
        except:
            print("[", connectionAddress, "]", "Username already taken [", username, "]")
            SendPayload(connectionSocket, "300")
            usernameAccepted = False

    # Receiving the user's HostName
    hostNameAccepted = False
    while(not hostNameAccepted):
        try:
            hostname = RecvPayload(connectionSocket)
            print("[", connectionAddress, "]", "Hostname: ", hostname)
            SendPayload(connectionSocket, "200")
            hostNameAccepted = True
        except:
            print("[", connectionAddress, "]", "Failed to record Hostname [", hostname, "]")
            SendPayload(connectionSocket, "300")
            hostNameAccepted = False


    # Receiving the user's InternetSpeed
    connectionSpeedAccepted = False
    while(not connectionSpeedAccepted):
        try:
            speed = RecvPayload(connectionSocket)
            print("[", connectionAddress, "]", "Connection Speed: ", speed)    
            SendPayload(connectionSocket, "200")
            connectionSpeedAccepted = True
        except:
            print("[", connectionAddress, "]", "Failed to record connection speed [", speed, "]")
            SendPayload(connectionSocket, "300")
            connectionSpeedAccepted = False


    # Saving user into our table. Key is the user's username
    usersTable[username] = (connection, hostname, speed)

    # Get the files available on the user's system
    RefreshUser(connection, username, "REFRESH_USER_FILES")

    while True:
        print("[", connectionAddress, "]", "Listening for commands")
        # data = connectionSocket.recv(bufferSize)
        # commandGiven = data.decode("UTF-8")
        commandGiven = RecvPayload(connectionSocket)
        commandArgs = commandGiven.split()

        print("[", connectionAddress, "] Received Command: ", commandGiven)

        if(len(commandArgs) == 1 and commandArgs[0].upper() == "REFRESH_USER_FILES"):
            RefreshUser(connection, username, commandArgs)
            continue
        elif(len(commandArgs) == 1 and commandArgs[0].upper() == "LIST"):
            List(connection, commandArgs)
            continue
        elif(len(commandArgs) == 2 and commandArgs[0].upper() == "SEARCH"):
            Search(connection, commandArgs)
            continue
        elif(len(commandArgs) == 2 and commandArgs[0].upper() == "RETRIEVE"):
            Retrieve(connection, commandArgs)
            continue
        elif(len(commandArgs) == 2 and commandArgs[0].upper() == "STORE"):
            Store(connection, commandArgs)
            continue
        elif(len(commandArgs) == 1 and (commandArgs[0].upper() == "QUIT" or commandArgs[0].upper() == "DISCONNECT")):
            # Close this connection
            ShutdownConnection(connection, username)
            break
        elif(len(commandArgs) == 1 and commandArgs[0].upper() == "SHUTDOWN_SERVER"):
            ShutdownConnection(connection, username)
            ShutdownServer()
            break
        else:
            print("Invalid Command Received.")
            print("Received ", len(commandArgs), " arguments.\nCommand: ", commandGiven)
            # connectionSocket.send(b"Invalid Command. Please Try Again.")
            # connectionSocket.send(b"\0")
            SendPayload(connectionSocket, "Invalid Command. Please Try Again.")
            continue

def Main():
    global activeConnections
    global bufferSize

    # Create a socket object
    openSocket = socket.socket()

    # Get local machine name
    host = "localhost"

    # Bind to the port
    openSocket.bind((host, port))

    # Configure to allow 5 connections
    openSocket.listen(maxConnections)

    # Wait for new connections
    while True:
        # Tupleboi is this ->     [connectionSocket, connectionAddress]
        print("Awaiting Connection")
        if not queueShutdown:
            tupleboi = openSocket.accept()

            if(len(usersTable) < maxConnections):
                # Telling user they've been approved to connect
                SendPayload(tupleboi[0], "200")
                asyncio.run(ManageConnection(tupleboi))
            else:
                SendPayload(tupleboi[0], "300")
        else:
            print("Queueing Shutdown")
            break


Main()
print("Program Closing")
