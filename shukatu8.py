import tkinter as tk
from tkinter import messagebox
from tkcalendar import DateEntry
from datetime import datetime, timedelta
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr

USER_FILE = "users.json"
TASK_FILE = "tasks.json"

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

SENDER_EMAIL = "yuriasunshine0218@gmail.com"
SENDER_PASSWORD = "zulq yonc jjrw dwsm"


def send_email(to_email, subject, body):
    msg = MIMEText(body.encode("utf-8"), "plain", "utf-8")
    msg["Subject"] = Header(subject, "utf-8").encode()
    msg["From"] = formataddr(("Todo App", SENDER_EMAIL))
    msg["To"] = to_email

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, local_hostname="localhost") as server:
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, to_email, msg.as_bytes())


def load_users():
    if not os.path.exists(USER_FILE):
        return {}
    with open(USER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_users(users):
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def load_tasks():
    if not os.path.exists(TASK_FILE):
        return {}
    with open(TASK_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_tasks(data):
    with open(TASK_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("ログイン")
        self.root.geometry("320x230")

        self.users = load_users()

        tk.Label(root, text="メールアドレス").pack(pady=5)
        self.email = tk.Entry(root, width=35)
        self.email.pack()

        tk.Label(root, text="パスワード").pack(pady=5)
        self.password = tk.Entry(root, show="*", width=35)
        self.password.pack()

        tk.Button(root, text="ログイン", command=self.login).pack(pady=8)
        tk.Button(root, text="新規登録", command=self.register).pack()

    def login(self):
        email = self.email.get().strip()
        pw = self.password.get().strip()

        if email in self.users and self.users[email] == pw:
            self.root.destroy()
            todo_root = tk.Tk()
            TodoApp(todo_root, email)
            todo_root.mainloop()
        else:
            messagebox.showerror("エラー", "ログイン失敗")

    def register(self):
        email = self.email.get().strip()
        pw = self.password.get().strip()

        if email == "" or pw == "":
            messagebox.showwarning("警告", "入力してください")
            return

        if email in self.users:
            messagebox.showerror("エラー", "既に存在します")
            return

        self.users[email] = pw
        save_users(self.users)
        messagebox.showinfo("成功", "登録完了")


class TodoApp:
    def __init__(self, root, user_email):
        self.root = root
        self.user_email = user_email

        self.root.title(f"ToDoアプリ - {user_email}")
        self.root.geometry("780x520")

        all_tasks = load_tasks()
        self.tasks = all_tasks.get(user_email, [])

        frame = tk.Frame(root)
        frame.pack(pady=10)

        self.entry = tk.Entry(frame, width=25)
        self.entry.pack(side=tk.LEFT, padx=5)

        self.date = DateEntry(frame, date_pattern="yyyy-mm-dd")
        self.date.pack(side=tk.LEFT, padx=5)

        self.hour = tk.Spinbox(frame, from_=0, to=23, width=3, format="%02.0f")
        self.hour.pack(side=tk.LEFT)

        tk.Label(frame, text=":").pack(side=tk.LEFT)

        self.minute = tk.Spinbox(frame, from_=0, to=59, width=3, format="%02.0f")
        self.minute.pack(side=tk.LEFT)

        # ⭐優先度
        tk.Label(frame, text="優先度").pack(side=tk.LEFT, padx=5)
        self.priority = tk.StringVar(value="中")
        tk.OptionMenu(frame, self.priority, "高", "中", "低").pack(side=tk.LEFT)

        tk.Button(frame, text="追加", command=self.add_task).pack(side=tk.LEFT, padx=5)

        self.listbox = tk.Listbox(root, width=95)
        self.listbox.pack(pady=10)

        tk.Button(root, text="完了", command=self.complete_task).pack(pady=5)
        tk.Button(root, text="削除", command=self.delete_task).pack(pady=5)

        self.update_listbox()
        self.check_deadline()

    def save(self):
        data = load_tasks()
        data[self.user_email] = self.tasks
        save_tasks(data)

    def add_task(self):
        text = self.entry.get().strip()

        if text == "":
            messagebox.showwarning("警告", "タスクを入力してください")
            return

        d = self.date.get_date()
        h = int(self.hour.get())
        m = int(self.minute.get())

        deadline = datetime(d.year, d.month, d.day, h, m)
        priority = self.priority.get()

        self.tasks.append({
            "text": text,
            "deadline": deadline.strftime("%Y-%m-%d %H:%M"),
            "priority": priority,
            "done": False,
            "notified": False
        })

        self.entry.delete(0, tk.END)
        self.save()
        self.update_listbox()

    def complete_task(self):
        selected = self.listbox.curselection()
        if not selected:
            messagebox.showwarning("警告", "選択してください")
            return

        self.tasks[selected[0]]["done"] = True
        self.save()
        self.update_listbox()

    def delete_task(self):
        selected = self.listbox.curselection()
        if not selected:
            messagebox.showwarning("警告", "選択してください")
            return

        self.tasks.pop(selected[0])
        self.save()
        self.update_listbox()

    def update_listbox(self):
        self.listbox.delete(0, tk.END)

        now = datetime.now()

        # ⭐優先度順に並び替え
        priority_order = {"高": 0, "中": 1, "低": 2}
        self.tasks.sort(key=lambda x: priority_order.get(x.get("priority", "中"), 1))

        for task in self.tasks:
            deadline = datetime.strptime(task["deadline"], "%Y-%m-%d %H:%M")
            status = "完了" if task["done"] else "未完了"
            priority = task.get("priority", "中")

            text = f"[{status}] ({priority}) {task['text']} 期限:{task['deadline']}"
            self.listbox.insert(tk.END, text)

            index = self.listbox.size() - 1

            # 色分け
            if not task["done"] and timedelta(0) <= deadline - now <= timedelta(days=1):
                self.listbox.itemconfig(index, fg="red")
            else:
                if priority == "高":
                    self.listbox.itemconfig(index, fg="red")
                elif priority == "中":
                    self.listbox.itemconfig(index, fg="orange")
                else:
                    self.listbox.itemconfig(index, fg="green")

    def check_deadline(self):
        now = datetime.now()
        changed = False

        for task in self.tasks:
            deadline = datetime.strptime(task["deadline"], "%Y-%m-%d %H:%M")

            if (
                not task["done"]
                and not task["notified"]
                and timedelta(0) <= deadline - now <= timedelta(days=1)
            ):
                try:
                    send_email(
                        self.user_email,
                        "タスク期限通知",
                        f"タスク: {task['text']}\n期限: {task['deadline']}"
                    )
                    task["notified"] = True
                    changed = True
                except Exception as e:
                    print("メールエラー:", e)

        if changed:
            self.save()

        self.root.after(60000, self.check_deadline)


if __name__ == "__main__":
    root = tk.Tk()
    LoginWindow(root)
    root.mainloop()