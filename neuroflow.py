#!/usr/bin/env python3
"""
NeuroFlow Scheduler  -  Terminal Edition  v2
=============================================
A smart, interactive task scheduler that runs entirely in your terminal.
Uses the Rich library for beautiful, colourful output.

FIX NOTE (v2)
-------------
Removed all rich.Text object usage.  Rich internally calls .translate()
(a plain-str method) on Text objects during width measurement, which caused:
    AttributeError: 'Text' object has no attribute 'translate'

Solution: use ONLY string-based Rich markup everywhere.  No Text objects.
Also fixed a broken f-string in action_clear_all where the closing tag
{COL_RED} was not interpolated.

Scheduling algorithms
---------------------
  1. Priority Scheduling           - High -> Medium -> Low
  2. Earliest Deadline First (EDF) - closest deadline runs first
  3. Shortest Job First (SJF)      - shortest duration runs first

Tasks are saved to tasks.json and survive restarts.

Usage
-----
  python neuroflow.py
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import List, Dict, Tuple

# ── Rich imports ──────────────────────────────────────────────────────────────
# NOTE: rich.text.Text is intentionally NOT imported.
#       It was the root cause of the AttributeError.
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich.rule import Rule
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markup import escape   # escapes user content so it is safe in markup
from rich import box

# ── Single shared console ─────────────────────────────────────────────────────
console = Console()


# ══════════════════════════════════════════════════════════════════════════════
#  CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

# JSON file that stores tasks between runs
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks.json")

# Priority sort rank  (lower = more urgent)
PRIORITY_ORDER: Dict[str, int] = {"High": 1, "Medium": 2, "Low": 3}

# Pastel hex colours
COL_LAVENDER = "#bdb2ff"   # headings / borders
COL_BLUE     = "#a0c4ff"   # prompts  / accents
COL_PINK     = "#ffc6d3"   # decorative
COL_GREEN    = "#6bcb77"   # success  / Low priority
COL_YELLOW   = "#ffd93d"   # warnings / Medium priority
COL_RED      = "#ff6b6b"   # errors   / High priority
COL_DIM      = "#888888"   # secondary text

PRIORITY_COLOR: Dict[str, str] = {
    "High":   COL_RED,
    "Medium": COL_YELLOW,
    "Low":    COL_GREEN,
}
PRIORITY_EMOJI: Dict[str, str] = {
    "High":   "🔴",
    "Medium": "🟡",
    "Low":    "🟢",
}

# Algorithm definitions
ALGORITHMS: Dict[str, Dict] = {
    "1": {
        "key":  "priority",
        "name": "Priority Scheduling",
        "icon": "🏆",
        "desc": "Tasks run High -> Medium -> Low.  Ties broken by earliest deadline.",
    },
    "2": {
        "key":  "edf",
        "name": "Earliest Deadline First (EDF)",
        "icon": "⏰",
        "desc": "Task with the closest deadline always runs first.  Minimises missed deadlines.",
    },
    "3": {
        "key":  "sjf",
        "name": "Shortest Job First (SJF)",
        "icon": "⚡",
        "desc": "Shortest task (by duration) runs first.  Maximises throughput & minimises wait time.",
    },
}

# NeuroBot mood -> colour
MOOD_COLOR: Dict[str, str] = {
    "info":    COL_BLUE,
    "success": COL_GREEN,
    "warn":    COL_YELLOW,
    "error":   COL_RED,
    "tip":     COL_LAVENDER,
}

ROBOT_ART = (
    "  +-------+\n"
    "  | o   o |\n"
    "  |   v   |\n"
    "  +---+---+\n"
    "   +--+--+\n"
    "   |  *  |\n"
    "   +-----+"
)


# ══════════════════════════════════════════════════════════════════════════════
#  PERSISTENT STORAGE
# ══════════════════════════════════════════════════════════════════════════════

def load_tasks() -> List[Dict]:
    """Read tasks.json.  Returns [] when the file is missing or corrupted."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def save_tasks(tasks: List[Dict]) -> None:
    """Write the task list to tasks.json."""
    with open(DATA_FILE, "w", encoding="utf-8") as fh:
        json.dump(tasks, fh, indent=2)


# ══════════════════════════════════════════════════════════════════════════════
#  NEUROBOT  -  robot assistant speech bubbles
# ══════════════════════════════════════════════════════════════════════════════

