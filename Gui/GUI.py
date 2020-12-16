import os
import sys
import tkinter as tk
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)
from User import user

search_results = []
# Places window in the center of user's screen
def center_window(win):
    # Get screen size
    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()

    # Set window coordinates
    x = (screen_width / 2) - (window_width / 2)
    y = (screen_height / 2) - (window_height / 2)

    # Set Window size and location (center of screen)
    win.geometry(f'{window_width}x{window_height}+{int(x)}+{int(y)}')

#Gets the selected speed user chose
def get_speed():
    x = speed.get()
    return x

#Gets the server hostname
def get_server_ip():
    x = server_ip_text.get("1.0", 'end-1c')
    return x

#Gets the port number
def get_port():
    x = port_text.get("1.0", 'end-1c')
    return x

#Gets the username
def get_username():
    x = username_text.get("1.0", 'end-1c')
    return x


#Function that is called when connect button is pressed
def connect_pressed():
    server_ip = get_server_ip()
    port_number = get_port()
    username = get_username()
    speed = get_speed()

    #array of connection information
    CONNECTION_INFORMATION = [
        server_ip,
        port_number,
        username,
        speed
    ]

    #call the connection function in user class
    if(server_ip != "" and port_number != ""):
        user.Connect(server_ip, port_number)
    else:
        print("You must provide both a valid IP Address and valid Port Number")

    #return the array 
    # print(CONNECTION_INFORMATION)
    return CONNECTION_INFORMATION

def search_pressed():
    if(not user.connected):
        print("You must first connect to a server")
        return

    x = keyword_search_text.get("1.0", 'end-1c')

    #call search function
    #call function to populate table
    return x

#list that is updated with information from search
def update_search_results(list):
    search_results = list

window = tk.Tk()
window.title('Project 2')

# Window size
window_width = 700
window_height = 700

center_window(window)

##CONNECTION SECTION
# labels for conenction section
connection_label = tk.Label(window, text="Connection", font=("Arial", 20)).grid(row=0, columnspan=4)
ip_label = tk.Label(window, text="Server IP: ").grid(row=1, column=0)
port_label = tk.Label(window, text="Port: ").grid(row=1, column=3)
username_label = tk.Label(window, text="Username: ").grid(row=2, column=0)
speed_label = tk.Label(window, text="Speed: ").grid(row=2, column=3)

#Edit texts, setting grid
server_ip_text = tk.Text(window, height=1, width=20, bg="light gray")
server_ip_text.grid(row=1, column=1)

port_text = tk.Text(window, height=1, width=20, bg="light gray")
port_text.grid(row=1, column=4)

username_text = tk.Text(window, height=1, width=20, bg="light gray")
username_text.grid(row=2, column=1)

#Drop down speed menu creation
SPEED_OPTIONS = [
    "Ethernet",
    "T1"
]

speed = tk.StringVar()
speed.set("Ethernet") #default
speed_drop_down = tk.OptionMenu(window, speed, *SPEED_OPTIONS).grid(row=2, column=4, ipadx =10, sticky="ew")


#Connect button
connect_button = tk.Button(window, text="Connect", command=connect_pressed, bg="white", activeforeground="gray", activebackground="dark gray").grid(row=1, column=6)


##SEARCH SECTION

#labels
search_label = tk.Label(window, text="Search", font=("Arial", 20)).grid(row=4, columnspan=4)
keyword_label = tk.Label(window, text="Keyword: ").grid(row=5, column=0)

#edit texts
keyword_search_text = tk.Text(window, height=1, width=20, bg="light gray")
keyword_search_text.grid(row=5, column=1)

#Search Button
search_button = tk.Button(window, text="Search", command=search_pressed, bg="white", activeforeground="gray", activebackground="dark gray").grid(row=5, column=3)

window.mainloop()