import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import subprocess
import threading
import time
import pygetwindow as gw
import win32gui
import win32con
import win32com.client
import pyautogui
from pynput import keyboard as pynput_keyboard
from playsound import playsound
import random

# === Global Variables ===
target_window_title = None
target_hwnd = None
lock_active = False
timer_done = False
lock_screen = None
keys_pressed = set()
proc = None
penalty_time = 0

# === GUI Setup ===
def select_exe():
    filepath = filedialog.askopenfilename(filetypes=[("Executable files", "*.exe")])
    exe_path.set(filepath)

def start_focus_session():
    global target_window_title, target_hwnd, proc, penalty_time, timer_done
    penalty_time = 0
    timer_done = False

    if not exe_path.get():
        messagebox.showerror("Error", "Please select an executable.")
        return

    duration = simpledialog.askinteger("Timer", "Enter focus time (in minutes):", minvalue=1)
    if not duration:
        return

    # Launch the app
    proc = subprocess.Popen(exe_path.get())
    time.sleep(3)

    # Get hwnd + title
    try:
        hwnd = win32gui.GetForegroundWindow()
        target_hwnd = hwnd
        target_window_title = win32gui.GetWindowText(hwnd)
    except Exception as e:
        print(f"[ERROR] Could not get window handle: {e}")

    threading.Thread(target=start_timer, args=(duration * 60,), daemon=True).start()
    threading.Thread(target=monitor_focus, daemon=True).start()

# === Timer Logic ===
def start_timer(duration):
    global timer_done
    while duration + penalty_time > 0:
        time.sleep(1)
        duration -= 1
    timer_done = True
    hide_lock_screen()
    print("✅ Focus session complete. You're free!")

# === Lock Screen Features ===
hacker_phrases = [
    "Tracing IP...",
    "Locating brain...",
    "Injecting firewall bypass...",
    "Deploying memetic kill agent...",
    "Sanity check failed... retrying...",
]

def animate_hacker_text(label, phrases, index=0):
    if index < len(phrases):
        label.config(text=phrases[index])
        lock_screen.after(1500, animate_hacker_text, label, phrases, index + 1)

def matrix_rain(canvas, width, height):
    chars = "01"
    drops = [0 for _ in range(width // 10)]
    def draw():
        canvas.delete("all")
        for i in range(len(drops)):
            char = random.choice(chars)
            canvas.create_text(i * 10, drops[i] * 10, text=char, fill="lime", font=("Courier", 12, "bold"))
            drops[i] = drops[i] + 1 if drops[i] * 10 < height else 0
        if not timer_done:
            canvas.after(50, draw)
    draw()

def play_scream():
    try:
        playsound("sound.mp3", block=False)
    except:
        print("⚠️ sound.mp3 missing or playback error.")

def jail_mouse_to_center():
    screenWidth, screenHeight = pyautogui.size()
    centerX, centerY = screenWidth // 2, screenHeight // 2
    def move_mouse_forever():
        while lock_active and not timer_done:
            pyautogui.moveTo(centerX + random.randint(-5, 5), centerY + random.randint(-5, 5))
            time.sleep(0.1)
    threading.Thread(target=move_mouse_forever, daemon=True).start()

def show_lock_screen():
    global lock_screen, lock_active, penalty_time
    if lock_active or timer_done:
        return

    lock_active = True
    penalty_time += 60
    print(f"🚨 Escape attempt detected! +1 minute added. Total Penalty: {penalty_time}s")

    play_scream()

    lock_screen = tk.Toplevel()
    lock_screen.attributes('-fullscreen', True)
    lock_screen.attributes('-topmost', True)
    lock_screen.configure(bg='black')
    lock_screen.protocol("WM_DELETE_WINDOW", lambda: None)

    canvas = tk.Canvas(lock_screen, bg="black", highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    width = lock_screen.winfo_screenwidth()
    height = lock_screen.winfo_screenheight()
    matrix_rain(canvas, width, height)

    label = tk.Label(lock_screen, text="", fg="red", bg="black", font=("Courier", 28, "bold"))
    label.place(relx=0.5, rely=0.4, anchor="center")

    animate_hacker_text(label, hacker_phrases)
    jail_mouse_to_center()

    threading.Thread(target=listen_for_unlock, daemon=True).start()

def hide_lock_screen():
    global lock_active, lock_screen, target_hwnd, target_window_title
    if lock_screen:
        try:
            lock_screen.after(0, lock_screen.destroy)
        except:
            pass
    lock_active = False

    try:
        if target_hwnd and win32gui.IsWindow(target_hwnd):
            shell = win32com.client.Dispatch("WScript.Shell")
            shell.SendKeys('%')  # Enable SetForegroundWindow

            win32gui.ShowWindow(target_hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(target_hwnd)

            rect = win32gui.GetWindowRect(target_hwnd)
            center_x = (rect[0] + rect[2]) // 2
            center_y = (rect[1] + rect[3]) // 2
            pyautogui.click(center_x, center_y)

            print(f"✅ Refocused to: {target_window_title}")
        else:
            print("⚠️ Window handle invalid or app was closed.")
    except Exception as e:
        print(f"[WARN] Could not refocus app: {e}")

# === Monitor App Focus ===
def monitor_focus():
    global target_hwnd
    while not timer_done:
        try:
            current_hwnd = win32gui.GetForegroundWindow()
            if current_hwnd != target_hwnd:
                show_lock_screen()
            else:
                if lock_active:
                    hide_lock_screen()
        except Exception as e:
            print(f"[ERROR] {e}")
        time.sleep(1)

# === Unlock Hotkey Combo ===
def listen_for_unlock():
    def on_press(key):
        try:
            if hasattr(key, 'char') and key.char == 'u':
                hide_lock_screen()
                return False
        except:
            pass

    with pynput_keyboard.Listener(on_press=on_press) as listener:
        listener.join()

# === Main GUI ===
root = tk.Tk()
root.title("Ctrl+Obey - Stay Focused or Else 😈")

exe_path = tk.StringVar()

frame = tk.Frame(root, padx=20, pady=20)
frame.pack()

tk.Label(frame, text="Select App to Focus On (.exe):").pack()
tk.Button(frame, text="Browse", command=select_exe).pack(pady=5)
tk.Entry(frame, textvariable=exe_path, width=50).pack()

tk.Button(frame, text="Start Focus Session", command=start_focus_session, bg='green', fg='white').pack(pady=20)

root.mainloop()