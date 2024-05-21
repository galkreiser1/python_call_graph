def schedule_event(events, date, event):
    events[date] = event
    return events

def update_event(events, date, new_event):
    events[date] = new_event
    return events

def list_events(events):
    return sorted(events.items())

def cancel_event(events, date):
    if date in events:
        del events[date]
    return events

def update_event_date(events, old_date, new_date):
    if old_date in events:
        event = events.pop(old_date)
        events[new_date] = event
    return events

def manage_events(events):
    events = schedule_event(events, "2024-05-10", "Doctor's Appointment")
    events = update_event(events, "2024-05-10", "Annual Check-up")
    events = schedule_event(events, "2024-05-12", "Meeting with Client")
    events = update_event_date(events, "2024-05-12", "2024-05-13")
    return events

def main():
    events = {}
    events = manage_events(events)
    all_events = list_events(events)
    events = cancel_event(events, "2024-05-10")
    
    print("Scheduled Events:", all_events)
    print("Events after cancellation:", events)

main()
