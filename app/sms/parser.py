"""SMS alarm message parser for SMS gateway integration"""

import re
from .config import DEPARTMENT_PATTERNS, ALARM_TYPE_PATTERNS

def parse_sms_alarm(content):
    """Parse SMS content to determine department and alarm details"""
    
    # Department detection using configuration
    department_code = detect_department(content)
    all_departments = detect_all_departments(content)
    
    # Parse the message to extract structured information
    parsed_info = parse_alarm_details(content)
    
    return {
        'department_code': department_code,
        'all_departments': all_departments,
        'alarm_type': parsed_info['type'],
        'description': parsed_info['description'],
        'what': parsed_info['what'],
        'where': parsed_info['where'],
        'who_called': parsed_info['who_called'],
        'raw_content': content
    }

def extract_department_codes_from_end(text):
    """Extract department codes from the end of text if they match known patterns"""
    if not text:
        return None, text
    
    # Look for patterns like "M111, M3, M31, POLIS" at the end
    # Match: comma-separated codes (M111, M3, POLIS, etc.) at the end, with optional punctuation
    # Try different patterns: with trailing comma, with periods, etc.
    patterns_to_try = [
        r'([A-Z][a-z]?\d+|[A-Z]+)(?:\s*,\s*([A-Z][a-z]?\d+|[A-Z]+))+\s*\.?\.?$',  # Multiple codes
        r'([A-Z][a-z]?\d+|[A-Z]+)\s*\.?\.?$',  # Single code at end
        r'([A-Z][a-z]?\d+|[A-Z]+)(?:\s*,\s*([A-Z][a-z]?\d+|[A-Z]+))*(?:\s*,\s*)?\s*\.?\.?$',  # Flexible
    ]
    
    for dept_pattern in patterns_to_try:
        match = re.search(dept_pattern, text)
        if match:
            # Get all department codes from the match
            dept_codes_str = match.group(0).rstrip('.,').strip()
            if not dept_codes_str:
                continue
                
            # Check if any codes match known department patterns
            dept_codes_upper = dept_codes_str.upper()
            for dept_code, patterns in DEPARTMENT_PATTERNS.items():
                if any(pattern.upper() in dept_codes_upper for pattern in patterns):
                    # Found matching department codes - extract them
                    remaining_text = text[:match.start()].strip()
                    return dept_codes_str, remaining_text
            
            # Also check for POLIS or PolisTeknik (common but not in config)
            if 'POLIS' in dept_codes_upper or 'POLISTEKNIK' in dept_codes_upper:
                remaining_text = text[:match.start()].strip()
                return dept_codes_str, remaining_text
    
    return None, text

