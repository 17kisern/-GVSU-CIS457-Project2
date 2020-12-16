import tkinter as tk


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


window = tk.Tk()
window.title('Project 2')

# Window size
window_width = 400
window_height = 120

center_window(window)

l1 = tk.Label(window, text="Connect to Server").grid(row=0, column=1)
host_label = tk.Label(window, text="Enter hostname: ").grid(row=1, column=0)
port_label = tk.Label(window, text="Enter port #: ").grid(row=2, column=0)

host_text = tk.Text(window, height=1, width=20, bg="light gray").grid(row=1, column=1)
port_text = tk.Text(window, height=1, width=20, bg="light gray").grid(row=2, column=1)

connect = tk.Button(window, text="Connect", bg="white", activeforeground="gray", activebackground="dark gray").grid(row=3, column=1)


window.mainloop()
