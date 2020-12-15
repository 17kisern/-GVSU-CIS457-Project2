import os
from os import path
import socket                   # Import socket module
import asyncio

port = 60000                    # Reserve a port for your service.
maxConnections = 5
bufferSize = 1024
queueShutdown = False
activeConnections = []
usersTable = {}
filesTable = {}

"""

Notes
==============

socket.gethostname() gets the current machines hostname, for example "DESKTOP-1337PBJ"

string.encode('UTF-8') encodes the given string into a 'bytes' literal object using the utf-8 standard that is required
bytes.decode("utf-8") decodes some 'bytes' object using the utf-8 standard that information gets sent over the internet in

all the b'string here' are converting a string into binary format. Hence the B

asyncio is just a library that allows us to run parallel operations without stressing about all the bullshit that comes with multithreading. It allows us to run multiple connections simultaneously

"""

# Send a list of all available files to a given user
def List(connection, commandArgs):
    global bufferSize

    connectionAddress = connection[1]
    connectionSocket = connection[0]

    connectionSocket.send(b"\nFiles on Server: \n")

    for fileFound in os.listdir("."):
        joiner = ""
        connectionSocket.send(joiner.join([" - ", fileFound, "\n"]).encode("UTF-8"))

    connectionSocket.send(b"\0")
    return

# Receives a list of all the available files associated with a given user
def RefreshUser(connection, commandArgs):
    global bufferSize

    connectionAddress = connection[1]
    connectionSocket = connection[0]

    # Receiving multiple Strings
    debugString = ""
    reachedEOF = False

    print("[", connectionAddress, "]", "Receiving User's FileTable")

    while not reachedEOF:
        # Receiving data in 1 KB chunks
        data = connectionSocket.recv(bufferSize)
        if(not data):
            reachedEOF = True
            break

        # If there was no data in the latest chunk, then break out of our loop
        decodedString = data.decode("utf-8")

        # If this is our final payload, then make sure this is our last iteration of info
        if(len(decodedString) >= 2 and decodedString[len(decodedString) - 1: len(decodedString)] == "\0"):
            reachedEOF = True
            decodedString = decodedString[0:len(decodedString) - 1]
        
        # Parse info about this specific file
        print(decodedString)
        fileInfo = decodedString.split("|")
        fileName = fileInfo[0]
        fileDescription = fileInfo[1]

        # Add entry to our files table
        fileEntry = (fileName, connectionAddress)
        filesTable[fileEntry] = fileDescription

        debugString += "".join(["\n - ", fileName, "\n", "   - Description: \"", fileDescription, "\""])
    
    debugString += "\n"
    print(debugString)

# Send a file to a given user
def Retrieve(connection, commandArgs):
    connectionAddress = connection[1]
    connectionSocket = connection[0]

    # Sending status code for if the file exists
    fileName = commandArgs[1]
    try:
        fileItself = open(fileName, "rb")
        connectionSocket.send("200".encode("UTF-8"))
    except:
        connectionSocket.send("300".encode("UTF-8"))
        return

    # Breaking the file down into smaller data chunks
    fileInBytes = fileItself.read(bufferSize)

    while fileInBytes:
        connectionSocket.send(fileInBytes)

        # Reading in the next chunk of data
        fileInBytes = fileItself.read(bufferSize)

    print("[", connectionAddress, "] Sent: ", commandArgs[1])

    # Let the client know we're done sending the file
    connectionSocket.send(b"\0")
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
        data = connectionSocket.recv(bufferSize)
        if(not data):
            reachedEOF = True
            break

        # If we reached the end of the file in the latest chunk, then break out of our loop
        decodedString = data.decode("UTF-8")
        if(len(decodedString) >= 2 and decodedString[len(decodedString) - 1: len(decodedString)] == "\0"):
            reachedEOF = True
            decodedString = decodedString[0: len(decodedString) - 1]

        # Write data to a file
        receivedFile.write(data)

    receivedFile.close()
    print("[", connectionAddress, "] Successfully downloaded and saved: ", commandArgs[1])
    return

# End a connection with a specific user
def ShutdownConnection(connection):
    global activeConnections
    connectionAddress = connection[1]
    connectionSocket = connection[0]

    print("[", connectionAddress, "] Ending Connection")
    usersTable.pop(connectionAddress)

    # For every send from one device, we need to have another device listening otherwise the program will hang
    connectionSocket.close()
    activeConnections.remove(connection)

# End all connections and shutdown the server
def ShutdownServer():
    global activeConnections
    global queueShutdown

    for connection in activeConnections:
        ShutdownConnection(connection)
    queueShutdown = True
    return

# Manage the connect/commands from a specific connection
async def ManageConnection(connection):
    global bufferSize
    
    connectionAddress = connection[1]
    connectionSocket = connection[0]
    print("[", connectionAddress, "] Received Connection")
    usersTable[connectionAddress] = None

    # Get the files available on the user's system
    RefreshUser(connection, "REFRESH_USER_FILES")

    while True:
        print("[", connectionAddress, "]", "Listening for commands")
        data = connectionSocket.recv(bufferSize)
        commandGiven = data.decode("UTF-8")
        commandArgs = commandGiven.split()

        print("[", connectionAddress, "] Received Command: ", commandGiven)

        if(len(commandArgs) == 1 and commandArgs[0].upper() == "REFRESH_USER_FILES"):
            RefreshUser(connection, commandArgs)
            continue
        elif(len(commandArgs) == 1 and commandArgs[0].upper() == "LIST"):
            List(connection, commandArgs)
            continue
        elif(len(commandArgs) == 2 and commandArgs[0].upper() == "RETRIEVE"):
            Retrieve(connection, commandArgs)
            continue
        elif(len(commandArgs) == 2 and commandArgs[0].upper() == "STORE"):
            Store(connection, commandArgs)
            continue
        elif(len(commandArgs) == 1 and (commandArgs[0].upper() == "QUIT" or commandArgs[0].upper() == "DISCONNECT")):
            # Close this connection
            ShutdownConnection(connection)
            break
        elif(len(commandArgs) == 1 and commandArgs[0].upper() == "SHUTDOWN_SERVER"):
            ShutdownConnection(connection)
            ShutdownServer()
            break
        else:
            print("Invalid Command Received.")
            print("Received ", len(commandArgs), " arguments.\nCommand: ", commandGiven)
            connectionSocket.send(b"Invalid Command. Please Try Again.")
            connectionSocket.send(b"\0")
            continue


def Main():
    global activeConnections

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
        # print("Number of Connections: ", numConnections)
        # Tupleboi is this ->     [connectionSocket, connectionAddress]
        print("Awaiting Connection")
        if not queueShutdown:
            tupleboi = openSocket.accept()
            if(len(activeConnections) < maxConnections):
                tupleboi[0].send(b"200")
                activeConnections.append(tupleboi)
                asyncio.run(ManageConnection(tupleboi))
            else:
                tupleboi[0].send(b"300")
        else:
            break


Main()
print("Program Closing")