def neurobot_say(message: str, mood: str = "info") -> None:
    """
    Print a NeuroBot speech-bubble Panel.

    Both the Panel title and content are plain markup strings -
    no Text objects, no Align wrappers on the subtitle.

    Parameters
    ----------
    message : str   Plain string that may contain Rich markup.
                    Escape user-supplied content with rich.markup.escape().
    mood    : str   'info' | 'success' | 'warn' | 'error' | 'tip'
    """
    color = MOOD_COLOR.get(mood, COL_BLUE)
    console.print()
    console.print(Panel(
        f"[bold {color}]{message}[/bold {color}]",
        title=f"[bold {COL_LAVENDER}]🤖  NeuroBot[/bold {COL_LAVENDER}]",
        border_style=COL_LAVENDER,
        padding=(0, 2),
        expand=False,
    ))
    time.sleep(0.35)


# ══════════════════════════════════════════════════════════════════════════════
#  UI HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def clear_screen() -> None:
    """Clear the terminal on Windows and Unix."""
    os.system("cls" if os.name == "nt" else "clear")


def show_header() -> None:
    """
    Print the branded NeuroFlow header panel.

    KEY FIX: uses a plain markup string passed to Align.center().
    No Text objects, no Align() wrapped around a Text as a Panel subtitle.
    """
    # Plain f-string with Rich markup - safe for Align.center()
    content = (
        f"[bold {COL_LAVENDER}]Neuro[/bold {COL_LAVENDER}]"
        f"[bold {COL_BLUE}]Flow[/bold {COL_BLUE}]"
        f"[bold white]  Scheduler[/bold white]  "
        f"[{COL_PINK}]* Terminal Edition *[/{COL_PINK}]"
    )
    # subtitle must be a plain str - NOT Align(Text(...))
    subtitle = (
        f"[{COL_DIM}]Smart Task Scheduling  .  Priority  .  EDF  .  SJF[/{COL_DIM}]"
    )

    console.print()
    console.print(Panel(
        Align.center(content),   # Align wrapping a str - always safe
        subtitle=subtitle,       # plain str - always safe
        border_style=COL_LAVENDER,
        padding=(1, 6),
    ))
    console.print()


def show_menu() -> None:
    """Render the main navigation menu as a rounded Rich table."""
    table = Table(
        box=box.ROUNDED,
        border_style=COL_LAVENDER,
        show_header=False,
        padding=(0, 2),
        expand=False,
    )
    table.add_column(style=f"bold {COL_BLUE}", width=5)
    table.add_column(style="white")

    for key, label in [
        ("1", "  Add Task"),
        ("2", "  View All Tasks"),
        ("3", "  Schedule Tasks"),
        ("4", "  Delete a Task"),
        ("5", "  Clear All Tasks"),
        ("0", "  Exit"),
    ]:
        # Use \[ to print a literal [ so Rich does not parse [1] as a markup tag
        table.add_row(f"\\[{key}]", label)

    console.print(Align.center(table))
    console.print()


def build_task_table(
    task_list: List[Dict],
    title: str = "Tasks",
    show_order_number: bool = False,
) -> Table:
    """
    Build a Rich Table for a list of task dicts.

    All cell values are plain strings with markup - no Text objects.
    User-supplied content (task names) is passed through escape().

    Parameters
    ----------
    task_list         : list of task dicts
    title             : table heading text
    show_order_number : True  -> show execution order 1, 2, 3 ...
                        False -> show the stored task ID
    """
    table = Table(
        title=f"[bold {COL_LAVENDER}]{title}[/bold {COL_LAVENDER}]",
        box=box.ROUNDED,
        border_style=COL_BLUE,
        header_style=f"bold {COL_LAVENDER}",
        show_lines=True,
    )

    id_header = "#" if show_order_number else "ID"
    table.add_column(id_header,    justify="center", style=f"bold {COL_BLUE}", width=4)
    table.add_column("Task Name",  style="bold white",                          min_width=22)
    table.add_column("Priority",   justify="center",                            width=12)
    table.add_column("Duration",   justify="center",  style=f"dim {COL_DIM}",  width=10)
    table.add_column("Deadline",   style=f"dim {COL_DIM}",                     width=20)

    for idx, task in enumerate(task_list, start=1):
        p_color = PRIORITY_COLOR.get(task["priority"], "white")
        p_emoji = PRIORITY_EMOJI.get(task["priority"], "")

        # Human-readable deadline
        try:
            dt = datetime.fromisoformat(task["deadline"])
            deadline_str = dt.strftime("%b %d, %Y  %H:%M")
        except (ValueError, TypeError):
            deadline_str = str(task["deadline"])

        row_id = str(idx) if show_order_number else str(task["id"])

        table.add_row(
            row_id,
            escape(task["name"]),    # escape so special chars don't break markup
            f"[bold {p_color}]{p_emoji} {task['priority']}[/bold {p_color}]",
            f"{task['duration']} min",
            deadline_str,
        )

    return table


