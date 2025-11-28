"""Configuration for SMS alarm integration"""

# Department detection patterns
# Configure these patterns to match your SMS alarm message format
# Each department can have multiple patterns (vehicle codes, department codes, names)
DEPARTMENT_PATTERNS = {
    'DEPT01': ['A01', 'A02', 'A03', 'DEPT01', 'Station A'],
    'DEPT02': ['B01', 'B02', 'B03', 'DEPT02', 'Station B'],
    'DEPT03': ['C01', 'C02', 'C03', 'DEPT03', 'Station C'],
    'DEPT04': ['D01', 'D02', 'D03', 'DEPT04', 'Station D'],
    'DEPT05': ['E01', 'E02', 'E03', 'DEPT05', 'Station E'],
    'RESCUE': ['RESCUE01', 'Rescue Team', 'Emergency Response']
}

# Alarm type detection patterns
ALARM_TYPE_PATTERNS = {
    'practice': ['PROVALARM', 'Övning', 'test'],
    'test': ['test', 'TEST'],
    'Larm': []  # Default for real alarms
}

# SMS webhook settings
SMS_WEBHOOK_SETTINGS = {
    'endpoint': '/sms-webhook',
    'test_endpoint': '/sms-test',
    'supported_methods': ['POST', 'GET'],
    'content_type': 'application/json'
}

# SMS Gateway integration settings
# Configure your SMS gateway webhook URL here
SMS_GATEWAY_SETTINGS = {
    'webhook_url': 'https://yourdomain.com/sms-webhook',
    'retry_scheme': {
        'attempts': [10, 20, 30, 1800],  # seconds
        'max_age': 604800  # 1 week in seconds
    }
}
