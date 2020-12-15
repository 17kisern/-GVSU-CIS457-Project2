import socket                               # Import socket module

"""

Notes
==============

socket.gethostname() gets the current machines hostname, for example "DESKTOP-1337PBJ"

string.encode('UTF-8') encodes the given string into a 'bytes' literal object using the utf-8 standard that is required
bytes.decode("utf-8") decodes some 'bytes' literal object using the utf-8 standard that information gets sent over the internet in

all the b'string here' are converting a string into binary format. Hence the B

"""

connected = False
socketObject = socket.socket()              # Create a socket object
# host = socket.gethostname()
# host = "localhost"                          # Get local machine name
# port = 60000                                # Reserve a port for your service.
bufferSize = 1024


def Connect(address, port: int):
    global connected
    global socketObject
    global bufferSize

    try:
        socketObject.connect((address, int(port)))

        data = socketObject.recv(bufferSize)
        connectionStatus = data.decode("UTF-8")

        # Make sure we were accepted (server hasn't hit limit)
        if(int(connectionStatus) != 200):
            raise ConnectionRefusedError
        else:
            print("\nSuccessfully connected to\nAddress: ", address, "\tPort: ", int(port))

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
        command = " "
        socketObject.send(command.join(commandArgs).encode("UTF-8"))

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

    command = " "
    socketObject.send(command.join(commandArgs).encode("UTF-8"))

    # Receiving List of Strings
    listOutput = ""
    reachedEOF = False

    while not reachedEOF:
        # Receiving data in 1 KB chunks
        data = socketObject.recv(bufferSize)
        if(not data):
            break

        # If there was no data in the latest chunk, then break out of our loop
        decodedString = data.decode("utf-8")
        if(len(decodedString) >= 2 and decodedString[len(decodedString) - 1: len(decodedString)] == "\0"):
            reachedEOF = True
            decodedString = decodedString[0:len(decodedString) - 1]

        listOutput += data.decode("utf-8")
        # print("Data Received: ", data.decode("utf-8"))

    print(listOutput)

    return

# Send our available files to the central server
def RefreshServer(commandArgs):
    # Send the server info about what files we have
    socketObject.send(b"\nFiles from User: \n")
    for fileFound in os.listdir("."):
        joiner = ""
        toSend = joiner.join([" - ", fileFound, "\n"])
        print(toSend)
        socketObject.send(toSend.encode("UTF-8"))
    socketObject.send(b"\0")

# Ask server to retrieve a requested file
def Retrieve(commandArgs):
    global socketObject
    global bufferSize

    command = " "
    socketObject.send(command.join(commandArgs).encode("UTF-8"))

    # First listen for status code
    statusData = socketObject.recv(1024)
    statusCode = statusData.decode("UTF-8")
    if(int(statusCode) == 300):
        print("File does not exist")
        return
    if(int(statusCode) != 200):
        print("Error in downloading file")
        return

    try:
        joiner = ""
        receivedFile = open(commandArgs[1], 'wb')
    except:
        print("Error in downloading file")
        return

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

    command = " "
    socketObject.send(command.join(commandArgs).encode("UTF-8"))

    # Breaking the file down into smaller data chunks
    fileInBytes = fileItself.read(bufferSize)

    while fileInBytes:
        socketObject.send(fileInBytes)

        # Reading in the next chunk of data
        fileInBytes = fileItself.read(bufferSize)

    print("Sent: ", commandArgs[1])

    # Let the client know we're done sending the file
    socketObject.send(b"\0")
    fileItself.close()
    return

# Shutdown the server
def Shutdown_Server(commandArgs):
    global socketObject

    command = " "
    socketObject.send(command.join(commandArgs).encode("UTF-8"))
    return


def Main():
    print("You must first connect to a server before issuing any commands.")

    while True:
        userInput = input("\nEnter Command: ")
        commandArgs = userInput.split()
        commandGiven = commandArgs[0]

        if(commandGiven.upper() == "CONNECT" and len(commandArgs) == 3):
            if connected:
                Disconnect(commandArgs)
                Connect(commandArgs[1], commandArgs[2])
            else:
                Connect(commandArgs[1], commandArgs[2])
            continue
        else:
            if not connected:
                print("You must first connect to a server before issuing any commands.")
                continue

        if(commandGiven.upper() == "LIST" and len(commandArgs) == 1):
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

        # socketObject.send(userInput.encode('UTF-8'))

        # socketObject.close()
        # print("Connection with Server Closed")


Main()
print("Program Closing")