def pause() -> None:
    """Wait for Enter before returning to the main menu."""
    console.print()
    Prompt.ask(f"[{COL_DIM}]  Press Enter to continue ...[/{COL_DIM}]", default="")


# ══════════════════════════════════════════════════════════════════════════════
#  SCHEDULING ALGORITHMS
# ══════════════════════════════════════════════════════════════════════════════

def run_schedule(task_list: List[Dict], algorithm: str) -> Tuple[List[Dict], str]:
    """
    Sort task_list using the chosen algorithm.

    Returns
    -------
    (sorted_task_list, reasoning_string)
    """
    copy = list(task_list)    # never mutate the caller's list

    if algorithm == "priority":
        # Primary key  : priority rank (High=1, Medium=2, Low=3)
        # Secondary key: deadline (ISO string - sorts lexicographically)
        result = sorted(copy, key=lambda t: (PRIORITY_ORDER[t["priority"]], t["deadline"]))
        reason = (
            "Tasks are ordered by urgency: High -> Medium -> Low.\n"
            "When two tasks share the same priority the one due sooner runs first."
        )

    elif algorithm == "edf":
        # Primary key  : deadline
        # Secondary key: priority rank
        result = sorted(copy, key=lambda t: (t["deadline"], PRIORITY_ORDER[t["priority"]]))
        reason = (
            "Tasks are ordered by deadline - the task due soonest runs first.\n"
            "EDF is provably optimal for minimising missed deadlines.\n"
            "Equal-deadline tasks are resolved by priority."
        )

    elif algorithm == "sjf":
        # Primary key  : duration (minutes)
        # Secondary key: deadline
        result = sorted(copy, key=lambda t: (t["duration"], t["deadline"]))
        reason = (
            "Tasks are ordered by estimated duration - the shortest task runs first.\n"
            "SJF minimises average waiting time and maximises task throughput.\n"
            "Tasks of equal length are broken by their deadline."
        )

    else:
        result = copy
        reason = "No sorting applied - unknown algorithm."

    return result, reason


# ══════════════════════════════════════════════════════════════════════════════
#  ACTION FUNCTIONS  (one per menu option)
# ══════════════════════════════════════════════════════════════════════════════

