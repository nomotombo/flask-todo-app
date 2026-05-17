import tkinter as tk
from tkinter import messagebox, ttk
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

# Gmailアプリパスワードをコードに直接書くのは危険なので、環境変数から読み込む
# Windowsの例:
# setx TODO_SENDER_EMAIL "自分のGmailアドレス"
# setx TODO_SENDER_PASSWORD "Gmailのアプリパスワード"
SENDER_EMAIL = os.getenv("TODO_SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("TODO_SENDER_PASSWORD")


PRIORITY_ORDER = {
    "高": 0,
    "中": 1,
    "低": 2
}

NOTIFY_OPTIONS = {
    "1時間前": timedelta(hours=1),
    "当日": timedelta(days=0),
    "1日前": timedelta(days=1),
    "3日前": timedelta(days=3)
}


# -------------------------
# メール送信
# -------------------------
def send_email(to_email, subject, body):
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        raise ValueError("送信用メールアドレスまたはアプリパスワードが環境変数に設定されていません。")

    msg = MIMEText(body.encode("utf-8"), "plain", "utf-8")
    msg["Subject"] = Header(subject, "utf-8").encode()
    msg["From"] = formataddr(("Todo App", SENDER_EMAIL))
    msg["To"] = to_email

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, local_hostname="localhost") as server:
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, to_email, msg.as_bytes())


# -------------------------
# JSON読み書き
# -------------------------
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


# -------------------------
# ログイン画面
# -------------------------
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
            messagebox.showwarning("警告", "メールアドレスとパスワードを入力してください")
            return

        if email in self.users:
            messagebox.showerror("エラー", "既に存在します")
            return

        self.users[email] = pw
        save_users(self.users)
        messagebox.showinfo("成功", "登録完了")