def parse_alarm_details(content):
    """Parse alarm details from SMS content"""
    
    # Initialize result
    result = {
        'type': None,
        'what': None,
        'where': None,
        'who_called': None,
        'description': content
    }
    
    # Check for ignore patterns first
    ignore_patterns = [
        'PROVALARM-BEFOLKNINGSSKYDD',
        'Återbud'
    ]
    
    for pattern in ignore_patterns:
        if pattern in content:
            result['type'] = 'IGNORE'
            return result
    
    # Pattern 4: Simple PROVALARM without department prefix
    # Example: PROVALARM Station A. . Practice drill tonight at 19:00.
    pattern4_match = re.match(r'^PROVALARM\s+(.+)$', content)
    if pattern4_match:
        description_part = pattern4_match.group(1).strip()
        
        result['type'] = 'PROVALARM'
        result['what'] = description_part
        result['where'] = None
        result['who_called'] = None
        
        return result
    
    # Pattern 1: Department_N_number_PROVALARM description._location
    # Example: DEPT01_N_900_PROVALARM Station A. . Practice drill tonight at 19:00._Main Street 12, Station A, City
    pattern1_match = re.match(r'^([A-Za-z]+)_([A-Z]_\d+)_PROVALARM\s+(.+?)\._(.+)$', content)
    if pattern1_match:
        dept = pattern1_match.group(1)
        type_code = pattern1_match.group(2)
        description_part = pattern1_match.group(3).strip()
        location_part = pattern1_match.group(4).strip()
        
        result['type'] = 'PROVALARM'
        result['what'] = description_part
        result['where'] = location_part.lstrip('_')
        result['who_called'] = None
        
        return result
    
    # Pattern 2: Department_C_number_description._location
    # Example: A01, DEPT01_C_441_Other Staff station due to resources busy with fire at location ._Main Street 12, Station A, City
    pattern2_match = re.match(r'^([^_]+)_([A-Z]_\d+)_(.+?)\.(.+)$', content)
    if pattern2_match:
        who_called = pattern2_match.group(1).strip()
        type_code = pattern2_match.group(2)
        description_part = pattern2_match.group(3).strip()
        location_part = pattern2_match.group(4).strip()
        
        # Try to extract type from description
        type_keywords = ['Beredskapsalarm', 'Övrigt', 'Meddelande']
        for keyword in type_keywords:
            if keyword in description_part:
                result['type'] = keyword
                break
        
        if not result['type']:
            result['type'] = 'Larm'  # Default for C-type alarms
        
        result['what'] = description_part
        result['where'] = location_part.lstrip('_')
        result['who_called'] = who_called
        
        return result
    
    # Pattern 3: Department codes at start, then department_type_number: description._location
    # Example: B01, B02, B03, A01, A02, A03, POLICE, PoliceTech_A_422_Class: Major Alarm - Building Fire._Oak Street 11, City
    pattern3_match = re.match(r'^([^_]+)_([A-Z]_\d+)_([^_]+)\.(.+)$', content)
    if pattern3_match:
        who_called = pattern3_match.group(1).strip()
        type_code = pattern3_match.group(2)
        description_part = pattern3_match.group(3).strip()
        location_part = pattern3_match.group(4).strip()
        
        # Extract type from description
        if 'Klass:' in description_part:
            type_match = re.search(r'Klass:\s*([^.-]+)', description_part)
            if type_match:
                result['type'] = type_match.group(1).strip()
        
        # Extract what (everything after type)
        if ' - ' in description_part:
            what_part = description_part.split(' - ', 1)[1]
            result['what'] = what_part.strip()
        else:
            result['what'] = description_part
        
        # Extract where (remove leading underscore if present)
        result['where'] = location_part.lstrip('_')
        
        # Extract who is called
        result['who_called'] = who_called
        
        return result
    
    # Pattern 4: Location; Class: type. Event? what. Other: additional_info.; who_called
    # Example: Old School Street 12, City;  Class: Person Search Alarm. Event? LIFT ASSISTANCE. Other: door open, sitting on floor outside bathroom.;  B01, B02
    pattern4_match = re.match(r'^(.+?);\s*Klass:\s*([^;]+)\.\s*Händelse\?\s*([^;]+)\.\s*Övrigt:\s*([^;]+);\s*(.+)$', content)
    if pattern4_match:
        location = pattern4_match.group(1).strip()
        alarm_type = pattern4_match.group(2).strip()
        händelse = pattern4_match.group(3).strip()
        övrigt = pattern4_match.group(4).strip()
        who_called = pattern4_match.group(5).strip()
        
        result['type'] = alarm_type
        result['what'] = f"{händelse}. Övrigt: {övrigt}"
        result['where'] = location
        result['who_called'] = who_called
        
        return result
    
    # Pattern 5: Location; Class: type. Event: what. additional_info.; who_called
    # Example: Main Road, City;  Class: Rescue - Assistance. Event: driven into ditch, 1 person not trapped . Type of traffic accident: Single accident/Off-road. Type of vehicle Car. Vehicle on wheels. Patient injuries neck pain .;  B01, B02, B03, A01, A02, A03, POLICE
    pattern5_match = re.match(r'^(.+?);\s*Klass:\s*([^;]+)\.\s*Händelse:\s*([^;]+);\s*(.+)$', content)
    if pattern5_match:
        location = pattern5_match.group(1).strip()
        alarm_type = pattern5_match.group(2).strip()
        händelse = pattern5_match.group(3).strip()
        who_called = pattern5_match.group(4).strip()
        
        result['type'] = alarm_type
        result['what'] = händelse
        result['where'] = location
        result['who_called'] = who_called
        
        return result
    
    # Pattern 6: Location; additional_location; Class: type - what. additional_info.; who_called
    # Example: Spark Street, Hilltop, City;  At old stone crusher;  Class: Major Alarm - Wildfire. Other information Smoke up on the hill at old stone crusher.;  B01, B02, B03, A01, A02, A03, POLICE, PoliceTech
    pattern6_match = re.match(r'^(.+?);\s+(.+?);\s+Klass:\s*([^-]+?)\s*-\s*([^.;]+?)\.\s*([^;]+?);\s+(.+)$', content)
    if pattern6_match:
        location1 = pattern6_match.group(1).strip()
        location2 = pattern6_match.group(2).strip()
        alarm_type = pattern6_match.group(3).strip()
        what = pattern6_match.group(4).strip()
        additional_info = pattern6_match.group(5).strip()
        who_called = pattern6_match.group(6).strip()
        
        result['type'] = alarm_type
        result['what'] = f"{what}. {additional_info}"
        result['where'] = f"{location1}; {location2}"
        result['who_called'] = who_called
        
        return result
    
    # Pattern 7: Location; additional_info; Class: type. Event? what. Other: additional_info.; who_called
    # Example: Old School Street 12, City;  light 3 ;  Class: Person Search Alarm. Event? LIFT ASSISTANCE . Other: sitting on floor cannot get up. .;  B01, B02
    # More tolerant matching (extra spaces or dots around sentences)
    pattern7_match = re.match(
        r'^(.+?);\s*(.+?);\s*Klass:\s*([^.;]+)\.\s*Händelse\?\s*([^.;]+?)\s*\.?\s*Övrigt:\s*([^;]+?)\s*\.?\s*;\s*(.+)$',
        content
    )
    if pattern7_match:
        location = pattern7_match.group(1).strip()
        additional_info = pattern7_match.group(2).strip()
        alarm_type = pattern7_match.group(3).strip()
        händelse = pattern7_match.group(4).strip()
        övrigt = pattern7_match.group(5).strip()
        who_called = pattern7_match.group(6).strip()
        
        result['type'] = alarm_type
        result['what'] = f"{händelse}. Övrigt: {övrigt}".replace('..', '.').replace(' .', '.')
        result['where'] = f"{location}; {additional_info}"
        result['who_called'] = who_called
        
        return result
    
    # Pattern 8a: Address; /Class: AlarmType - What. Other information additional_info [departments]
    # Example: Main Street 12, Station A school north, City; /Class: Major Alarm - Automatic Alarm. Other information Automatic alarm A01, A02, A03..
    pattern8a_match = re.match(r'^(.+?);\s*/Klass:\s*([^-]+?)\s*-\s*([^.;]+?)\s*\.\s*(.+)$', content)
    if pattern8a_match:
        location = pattern8a_match.group(1).strip()
        alarm_type = pattern8a_match.group(2).strip()
        what = pattern8a_match.group(3).strip()
        rest = pattern8a_match.group(4).strip()
        
        # Try to extract who_called from the end (department codes)
        who_called, what_part = extract_department_codes_from_end(rest)
        
        result['type'] = alarm_type
        result['what'] = f"{what}. {what_part}".strip() if what_part else what
        result['where'] = location
        result['who_called'] = who_called
        
        return result
    
    # Pattern 8b: Address; Class: AlarmType-What. Other information additional_info [departments]
    # Example: West School Street 4, Station A elementary school, City; Class: Major Alarm-Automatic Alarm. Other information Automatic alarm A01, A02, A03,
    pattern8b_match = re.match(r'^(.+?);\s*Klass:\s*([^-]+?)-([^.;]+?)\s*\.\s*(.+)$', content)
    if pattern8b_match:
        location = pattern8b_match.group(1).strip()
        alarm_type = pattern8b_match.group(2).strip()
        what = pattern8b_match.group(3).strip()
        rest = pattern8b_match.group(4).strip()
        
        # Try to extract who_called from the end (department codes)
        who_called, what_part = extract_department_codes_from_end(rest)
        
        result['type'] = alarm_type
        result['what'] = f"{what}. {what_part}".strip() if what_part else what
        result['where'] = location
        result['who_called'] = who_called
        
        return result
    
    # Pattern 8c: Address; /Class: AlarmType - What.; WhoCalled
    # Example: Main Street 12, Station A school north, City; /Class: Major Alarm - Automatic Alarm.; A01, A02, A03
    pattern8c_match = re.match(r'^(.+?);\s*/Klass:\s*([^-]+?)\s*-\s*([^;]+?)\s*\.\s*;\s*(.+)$', content)
    if pattern8c_match:
        location = pattern8c_match.group(1).strip()
        alarm_type = pattern8c_match.group(2).strip()
        what = pattern8c_match.group(3).strip()
        who_called = pattern8c_match.group(4).strip()
        
        result['type'] = alarm_type
        result['what'] = what
        result['where'] = location
        result['who_called'] = who_called
        
        return result
    
    # Pattern 8d: Address; Class: AlarmType-What.; WhoCalled
    # Example: West School Street 4, Station A elementary school, City; Class: Major Alarm-Automatic Alarm.; A01, A02, A03
    pattern8d_match = re.match(r'^(.+?);\s*Klass:\s*([^-]+?)-([^;]+?)\s*\.\s*;\s*(.+)$', content)
    if pattern8d_match:
        location = pattern8d_match.group(1).strip()
        alarm_type = pattern8d_match.group(2).strip()
        what = pattern8d_match.group(3).strip()
        who_called = pattern8d_match.group(4).strip()
        
        result['type'] = alarm_type
        result['what'] = what
        result['where'] = location
        result['who_called'] = who_called
        
        return result
    
    # Pattern 8b: Location; Class: type - what. additional_info.; who_called
    # Example: Bay Street 323, City;  Class: Small Alarm - Chimney Fire. What type of building? chimney fire. 2 floors.;  E01, E02, A01, POLICE
    # Format: Location; Klass: Type - What. AdditionalInfo.; WhoCalled
    pattern8b_match = re.match(r'^(.+?);\s*Klass:\s*([^-]+?)\s*-\s*([^.]+?)\.\s*([^;]+)\s*;\s*(.+)$', content)
    if pattern8b_match:
        location = pattern8b_match.group(1).strip()
        alarm_type = pattern8b_match.group(2).strip()
        what = pattern8b_match.group(3).strip()
        additional_info = pattern8b_match.group(4).strip()
        who_called = pattern8b_match.group(5).strip()
        
        result['type'] = alarm_type
        result['what'] = f"{what}. {additional_info}".strip()
        result['where'] = location
        result['who_called'] = who_called
        
        return result
    
    # Pattern 8c: Location, Class: type - what. additional_info; who_called
    # Example: Bay Street 323, City, Class: Small Alarm - Chimney Fire. What type of building? chimney fire. 2 floors; E01, E02, A01, POLICE
    # Format: Location, Klass: Type - What. AdditionalInfo; WhoCalled (comma instead of semicolon)
    pattern8c_match = re.match(r'^(.+?),\s*Klass:\s*([^-]+?)\s*-\s*([^.]+?)\.\s*([^;]+)\s*;\s*(.+)$', content)
    if pattern8c_match:
        location = pattern8c_match.group(1).strip()
        alarm_type = pattern8c_match.group(2).strip()
        what = pattern8c_match.group(3).strip()
        additional_info = pattern8c_match.group(4).strip()
        who_called = pattern8c_match.group(5).strip()
        
        result['type'] = alarm_type
        result['what'] = f"{what}. {additional_info}".strip()
        result['where'] = location
        result['who_called'] = who_called
        
        return result
    
    # Pattern 8: Address; Class: AlarmType - What.; WhoCalled
    # Example: Ridge Road 121 Farm, City; Class: Major Alarm - Automatic Alarm.; B01, B02, C01, C02, A01, POLICE
    # Format is ALWAYS: Address; Klass: Type - What.; WhoCalled
    pattern8_match = re.match(r'^(.+?);\s*Klass:\s*([^-]+?)\s*-\s*([^;]+?)\s*\.\s*;\s*(.+)$', content)
    if pattern8_match:
        location = pattern8_match.group(1).strip()
        alarm_type = pattern8_match.group(2).strip()
        what = pattern8_match.group(3).strip()
        who_called = pattern8_match.group(4).strip()
        
        result['type'] = alarm_type
        result['what'] = what
        result['where'] = location
        result['who_called'] = who_called
        
        return result
    
    # Pattern 9: Location; Standby Alarm/Other description. Other additional_info., WhoCalled
    # Example: Main Street 12, Station A, City; Standby Alarm all ambulances out, contact supervisor tel 123456. Other On standby., A01, DEPT01
    pattern9_match = re.match(r'^(.+?);\s*(Beredskapsalarm|Övrigt)\s*(.+?)\s*\.\s*Övrigt\s+([^.,]+?)\s*\.\s*,\s*(.+)$', content)
    if pattern9_match:
        location = pattern9_match.group(1).strip()
        alarm_type = pattern9_match.group(2).strip()
        description = pattern9_match.group(3).strip()
        additional_info = pattern9_match.group(4).strip()
        who_called = pattern9_match.group(5).strip()
        
        result['type'] = alarm_type
        result['what'] = f"{description}. Övrigt {additional_info}".strip()
        result['where'] = location
        result['who_called'] = who_called
        
        return result
    
    # Pattern 9b: Location; Standby Alarm/Other description., WhoCalled
    # Example: Main Street 12, Station A, City; Standby Alarm standby at depot., A01, DEPT01
    pattern9b_match = re.match(r'^(.+?);\s*(Beredskapsalarm|Övrigt)\s*(.+?)\s*\.\s*,\s*(.+)$', content)
    if pattern9b_match:
        location = pattern9b_match.group(1).strip()
        alarm_type = pattern9b_match.group(2).strip()
        description = pattern9b_match.group(3).strip()
        who_called = pattern9b_match.group(4).strip()
        
        result['type'] = alarm_type
        result['what'] = description
        result['where'] = location
        result['who_called'] = who_called
        
        return result
    
    # Pattern 9c: Location; Type of reinforcement Fire Department. Other information: description.; WhoCalled
    # Example: Harbor Road, City; Type of reinforcement Fire Department. Other information: Fire in barn City.; A01, A02, A03, DEPT01
    pattern9c_match = re.match(r'^(.+?);\s*Typ av förstärkning\s+([^.;]+?)\.\s*Övrig information:\s*([^;]+?)\s*\.\s*;\s*(.+)$', content)
    if pattern9c_match:
        location = pattern9c_match.group(1).strip()
        reinforcement_type = pattern9c_match.group(2).strip()
        description = pattern9c_match.group(3).strip()
        who_called = pattern9c_match.group(4).strip()
        
        result['type'] = 'Förstärkning'
        result['what'] = f"Typ av förstärkning {reinforcement_type}. Övrig information: {description}"
        result['where'] = location
        result['who_called'] = who_called
        
        return result
    
    # Pattern 10: WhoCalled Class: AlarmType - What. Address
    # Example: E01, E02, A01, POLICE B 417 Class: Small Alarm - Chimney Fire. Bay Street 323, City
    # Format: Department codes at start, then "Klass: Type - What. Address"
    pattern10_match = re.match(r'^(.+?)\s+Klass:\s*([^-]+?)\s*-\s*([^.]+?)\.\s*(.+)$', content)
    if pattern10_match:
        who_called = pattern10_match.group(1).strip()
        alarm_type = pattern10_match.group(2).strip()
        what = pattern10_match.group(3).strip()
        location = pattern10_match.group(4).strip()
        
        result['type'] = alarm_type
        result['what'] = what
        result['where'] = location
        result['who_called'] = who_called
        
        return result
    
    # Default fallback - try to extract basic info
    result['type'] = 'Unknown'
    result['what'] = content
    result['where'] = None
    result['who_called'] = None
    
    return result