def action_add_task(tasks: List[Dict]) -> List[Dict]:
    """Prompt for task details, validate, persist, and give NeuroBot feedback."""
    console.print()
    console.print(Rule(
        f"[bold {COL_LAVENDER}]  Add New Task[/bold {COL_LAVENDER}]",
        style=COL_LAVENDER,
    ))
    console.print()

    # ── Task name ─────────────────────────────────────────────────────────────
    name = Prompt.ask(f"[bold {COL_BLUE}]  Task name[/bold {COL_BLUE}]").strip()
    if not name:
        neurobot_say("Task name cannot be empty!  Please try again.", mood="error")
        return tasks

    # ── Deadline ──────────────────────────────────────────────────────────────
    while True:
        dl_raw = Prompt.ask(
            f"[bold {COL_BLUE}]  Deadline[/bold {COL_BLUE}]"
            f"  [{COL_DIM}]YYYY-MM-DD HH:MM[/{COL_DIM}]"
        ).strip()
        try:
            dl_dt = datetime.strptime(dl_raw, "%Y-%m-%d %H:%M")
            deadline_iso = dl_dt.isoformat()
            break
        except ValueError:
            console.print(
                f"  [{COL_RED}]Invalid format.[/{COL_RED}]"
                "  Use  YYYY-MM-DD HH:MM  e.g.  2025-06-30 18:00"
            )

    # ── Priority ──────────────────────────────────────────────────────────────
    priority = Prompt.ask(
        f"[bold {COL_BLUE}]  Priority[/bold {COL_BLUE}]",
        choices=["High", "Medium", "Low"],
        default="Medium",
    )

    # ── Duration ──────────────────────────────────────────────────────────────
    while True:
        dur_raw = Prompt.ask(
            f"[bold {COL_BLUE}]  Duration[/bold {COL_BLUE}]"
            f"  [{COL_DIM}]minutes[/{COL_DIM}]"
        ).strip()
        try:
            duration = int(dur_raw)
            if duration <= 0:
                raise ValueError("must be positive")
            break
        except ValueError:
            console.print(f"  [{COL_RED}]Please enter a positive whole number.[/{COL_RED}]")

    # ── Build task and save ───────────────────────────────────────────────────
    new_id = max((t["id"] for t in tasks), default=0) + 1
    task: Dict = {
        "id":       new_id,
        "name":     name,
        "deadline": deadline_iso,
        "priority": priority,
        "duration": duration,
    }
    tasks.append(task)
    save_tasks(tasks)

    console.print()
    console.print(build_task_table([task], title="Task Added"))

    # ── NeuroBot smart suggestions ────────────────────────────────────────────
    bot_messages = [f'Task "{escape(name)}" added successfully!']

    if priority == "High":
        bot_messages.append(
            "High priority detected!\n"
            "  Option 3 - Priority Scheduling will put this task at the front."
        )
    if duration <= 15:
        bot_messages.append(
            "Short task detected  (15 min or less).\n"
            "  Option 3 - Shortest Job First will knock it out early!"
        )
    try:
        hours_left = (dl_dt - datetime.now()).total_seconds() / 3600
        if 0 < hours_left < 24:
            bot_messages.append(
                "Deadline is within 24 hours!\n"
                "  Option 3 - Earliest Deadline First is strongly recommended."
            )
        elif hours_left <= 0:
            bot_messages.append(
                "Warning: this deadline has already passed!\n"
                "  Double-check the date you entered."
            )
    except Exception:
        pass

    for msg in bot_messages:
        neurobot_say(msg, mood="success" if "added successfully" in msg else "warn")

    return tasks


def action_view_tasks(tasks: List[Dict]) -> None:
    """Display all tasks in a formatted table."""
    console.print()
    if not tasks:
        neurobot_say("The queue is empty!  Use option 1 to add your first task.", mood="info")
        return
    console.print(build_task_table(tasks, title=f"Task Queue  ({len(tasks)} task(s))"))
    console.print()
    neurobot_say(
        f"You have {len(tasks)} task(s) in the queue.\n"
        "Ready to schedule? Select option 3!",
        mood="tip",
    )


def action_schedule(tasks: List[Dict]) -> None:
    """Pick an algorithm, animate a spinner, then show the ordered plan."""
    console.print()
    if not tasks:
        neurobot_say("Nothing to schedule - add some tasks first!", mood="warn")
        return

    # ── Algorithm picker ──────────────────────────────────────────────────────
    console.print(Rule(
        f"[bold {COL_LAVENDER}]  Choose a Scheduling Algorithm[/bold {COL_LAVENDER}]",
        style=COL_LAVENDER,
    ))
    console.print()

    for key, info in ALGORITHMS.items():
        console.print(
            f"  [bold {COL_BLUE}]\\[{key}][/bold {COL_BLUE}]  "
            f"{info['icon']}  [bold white]{info['name']}[/bold white]"
        )
        console.print(f"       [{COL_DIM}]{info['desc']}[/{COL_DIM}]")
        console.print()

    choice = Prompt.ask(
        f"[bold {COL_LAVENDER}]  Select algorithm[/bold {COL_LAVENDER}]",
        choices=["1", "2", "3"],
        default="1",
    )
    info = ALGORITHMS[choice]

    # ── Animated spinner ──────────────────────────────────────────────────────
    console.print()
    with Progress(
        SpinnerColumn(style=COL_LAVENDER),
        TextColumn(
            f"[bold {COL_BLUE}]Scheduling {len(tasks)} task(s)"
            f" using {info['name']} ...[/bold {COL_BLUE}]"
        ),
        transient=True,
    ) as progress:
        progress.add_task("schedule")
        time.sleep(1.4)

    ordered_tasks, reasoning = run_schedule(tasks, info["key"])

    # ── Reasoning panel ───────────────────────────────────────────────────────
    console.print()
    console.print(Panel(
        f"[bold {COL_YELLOW}]Reasoning[/bold {COL_YELLOW}]\n\n"
        f"[white]{reasoning}[/white]",
        title=f"[bold {COL_YELLOW}]{info['icon']}  {info['name']}[/bold {COL_YELLOW}]",
        border_style=COL_YELLOW,
        padding=(0, 2),
    ))
    console.print()

    # ── Ordered execution table ───────────────────────────────────────────────
    console.print(build_task_table(
        ordered_tasks,
        title=f"Execution Order  -  {info['name']}",
        show_order_number=True,
    ))
    console.print()

    # ── NeuroBot result comment ───────────────────────────────────────────────
    result_msgs = {
        "priority": "Priority scheduling complete!\n  Critical tasks are at the top where they belong.",
        "edf":      "EDF scheduling complete!\n  You'll hit every deadline - stress-free!",
        "sjf":      "SJF scheduling complete!\n  Quick wins first - great for productivity!",
    }
    neurobot_say(result_msgs[info["key"]], mood="success")