# -------------------------
# ToDoアプリ本体
# -------------------------
class TodoApp:
    def __init__(self, root, user_email):
        self.root = root
        self.user_email = user_email

        self.root.title(f"ToDoアプリ - {user_email}")
        self.root.geometry("980x650")

        all_tasks = load_tasks()
        self.tasks = all_tasks.get(user_email, [])
        self.normalize_tasks()

        # 実際に画面へ表示しているタスクの番号を保持する
        self.displayed_indexes = []

        # -------------------------
        # 入力エリア
        # -------------------------
        input_frame = tk.LabelFrame(root, text="タスク入力")
        input_frame.pack(pady=10, padx=10, fill="x")

        tk.Label(input_frame, text="タスク名").grid(row=0, column=0, padx=5, pady=5)
        self.entry = tk.Entry(input_frame, width=28)
        self.entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(input_frame, text="期限").grid(row=0, column=2, padx=5, pady=5)
        self.date = DateEntry(input_frame, date_pattern="yyyy-mm-dd")
        self.date.grid(row=0, column=3, padx=5, pady=5)

        self.hour = tk.Spinbox(input_frame, from_=0, to=23, width=3, format="%02.0f")
        self.hour.grid(row=0, column=4)
        tk.Label(input_frame, text=":").grid(row=0, column=5)
        self.minute = tk.Spinbox(input_frame, from_=0, to=59, width=3, format="%02.0f")
        self.minute.grid(row=0, column=6)

        tk.Label(input_frame, text="優先度").grid(row=1, column=0, padx=5, pady=5)
        self.priority = ttk.Combobox(input_frame, values=["高", "中", "低"], width=6, state="readonly")
        self.priority.set("中")
        self.priority.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        tk.Label(input_frame, text="カテゴリ").grid(row=1, column=2, padx=5, pady=5)
        self.category = ttk.Combobox(input_frame, values=["就活", "勉強", "生活", "提出物", "その他"], width=10)
        self.category.set("その他")
        self.category.grid(row=1, column=3, padx=5, pady=5, sticky="w")

        tk.Label(input_frame, text="通知").grid(row=1, column=4, padx=5, pady=5)
        self.notify_timing = ttk.Combobox(input_frame, values=list(NOTIFY_OPTIONS.keys()), width=8, state="readonly")
        self.notify_timing.set("1日前")
        self.notify_timing.grid(row=1, column=5, columnspan=2, padx=5, pady=5, sticky="w")

        tk.Button(input_frame, text="追加", command=self.add_task).grid(row=0, column=7, padx=5, pady=5)
        tk.Button(input_frame, text="編集反映", command=self.edit_task).grid(row=1, column=7, padx=5, pady=5)

        # -------------------------
        # 検索・絞り込みエリア
        # -------------------------
        filter_frame = tk.LabelFrame(root, text="検索・絞り込み")
        filter_frame.pack(pady=5, padx=10, fill="x")

        tk.Label(filter_frame, text="検索").pack(side=tk.LEFT, padx=5)
        self.search_entry = tk.Entry(filter_frame, width=25)
        self.search_entry.pack(side=tk.LEFT, padx=5)

        tk.Label(filter_frame, text="表示").pack(side=tk.LEFT, padx=5)
        self.filter_status = ttk.Combobox(
            filter_frame,
            values=["すべて", "未完了のみ", "完了のみ", "優先度:高", "期限切れ"],
            width=12,
            state="readonly"
        )
        self.filter_status.set("すべて")
        self.filter_status.pack(side=tk.LEFT, padx=5)

        tk.Button(filter_frame, text="検索/絞り込み", command=self.update_listbox).pack(side=tk.LEFT, padx=5)
        tk.Button(filter_frame, text="リセット", command=self.reset_filter).pack(side=tk.LEFT, padx=5)

        # -------------------------
        # タスク一覧
        # -------------------------
        self.listbox = tk.Listbox(root, width=130, height=20)
        self.listbox.pack(pady=10, padx=10)
        self.listbox.bind("<<ListboxSelect>>", self.on_select_task)

        # -------------------------
        # 操作ボタン
        # -------------------------
        button_frame = tk.Frame(root)
        button_frame.pack(pady=5)

        tk.Button(button_frame, text="完了", command=self.complete_task).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="未完了に戻す", command=self.uncomplete_task).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="削除", command=self.delete_task).pack(side=tk.LEFT, padx=5)

        self.save()
        self.update_listbox()
        self.check_deadline()

    # -------------------------
    # 古いtasks.jsonとの互換性を保つ
    # -------------------------
    def normalize_tasks(self):
        for task in self.tasks:
            if "done" not in task:
                task["done"] = task.get("completed", False)
            if "notified" not in task:
                task["notified"] = False
            if "priority" not in task:
                task["priority"] = "中"
            if "category" not in task:
                task["category"] = "その他"
            if "notify_timing" not in task:
                task["notify_timing"] = "1日前"

    def save(self):
        data = load_tasks()
        data[self.user_email] = self.tasks
        save_tasks(data)

    def get_deadline_from_inputs(self):
        d = self.date.get_date()
        h = int(self.hour.get())
        m = int(self.minute.get())
        return datetime(d.year, d.month, d.day, h, m)

    def get_selected_task_index(self):
        selected = self.listbox.curselection()
        if not selected:
            return None
        display_index = selected[0]
        if display_index >= len(self.displayed_indexes):
            return None
        return self.displayed_indexes[display_index]

    # -------------------------
    # タスク追加
    # -------------------------
    def add_task(self):
        text = self.entry.get().strip()

        if text == "":
            messagebox.showwarning("警告", "タスクを入力してください")
            return

        deadline = self.get_deadline_from_inputs()

        self.tasks.append({
            "text": text,
            "deadline": deadline.strftime("%Y-%m-%d %H:%M"),
            "done": False,
            "notified": False,
            "priority": self.priority.get(),
            "category": self.category.get().strip() or "その他",
            "notify_timing": self.notify_timing.get()
        })

        self.entry.delete(0, tk.END)
        self.save()
        self.update_listbox()

    # -------------------------
    # タスク編集
    # -------------------------
    def edit_task(self):
        task_index = self.get_selected_task_index()

        if task_index is None:
            messagebox.showwarning("警告", "編集するタスクを選択してください")
            return

        text = self.entry.get().strip()
        if text == "":
            messagebox.showwarning("警告", "タスク名を入力してください")
            return

        deadline = self.get_deadline_from_inputs()
        task = self.tasks[task_index]

        task["text"] = text
        task["deadline"] = deadline.strftime("%Y-%m-%d %H:%M")
        task["priority"] = self.priority.get()
        task["category"] = self.category.get().strip() or "その他"
        task["notify_timing"] = self.notify_timing.get()

        # 期限や通知タイミングを変更したら、再通知できるようにする
        task["notified"] = False

        self.save()
        self.update_listbox()
        messagebox.showinfo("成功", "タスクを編集しました")

    def on_select_task(self, event):
        task_index = self.get_selected_task_index()
        if task_index is None:
            return

        task = self.tasks[task_index]
        deadline = datetime.strptime(task["deadline"], "%Y-%m-%d %H:%M")

        self.entry.delete(0, tk.END)
        self.entry.insert(0, task["text"])
        self.date.set_date(deadline.date())
        self.hour.delete(0, tk.END)
        self.hour.insert(0, f"{deadline.hour:02d}")
        self.minute.delete(0, tk.END)
        self.minute.insert(0, f"{deadline.minute:02d}")
        self.priority.set(task.get("priority", "中"))
        self.category.set(task.get("category", "その他"))
        self.notify_timing.set(task.get("notify_timing", "1日前"))

    # -------------------------
    # 完了・未完了・削除
    # -------------------------
    def complete_task(self):
        task_index = self.get_selected_task_index()

        if task_index is None:
            messagebox.showwarning("警告", "タスクを選択してください")
            return

        self.tasks[task_index]["done"] = True
        self.save()
        self.update_listbox()

    def uncomplete_task(self):
        task_index = self.get_selected_task_index()

        if task_index is None:
            messagebox.showwarning("警告", "タスクを選択してください")
            return

        self.tasks[task_index]["done"] = False
        self.tasks[task_index]["notified"] = False
        self.save()
        self.update_listbox()

    def delete_task(self):
        task_index = self.get_selected_task_index()

        if task_index is None:
            messagebox.showwarning("警告", "タスクを選択してください")
            return

        self.tasks.pop(task_index)
        self.save()
        self.update_listbox()

    # -------------------------
    # 検索・絞り込み
    # -------------------------
    def reset_filter(self):
        self.search_entry.delete(0, tk.END)
        self.filter_status.set("すべて")
        self.update_listbox()

    def should_display_task(self, task, now):
        keyword = self.search_entry.get().strip().lower()
        filter_value = self.filter_status.get()

        deadline = datetime.strptime(task["deadline"], "%Y-%m-%d %H:%M")
        is_overdue = not task["done"] and deadline < now

        if keyword:
            target = f"{task['text']} {task.get('category', '')} {task.get('priority', '')}".lower()
            if keyword not in target:
                return False

        if filter_value == "未完了のみ" and task["done"]:
            return False
        if filter_value == "完了のみ" and not task["done"]:
            return False
        if filter_value == "優先度:高" and task.get("priority") != "高":
            return False
        if filter_value == "期限切れ" and not is_overdue:
            return False

        return True

    # -------------------------
    # 表示更新
    # 期限が近い順・優先度が高い順で自動並び替え
    # -------------------------
    def update_listbox(self):
        self.listbox.delete(0, tk.END)
        self.displayed_indexes = []

        now = datetime.now()

        indexed_tasks = list(enumerate(self.tasks))

        # 優先度が高い順、その中で期限が近い順に並べる
        indexed_tasks.sort(
            key=lambda item: (
                PRIORITY_ORDER.get(item[1].get("priority", "中"), 1),
                datetime.strptime(item[1]["deadline"], "%Y-%m-%d %H:%M")
            )
        )

        for original_index, task in indexed_tasks:
            if not self.should_display_task(task, now):
                continue

            deadline = datetime.strptime(task["deadline"], "%Y-%m-%d %H:%M")
            is_overdue = not task["done"] and deadline < now

            if task["done"]:
                status = "完了"
            elif is_overdue:
                status = "期限切れ"
            else:
                status = "未完了"

            display_text = (
                f"[{status}] "
                f"[優先度:{task.get('priority', '中')}] "
                f"[カテゴリ:{task.get('category', 'その他')}] "
                f"{task['text']} "
                f"期限:{task['deadline']} "
                f"通知:{task.get('notify_timing', '1日前')}"
            )

            self.listbox.insert(tk.END, display_text)
            self.displayed_indexes.append(original_index)

            index = self.listbox.size() - 1

            # 期限切れは赤色
            if is_overdue:
                self.listbox.itemconfig(index, fg="red")
            # 期限が24時間以内の未完了タスクも赤色
            elif not task["done"] and timedelta(0) <= deadline - now <= timedelta(days=1):
                self.listbox.itemconfig(index, fg="red")
            # 完了タスクはグレー
            elif task["done"]:
                self.listbox.itemconfig(index, fg="gray")

    # -------------------------
    # 通知チェック
    # -------------------------
    def check_deadline(self):
        now = datetime.now()
        changed = False

        for task in self.tasks:
            deadline = datetime.strptime(task["deadline"], "%Y-%m-%d %H:%M")
            notify_timing = task.get("notify_timing", "1日前")
            notify_delta = NOTIFY_OPTIONS.get(notify_timing, timedelta(days=1))

            # 当日通知の場合は、期限日の0:00以降、期限前なら通知対象にする
            if notify_timing == "当日":
                should_notify = (
                    not task["done"]
                    and not task["notified"]
                    and now.date() == deadline.date()
                    and now <= deadline
                )
            else:
                should_notify = (
                    not task["done"]
                    and not task["notified"]
                    and timedelta(0) <= deadline - now <= notify_delta
                )

            if should_notify:
                try:
                    send_email(
                        self.user_email,
                        "タスク期限通知",
                        f"以下タスクの期限が近づいています。\n\n"
                        f"タスク: {task['text']}\n"
                        f"カテゴリ: {task.get('category', 'その他')}\n"
                        f"優先度: {task.get('priority', '中')}\n"
                        f"期限: {task['deadline']}\n"
                        f"通知タイミング: {task.get('notify_timing', '1日前')}"
                    )
                    task["notified"] = True
                    changed = True

                except Exception as e:
                    print("メール送信エラー:", e)

        if changed:
            self.save()

        self.update_listbox()
        self.root.after(60000, self.check_deadline)


if __name__ == "__main__":
    root = tk.Tk()
    LoginWindow(root)
    root.mainloop()