def detect_department(content):
    """Enhanced department detection using configuration patterns - returns first matching department"""
    
    # Use detect_all_departments to get all matches, then return the first one
    all_departments = detect_all_departments(content)
    
    if not all_departments:
        return None
    
    # Return the first department for backward compatibility
    return all_departments[0]

def detect_all_departments(content):
    """Detect all departments mentioned in the SMS content"""
    
    matched_departments = []
    content_upper = content.upper()  # Convert to uppercase for case-insensitive matching
    
    # First, try to extract department codes from the end of the message
    # These are usually comma-separated codes like "B01, B02, A01, POLICE"
    dept_codes_str, _ = extract_department_codes_from_end(content)
    
    # Extract individual codes from the comma-separated string
    extracted_codes = set()
    if dept_codes_str:
        # Split by comma and clean up
        codes = [code.strip().upper() for code in dept_codes_str.split(',')]
        extracted_codes.update(codes)
    
    # Also extract codes that appear at the start (before first underscore or space after comma)
    # Pattern: codes at start like "A01, DEPT01_C_440..."
    start_match = re.match(r'^([A-Z][a-z]?\d+|[A-Z]+)(?:\s*,\s*([A-Z][a-z]?\d+|[A-Z]+))*(?:\s*,\s*|_)', content_upper)
    if start_match:
        # Extract all codes from the match
        start_codes_str = start_match.group(0).rstrip('_,').strip()
        if start_codes_str:
            start_codes = [code.strip() for code in start_codes_str.split(',')]
            extracted_codes.update(start_codes)
    
    for department_code, patterns in DEPARTMENT_PATTERNS.items():
        matched = False
        
        # Check if any extracted code matches a pattern (exact match)
        for pattern in patterns:
            pattern_upper = pattern.upper()
            if pattern_upper in extracted_codes:
                matched = True
                break
        
        # If not matched yet, check for patterns in the content
        # Use smart matching to avoid false positives:
        # - For short codes (<=4 chars), require word boundary or non-alphanumeric boundaries
        # - For longer patterns (department names), use word boundary matching
        if not matched:
            for pattern in patterns:
                pattern_upper = pattern.upper()
                if len(pattern) <= 4:
                    # Short codes: match only at word boundaries or non-alphanumeric boundaries
                    # This prevents "E11" matching "LE11", but allows "M31" matching "M31," or "M31_"
                    # Use negative lookbehind/lookahead to ensure not part of a longer alphanumeric sequence
                    pattern_regex = r'(?<![A-Z0-9])' + re.escape(pattern_upper) + r'(?![A-Z0-9])'
                else:
                    # Longer patterns (department names): use word boundary
                    pattern_regex = r'\b' + re.escape(pattern_upper) + r'\b'
                
                if re.search(pattern_regex, content_upper):
                    matched = True
                    break
        
        if matched:
            matched_departments.append(department_code)
    
    return matched_departments

def detect_alarm_kind(content):
    """Detect alarm kind based on content patterns"""
    
    for kind, patterns in ALARM_TYPE_PATTERNS.items():
        if any(pattern in content for pattern in patterns):
            return kind
    
    return 'real'  # Default to real alarm
