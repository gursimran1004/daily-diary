import threading
import time
from instagrapi import Client
import tkinter as tk
from tkinter import messagebox, Toplevel, scrolledtext

cl = Client()
logged_in = False
stop_bot = False
last_checked = {}

# ✅ Login Function
def login():
    global logged_in
    username = username_entry.get()
    password = password_entry.get()
    try:
        cl.login(username, password)
        logged_in = True
        messagebox.showinfo("Login", "✅ Logged in successfully")
    except Exception as e:
        messagebox.showerror("Login Failed", f"❌ {e}")

# ✅ Fetch Threads
def fetch_safe_threads():
    try:
        result = cl.private_request("direct_v2/inbox/")
        threads = result.get("inbox", {}).get("threads", [])
        safe_threads = []

        for thread in threads:
            thread_id = thread.get("thread_id")
            users = thread.get("users", [])
            messages = thread.get("items", [])
            text_messages = [m for m in messages if m.get("item_type") == "text"]

            if text_messages:
                safe_threads.append({
                    "thread_id": thread_id,
                    "users": users,
                    "messages": text_messages
                })
        return safe_threads
    except Exception as e:
        print("Fetch failed:", e)
        return []

# ✅ Auto-reply Thread
def auto_reply(display_box=None):
    global last_checked
    my_pk = cl.user_id
    while True:
        threads = fetch_safe_threads()
        for thread in threads:
            thread_id = thread["thread_id"]
            messages = thread["messages"]

            if not messages:
                continue  # skip if no messages

            last_msg = messages[0]
            sender_id = last_msg.get("user_id")
            timestamp = int(last_msg.get("timestamp", "0")) // 1000000
            current_time = int(time.time())

            if current_time - timestamp > 3:
                continue  # only reply if message is within 3 seconds

            if last_checked.get(thread_id, 0) >= timestamp:
                continue

            if sender_id == my_pk:
                continue  # skip messages sent by self

            text = last_msg.get("text", "")
            users = thread.get("users", [])
            if not users:
                continue

            user = users[0]
            user_pk = user.get("pk")
            username = user.get("username")

            log = f"New message from {username}: {text}\n"
            if display_box:
                display_box.insert(tk.END, log)
                display_box.see(tk.END)
            else:
                print(log.encode('utf-8', errors='ignore').decode())

            reply = f"Hello @{username}, thank you for your message!"
            try:
                cl.direct_send(reply, [user_pk])
                reply_log = f"Replied to {username}\n"
                if display_box:
                    display_box.insert(tk.END, reply_log)
                    display_box.see(tk.END)
                else:
                    print(reply_log.encode('utf-8', errors='ignore').decode())
            except Exception as e:
                err_log = f"Failed to reply to {username}: {e}\n"
                if display_box:
                    display_box.insert(tk.END, err_log)
                    display_box.see(tk.END)
                else:
                    print(err_log.encode('utf-8', errors='ignore').decode())

            last_checked[thread_id] = timestamp

        time.sleep(3)

# ✅ Start Auto-reply
def start_bot(display_box=None):
    if not logged_in:
        messagebox.showwarning("Login Required", "Please login first!")
        return
    threading.Thread(target=auto_reply, args=(display_box,), daemon=True).start()
    if not display_box:
        messagebox.showinfo("Bot", "Auto-reply started")

# ✅ Send Message
def send_message(username_entry, message_entry, display_box):
    if not logged_in:
        messagebox.showwarning("Login Required", "Please login first!")
        return
    username = username_entry.get().strip()
    message = message_entry.get().strip()
    try:
        user_id = cl.user_id_from_username(username)
        cl.direct_send(message, [user_id])
        output = f"Sent to @{username}: {message}\n\n"
        display_box.insert(tk.END, output)
        display_box.see(tk.END)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to send: {e}")

# ✅ Message Window
def open_message_window():
    if not logged_in:
        messagebox.showwarning("Login Required", "Please login first!")
        return

    msg_window = Toplevel(root)
    msg_window.title("Message & Auto Reply")
    msg_window.geometry("420x520")
    msg_window.configure(bg="#f3f3ff")

    tk.Label(msg_window, text="To Username", font=("Helvetica", 10, "bold"), bg="#f3f3ff").pack()
    to_entry = tk.Entry(msg_window, font=("Arial", 11), bg="#ffffff")
    to_entry.pack(pady=5)

    tk.Label(msg_window, text="Your Message", font=("Helvetica", 10, "bold"), bg="#f3f3ff").pack()
    msg_entry = tk.Entry(msg_window, font=("Arial", 11), bg="#ffffff")
    msg_entry.pack(pady=5)

    display_box = scrolledtext.ScrolledText(msg_window, wrap=tk.WORD, height=18, width=45, bg="#fffaf0", fg="#000080", font=("Courier", 10))
    display_box.pack(pady=10)

    tk.Button(msg_window, text="Send", font=("Helvetica", 10, "bold"), bg="#4caf50", fg="white",
              command=lambda: send_message(to_entry, msg_entry, display_box)).pack(pady=5)

    tk.Button(msg_window, text="Start Auto-Reply", font=("Helvetica", 10, "bold"), bg="#2196f3", fg="white",
              command=lambda: start_bot(display_box)).pack(pady=5)

# ✅ Main GUI
root = tk.Tk()
root.title("Instagram Bot GUI")
root.geometry("420x300")
root.configure(bg="#e0f7fa")

tk.Label(root, text="Instagram Username", font=("Helvetica", 12, "bold"), bg="#e0f7fa").pack(pady=5)
username_entry = tk.Entry(root, font=("Arial", 11), bg="#ffffff")
username_entry.pack(pady=5)

tk.Label(root, text="Password", font=("Helvetica", 12, "bold"), bg="#e0f7fa").pack(pady=5)
password_entry = tk.Entry(root, show="*", font=("Arial", 11), bg="#ffffff")
password_entry.pack(pady=5)

tk.Button(root, text="Login", font=("Helvetica", 11, "bold"), bg="#8e44ad", fg="white", command=login).pack(pady=10)

tk.Button(root, text="Open Message Window", font=("Helvetica", 11, "bold"), bg="#ff9800", fg="white", command=open_message_window).pack(pady=5)

root.mainloop()
