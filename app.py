import smtplib
import os
from email.mime.text import MIMEText
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# タスクを保存するリストとIDカウンター
task_id_counter = 0
tasks = []


@app.route("/")
def index():
    return render_template("index.html", tasks=tasks)


@app.route("/add", methods=["POST"])
def add():
    global task_id_counter
    text = request.form.get("text")
    deadline = request.form.get("deadline")
    priority = request.form.get("priority", "中")
    category = request.form.get("category", "その他")
    notify_timing = request.form.get("notify_timing", "1日前")

    if text:
        tasks.append({
            "id": task_id_counter,
            "text": text,
            "done": 0,
            "deadline": deadline,
            "priority": priority,
            "category": category,
            "notify_timing": notify_timing
        })
        task_id_counter += 1

    return redirect(url_for("index"))


@app.route("/complete/<int:task_id>")
def complete(task_id):
    for task in tasks:
        if task["id"] == task_id:
            task["done"] = 1
            break
    return redirect(url_for("index"))


@app.route("/delete/<int:task_id>")
def delete(task_id):
    global tasks
    tasks = [t for t in tasks if t["id"] != task_id]
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)