def action_delete_task(tasks: List[Dict]) -> List[Dict]:
    """Delete a single task by its ID."""
    console.print()
    if not tasks:
        neurobot_say("The queue is already empty - nothing to delete!", mood="info")
        return tasks

    console.print(build_task_table(tasks, title="Select a Task to Delete"))
    console.print()

    valid_ids = {str(t["id"]) for t in tasks}
    raw = Prompt.ask(
        f"[bold {COL_BLUE}]  Enter Task ID to delete[/bold {COL_BLUE}]"
        f"  [{COL_DIM}]or 'c' to cancel[/{COL_DIM}]"
    ).strip()

    if raw.lower() == "c":
        neurobot_say("Deletion cancelled - tasks are safe!", mood="info")
        return tasks

    if raw not in valid_ids:
        neurobot_say(f"No task with ID '{escape(raw)}' found.  Try again!", mood="error")
        return tasks

    task_id = int(raw)
    deleted  = next(t for t in tasks if t["id"] == task_id)
    tasks    = [t for t in tasks if t["id"] != task_id]
    save_tasks(tasks)

    neurobot_say(
        f'Task "{escape(deleted["name"])}" has been removed from the queue.',
        mood="warn",
    )
    return tasks


def action_clear_all(tasks: List[Dict]) -> List[Dict]:
    """Clear every task after explicit confirmation."""
    console.print()
    if not tasks:
        neurobot_say("The queue is already empty - nothing to clear!", mood="info")
        return tasks

    # FIX: both string halves are f-strings so COL_RED is interpolated correctly
    confirmed = Confirm.ask(
        f"[bold {COL_RED}]  Clear all {len(tasks)} task(s)?  "
        f"This cannot be undone.[/bold {COL_RED}]"
    )
    if confirmed:
        tasks.clear()
        save_tasks(tasks)
        neurobot_say("All tasks cleared.  Fresh start!", mood="warn")
    else:
        neurobot_say("Cancelled - your tasks are safe!", mood="info")
    return tasks


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN LOOP
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    """Entry point: load tasks, greet the user, run the interactive menu loop."""

    tasks: List[Dict] = load_tasks()

    clear_screen()
    show_header()

    # ── Welcome greeting ──────────────────────────────────────────────────────
    if tasks:
        neurobot_say(
            f"Welcome back!  Found [bold]{len(tasks)}[/bold] task(s) from your last session.\n"
            "Select option 2 to review them or option 3 to schedule right away.",
            mood="info",
        )
    else:
        neurobot_say(
            "Hi!  I'm [bold]NeuroBot[/bold] - your scheduling assistant.\n"
            "Add tasks with option 1 and I'll help you schedule them intelligently!\n\n"
            f"[{COL_DIM}]{ROBOT_ART}[/{COL_DIM}]",
            mood="tip",
        )

    # ── Interactive menu loop ─────────────────────────────────────────────────
    while True:
        console.print()
        show_menu()

        choice = Prompt.ask(
            f"[bold {COL_LAVENDER}]  Select an option[/bold {COL_LAVENDER}]",
            choices=["0", "1", "2", "3", "4", "5"],
            default="1",
        )

        if   choice == "1":  tasks = action_add_task(tasks)
        elif choice == "2":  action_view_tasks(tasks)
        elif choice == "3":  action_schedule(tasks)
        elif choice == "4":  tasks = action_delete_task(tasks)
        elif choice == "5":  tasks = action_clear_all(tasks)
        elif choice == "0":
            console.print()
            neurobot_say("Goodbye!  Keep crushing those deadlines!", mood="tip")
            console.print()
            sys.exit(0)

        pause()
        clear_screen()
        show_header()


# ── Entry guard ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
