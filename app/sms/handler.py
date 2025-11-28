"""SMS alarm handler for creating database records"""

from datetime import datetime, timezone, timedelta
from .. import db

def create_alarm_from_sms(alarm_data, timestamp):
    """Create alarm record from SMS data or link to existing duplicate"""
    
    # Determine alarm kind using parser
    from .parser import detect_alarm_kind
    kind = detect_alarm_kind(alarm_data['raw_content'])
    
    occurred_at = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    
    # Check for existing duplicate alarm within a time window (2 minutes)
    # Match on: what, where_location, alarm_type, and occurred_at within 2 minutes
    time_window_start = occurred_at - timedelta(minutes=2)
    time_window_end = occurred_at + timedelta(minutes=2)
    
    existing_alarm = db.sql_one("""
        SELECT a.id
        FROM alarms a
        WHERE a.source = 'SMS'
        AND (a.what IS NOT DISTINCT FROM %s)
        AND (a.where_location IS NOT DISTINCT FROM %s)
        AND (a.alarm_type IS NOT DISTINCT FROM %s)
        AND a.occurred_at BETWEEN %s AND %s
        AND a.ended_at IS NULL
        ORDER BY a.occurred_at DESC
        LIMIT 1
    """, alarm_data.get('what'), alarm_data.get('where'), 
         alarm_data.get('alarm_type'), time_window_start, time_window_end)
    
    if existing_alarm:
        # Duplicate alarm found - add departments to existing alarm
        alarm_id = existing_alarm[0]
        departments = alarm_data.get('all_departments', [])
        if not departments and alarm_data.get('department_code'):
            departments = [alarm_data['department_code']]
        
        if not departments:
            print(f"Warning: No departments found for duplicate alarm {alarm_id}")
        
        for dept_code in departments:
            # Use case-insensitive lookup since database might have mixed case (LuFBK vs LUFBK)
            dept = db.sql_one("SELECT id FROM departments WHERE UPPER(code) = UPPER(%s)", dept_code)
            if dept:
                # Use INSERT ... ON CONFLICT to avoid duplicate department assignments
                db.sql_exec("""
                    INSERT INTO alarm_departments (alarm_id, department_id)
                    VALUES (%s, %s)
                    ON CONFLICT (alarm_id, department_id) DO NOTHING
                """, alarm_id, dept[0])
            else:
                print(f"Warning: Department {dept_code} not found")
        
        return alarm_id
    else:
        # No duplicate found - create new alarm
        alarm_id = db.sql_one("""
            INSERT INTO alarms (kind, description, occurred_at, source, alarm_type, what, where_location, who_called)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, kind, alarm_data['description'], 
             occurred_at, 'SMS',
             alarm_data.get('alarm_type'), alarm_data.get('what'), 
             alarm_data.get('where'), alarm_data.get('who_called'))
        
        # Assign to all departments mentioned in the SMS
        departments = alarm_data.get('all_departments', [])
        if not departments and alarm_data.get('department_code'):
            departments = [alarm_data['department_code']]
        
        if not departments:
            print(f"Warning: No departments found for alarm {alarm_id[0]}")
        
        for dept_code in departments:
            # Use case-insensitive lookup since database might have mixed case (LuFBK vs LUFBK)
            dept = db.sql_one("SELECT id FROM departments WHERE UPPER(code) = UPPER(%s)", dept_code)
            if dept:
                db.sql_exec("""
                    INSERT INTO alarm_departments (alarm_id, department_id)
                    VALUES (%s, %s)
                """, alarm_id[0], dept[0])
            else:
                print(f"Warning: Department {dept_code} not found")
        
        return alarm_id[0]

def process_sms_alarm(content, sender=None, timestamp=None):
    """Process incoming SMS alarm and create database record"""
    
    if timestamp is None:
        timestamp = int(datetime.now().timestamp())
    
    # Parse the alarm message
    from .parser import parse_sms_alarm
    alarm_data = parse_sms_alarm(content)
    
    if not alarm_data['department_code']:
        return {
            'status': 'ignored', 
            'reason': 'Unknown department',
            'parsed_data': alarm_data
        }
    
    # Create alarm in database
    try:
        alarm_id = create_alarm_from_sms(alarm_data, timestamp)
        return {
            'status': 'success',
            'alarm_id': str(alarm_id),
            'department': alarm_data['department_code'],
            'all_departments': alarm_data.get('all_departments', [alarm_data['department_code']]),
            'kind': alarm_data.get('alarm_type', 'Unknown'),
            'parsed_data': alarm_data
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e),
            'parsed_data': alarm_data
        }
