import sqlite3
from datetime import datetime, timedelta
import uuid

# Connect to database
conn = sqlite3.connect('/Users/autumn/Documents/Projects/ProjectReminder/reminders.db')
cursor = conn.cursor()

# Example reminders with variety
reminders = [
    {
        'text': 'Call dentist for checkup appointment',
        'priority': 'important',
        'due_date': (datetime.now() + timedelta(days=1)).date().isoformat(),
        'due_time': '14:00:00',
        'category': 'health'
    },
    {
        'text': 'Buy groceries (milk, eggs, bread)',
        'priority': 'urgent',
        'due_date': datetime.now().date().isoformat(),
        'due_time': '18:00:00',
        'category': 'errands'
    },
    {
        'text': 'Team standup meeting',
        'priority': 'important',
        'due_date': (datetime.now() + timedelta(days=1)).date().isoformat(),
        'due_time': '10:00:00',
        'category': 'work'
    },
    {
        'text': 'Pick up dry cleaning',
        'priority': 'chill',
        'due_date': (datetime.now() + timedelta(days=2)).date().isoformat(),
        'category': 'errands'
    },
    {
        'text': 'Finish quarterly report',
        'priority': 'urgent',
        'due_date': (datetime.now() + timedelta(days=3)).date().isoformat(),
        'due_time': '17:00:00',
        'category': 'work'
    },
    {
        'text': 'Water the plants',
        'priority': 'chill',
        'due_date': datetime.now().date().isoformat(),
        'category': 'home'
    },
    {
        'text': 'Read book chapter 5',
        'priority': 'someday',
        'category': 'personal'
    },
    {
        'text': 'Birthday gift for Mom',
        'priority': 'important',
        'due_date': (datetime.now() + timedelta(days=7)).date().isoformat(),
        'category': 'personal'
    },
    {
        'text': 'Pay electricity bill',
        'priority': 'urgent',
        'due_date': (datetime.now() + timedelta(days=2)).date().isoformat(),
        'category': 'errands'
    },
    {
        'text': 'Schedule oil change',
        'priority': 'chill',
        'due_date': (datetime.now() + timedelta(days=10)).date().isoformat(),
        'category': 'errands'
    }
]

# Insert reminders
for reminder in reminders:
    reminder_id = str(uuid.uuid4())
    now = datetime.now().isoformat()

    cursor.execute('''
        INSERT INTO reminders
        (id, text, priority, status, due_date, due_time, category, source, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        reminder_id,
        reminder['text'],
        reminder['priority'],
        'pending',
        reminder.get('due_date'),
        reminder.get('due_time'),
        reminder.get('category', 'personal'),
        'manual',
        now,
        now
    ))

conn.commit()
conn.close()

print(f"✅ Added {len(reminders)} example reminders to the database")
