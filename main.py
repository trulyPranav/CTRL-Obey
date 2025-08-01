import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import subprocess
import threading
import time
import pygetwindow as gw
import win32gui
import os
from pynput import keyboard as pynput_keyboard

# === Global Variables ===
target_window_title = None
lock_active = False
timer_done = False
lock_screen = None
keys_pressed = set()
proc = None

# === GUI Setup ===
def select_exe():
    filepath = filedialog.askopenfilename(filetypes=[("Executable files", "*.exe")])
    exe_path.set(filepath)

def start_focus_session():
    global target_window_title, proc

    if not exe_path.get():
        messagebox.showerror("Error", "Please select an executable.")
        return

    duration = simpledialog.askinteger("Timer", "Enter focus time (in minutes):", minvalue=1)
    if not duration:
        return

    # Launch the app
    proc = subprocess.Popen(exe_path.get())
    time.sleep(3)  # Give it time to launch

    # Get the window title of the launched app
    try:
        windows = gw.getWindowsWithTitle(proc.args[0].split("\\")[-1].replace(".exe", ""))
        if windows:
            target_window_title = windows[0].title
        else:
            target_window_title = win32gui.GetWindowText(win32gui.GetForegroundWindow())
    except:
        target_window_title = win32gui.GetWindowText(win32gui.GetForegroundWindow())

    # Start timer thread
    threading.Thread(target=start_timer, args=(duration * 60,), daemon=True).start()
    # Start monitor thread
    threading.Thread(target=monitor_focus, daemon=True).start()

# === Timer Logic ===
def start_timer(duration):
    global timer_done
    time.sleep(duration)
    timer_done = True
    hide_lock_screen()
    print("Focus session ended. You're free!")

# === Lock Screen ===
def show_lock_screen():
    global lock_screen, lock_active
    if lock_active or timer_done:
        return

    lock_active = True
    lock_screen = tk.Toplevel()
    lock_screen.attributes('-fullscreen', True)
    lock_screen.attributes('-topmost', True)
    lock_screen.configure(bg='black')
    lock_screen.protocol("WM_DELETE_WINDOW", lambda: None)  # Disable close

    label = tk.Label(lock_screen, text="🔒 ACCESS DENIED\nStay Focused!", fg="lime", bg="black", font=("Courier", 32))
    label.pack(expand=True)

    lock_screen.update()

    # Start listening for escape combo
    threading.Thread(target=listen_for_unlock, daemon=True).start()

def hide_lock_screen():
    global lock_active, lock_screen, target_window_title
    if lock_screen:
        try:
            lock_screen.after(0, lock_screen.destroy)
        except:
            pass
    lock_active = False

    # Bring the original app to front
    try:
        if target_window_title:
            win = gw.getWindowsWithTitle(target_window_title)
            if win:
                win[0].activate()
                win[0].minimize()  # Fix for some apps not raising
                win[0].restore()
    except Exception as e:
        print(f"[WARN] Could not refocus app: {e}")


# === Monitor App Focus ===
def monitor_focus():
    global target_window_title
    while not timer_done:
        try:
            current = win32gui.GetWindowText(win32gui.GetForegroundWindow())
            if target_window_title not in current:
                show_lock_screen()
            else:
                if lock_active:
                    hide_lock_screen()
        except Exception as e:
            print(f"[ERROR] {e}")
        time.sleep(1)

# === Unlock Combo Listener ===
def listen_for_unlock():
    def on_press(key):
        try:
            if key in [pynput_keyboard.Key.ctrl_l, pynput_keyboard.Key.ctrl_r,
                       pynput_keyboard.Key.alt_l, pynput_keyboard.Key.alt_r,
                       pynput_keyboard.Key.enter]:
                keys_pressed.add(key)

            if any(k in keys_pressed for k in [pynput_keyboard.Key.ctrl_l, pynput_keyboard.Key.ctrl_r]) and \
               any(k in keys_pressed for k in [pynput_keyboard.Key.alt_l, pynput_keyboard.Key.alt_r]) and \
               pynput_keyboard.Key.enter in keys_pressed:
                hide_lock_screen()
                return False  # stop listener
        except:
            pass

    def on_release(key):
        if key in keys_pressed:
            keys_pressed.remove(key)

    with pynput_keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

# === Tkinter GUI ===
root = tk.Tk()
root.title("AppJail - Stay Focused or Else 😈")

exe_path = tk.StringVar()

frame = tk.Frame(root, padx=20, pady=20)
frame.pack()

tk.Label(frame, text="Select App to Focus On (.exe):").pack()
tk.Button(frame, text="Browse", command=select_exe).pack(pady=5)
tk.Entry(frame, textvariable=exe_path, width=50).pack()

tk.Button(frame, text="Start Focus Session", command=start_focus_session, bg='green', fg='white').pack(pady=20)

root.mainloop()