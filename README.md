# Long Term Plan Assistant - Echo

## Why??

Most long term goals do not fail because people are unmotivated.
They fail because the goals are complex.

Applying for a visa, learning French for an exam, getting a driver’s license, or preparing for graduate school all involve policies, timelines, multiple decision points, and information that is hard to navigate.

This project explores a simple question:

What if an assistant could stay with you over time, remember your goals, break them down into milestones, help you choose the right path, and remind you when action is needed?

That is what the Long Term Plan Assistant is built for.

---

## What is Long Term Plan Assistant

Long Term Plan Assistant is an AI powered planning system designed to help users execute complex long term goals.

Instead of providing one time advice, the assistant supports the entire journey by:
- breaking large goals into structured milestones
- collecting and organizing relevant information for each step
- tracking progress over time
- issuing reminders before important deadlines

The focus is not just on planning, but on long term execution.

---

## Core Features

- Conversational goal setting
- Automatic milestone breakdown with timelines
- Persistent long term memory across conversations
- Decision support through information collection and comparison
- Progress tracking and risk awareness
- Deadline based reminders and notifications
- Calendar view with printable and exportable events
- Dashboard showing active goals and upcoming milestones
- Privacy and UI customization options 
---

## How Backboard.io is used

Backboard.io plays a central role in enabling long term planning.

We create a dedicated Backboard thread called `My Life Plan` that serves as persistent memory for the assistant.

This memory stores:
- long term goals
- user preferences and constraints
- generated milestones and timelines
- historical decisions and updates

On every user interaction:
1. The backend retrieves relevant memory from Backboard.io
2. The memory is injected into the prompt sent to the language model
3. The assistant continues planning instead of starting from scratch

When a reminder is required, the model outputs a structured action instruction.
Our backend interprets this instruction and schedules in app notifications or calendar events.

This allows planning decisions to turn into real world actions.

---

## System Architecture

Frontend:
- React
- Tailwind CSS

Backend:
- FastAPI

Core design:
- Brain: language model responsible for reasoning and planning
- Memory: Backboard.io for long term state and context
- Hands: tool functions that trigger reminders and calendar events

---

## Main Pages

- Chat
  Used to define goals, update progress, and generate next steps

- Dashboard
  Displays active goals, milestones, tasks for today, and risk alerts

- Calendar
  Visualizes deadlines and milestones with support for printing and ICS export

- Settings
  Controls privacy options, display preferences, and notification behavior

---

## Example Use Cases

- Learning French with the goal of passing a specific exam
- Applying for visas or immigration programs
- Preparing for graduate school applications
- Long term professional or personal development planning

---

## Project Status

This project is currently in MVP stage and focuses on demonstrating:
- persistent memory driven planning
- milestone based execution
- reminder and tracking mechanisms

Future work includes deeper personalization, richer data sources, and more advanced risk detection.


## Backend (FastAPI)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install fastapi uvicorn
python main.py
```

API: http://localhost:8000

## Frontend (Vite)

```powershell
cd frontend
npm install
npm run dev
```

Web: http://localhost:5173
---

## Contributors

- Karen Chen Lai
- Mary Li
- Shengyi Zhong
- Cleo Tang

Contributions, feedback, and suggestions are welcome.
