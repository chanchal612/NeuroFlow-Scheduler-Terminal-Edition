# 🧠 NeuroFlow Scheduler — Terminal Edition

> A smart, interactive task scheduler that runs entirely in your terminal.
> Powered by intelligent scheduling algorithms and guided by **NeuroBot**, your AI-style robot assistant.

---

## ✨ Features

- **3 Scheduling Algorithms**
  - 🏆 **Priority Scheduling** — High → Medium → Low urgency
  - ⏰ **Earliest Deadline First (EDF)** — closest deadline runs first
  - ⚡ **Shortest Job First (SJF)** — quickest task runs first
- **🤖 NeuroBot Assistant** — gives real-time tips after every action
- **💾 Persistent Storage** — tasks saved to `tasks.json`, survive restarts
- **🎨 Pastel terminal UI** — colourful tables, panels, and spinners via Rich
- **✅ Full task CRUD** — add, view, schedule, delete, clear
- **Smart tie-breaking** — equal-priority/equal-deadline tasks always resolve deterministically

---

## 📁 Project Structure

```
neuroflow-scheduler/
├── neuroflow.py        ← main application (single file)
├── tasks.json          ← auto-generated task storage (gitignored)
├── requirements.txt    ← Python dependencies
├── .gitignore
└── README.md
```

---

## 🚀 Quick Start (Warp Terminal)

### 1 — Clone or create the project folder

```bash
# If you're cloning from GitHub:
git clone https://github.com/YOUR_USERNAME/neuroflow-scheduler.git
cd neuroflow-scheduler

# Or navigate to the existing folder:
cd C:\Users\USER\neuroflow-scheduler
```

### 2 — Create & activate a virtual environment

```bash
# Create
python -m venv venv

# Activate (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activate (Windows CMD)
venv\Scripts\activate.bat

# Activate (macOS / Linux)
source venv/bin/activate
```

### 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### 4 — Run the app

```bash
python neuroflow.py
```

---

## 🎮 How to Use

Once the app is running you'll see the main menu:

```
  [1]  ➕  Add Task
  [2]  📋  View All Tasks
  [3]  🚀  Schedule Tasks
  [4]  🗑️  Delete a Task
  [5]  ❌  Clear All Tasks
  [0]  👋  Exit
```

### Adding a task
Select **[1]** and enter:
- **Task name** — e.g. `Submit assignment`
- **Deadline** — format `YYYY-MM-DD HH:MM` e.g. `2025-06-30 18:00`
- **Priority** — `High` / `Medium` / `Low`
- **Duration** — estimated minutes e.g. `45`

NeuroBot will immediately suggest the best algorithm based on your input.

### Scheduling tasks
Select **[3]**, then choose an algorithm:
- `[1]` Priority Scheduling
- `[2]` Earliest Deadline First
- `[3]` Shortest Job First

The app shows a spinner, then displays the full ordered execution table with a reasoning panel explaining *why* that order was chosen.

---

## 🤖 NeuroBot Messages

| Situation | NeuroBot says |
|-----------|--------------|
| Task added | ✅ "Task added successfully!" |
| High priority detected | 🔴 "Priority Scheduling will put this at the front" |
| Short task (≤15 min) | ⚡ "SJF will knock it out early!" |
| Deadline within 24 h | ⏰ "EDF is strongly recommended" |
| Scheduling complete | 🏆 / ⏰ / ⚡ algorithm-specific feedback |
| Past deadline | 🚨 "This deadline has already passed!" |

---

## 🔁 Git & GitHub Workflow

### First-time setup

```bash
# 1. Initialise the repo
git init

# 2. Stage all files
git add .

# 3. First commit
git commit -m "Initial commit - NeuroFlow Scheduler Terminal Edition"

# 4. Connect to GitHub (replace with your repo URL)
git remote add origin https://github.com/YOUR_USERNAME/neuroflow-scheduler.git

# 5. Push
git branch -M main
git push -u origin main
```

### Daily workflow

```bash
git add .
git commit -m "Feature: describe your change here"
git push
```

### Running a cloned copy on a new machine

```bash
git clone https://github.com/YOUR_USERNAME/neuroflow-scheduler.git
cd neuroflow-scheduler
python -m venv venv
.\venv\Scripts\Activate.ps1   # Windows
pip install -r requirements.txt
python neuroflow.py
```

---

## ⚙️ Algorithm Details

### Priority Scheduling
Sort key: `(priority_rank, deadline)`
Tasks are ordered High (1) → Medium (2) → Low (3).
Equal-priority tasks fall back to the earliest deadline.

### Earliest Deadline First (EDF)
Sort key: `(deadline, priority_rank)`
The task with the nearest deadline always executes first.
Provably optimal for minimising missed deadlines in preemptive systems.

### Shortest Job First (SJF)
Sort key: `(duration, deadline)`
The fastest task runs first, maximising throughput and minimising average waiting time.
Ties resolved by the nearest deadline.

---

## 🛠️ Requirements

| Requirement | Version |
|-------------|---------|
| Python | ≥ 3.8 |
| rich | ≥ 13.0.0 |

---

## 📸 Screenshots

> *(Add terminal screenshots here after your first run)*

---

## 📄 License

MIT — free to use, modify, and share.
