#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('app.db')
cursor = conn.cursor()

print("\n" + "="*80)
print("GOALS")
print("="*80)
cursor.execute("SELECT title, type, deadline, status FROM goals")
for row in cursor.fetchall():
    print(f"• {row[0]} ({row[1]})")
    print(f"  Deadline: {row[2]}, Status: {row[3]}")

print("\n" + "="*80)
print("MILESTONES")
print("="*80)
cursor.execute("SELECT title, target_date, status FROM milestones")
for row in cursor.fetchall():
    print(f"• {row[0]}")
    print(f"  Target: {row[1]}, Status: {row[2]}")

print("\n" + "="*80)
print("TASKS")
print("="*80)
cursor.execute("SELECT title, due_date, priority, status FROM tasks")
for row in cursor.fetchall():
    print(f"• {row[0]}")
    print(f"  Due: {row[1]}, Priority: {row[2]}, Status: {row[3]}")

print("\n")
conn.close()
