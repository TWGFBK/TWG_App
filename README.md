# Attendance Reporting System

A mobile-first attendance reporting system for emergency response organizations, fire departments, and similar organizations using Flask and PostgreSQL.

![Fire Truck](Img/brandbil_trans.png)

## Features

- **Mobile-first design** with clean, responsive UI
- **NFC tag support** for quick attendance marking
- **Multi-station support** with role-based access
- **Real-time alarm management** (real, test, practice alarms)
- **SMS gateway integration** for automatic alarm creation from SMS messages
- **CSV export** for attendance data
- **Admin interface** for user, tag, and alarm management
- **Secure authentication** with HMAC-based NFC tag hashing
- **Modern card-based UI** with consistent styling across all pages

## Tech Stack

- **Backend**: Python 3.11+, Flask, psycopg[binary]
- **Database**: PostgreSQL with raw SQL migrations
- **Frontend**: Vanilla JavaScript, Jinja2 templates, Custom CSS
- **Authentication**: Session-based with NFC tag support for personnel

## Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Setup Database

```bash
# Create PostgreSQL database
createdb your_database_name

# Copy environment file
cp env.example .env

# Edit .env with your database credentials
# DATABASE_URL=postgresql://user:pass@localhost:5432/your_database_name
# SECRET_KEY=your-secret-key
# NFC_HMAC_SECRET=your-32-byte-secret

psql your_database_name -f migrations/001_init_with_data.sql
psql your_database_name -f migrations/002_database_fixes.sql
```

### 3. Run Application

```bash
# Start the Flask development server
python run.py

# Or use Flask directly
flask --app app.app run --debug
```

The application will be available at `http://localhost:6000`

## Default Login Credentials

The seed data includes these test users:

- **Chief**: ID `0001`, Password `a` (all stations) - John Smith
- **Station A**: ID `0002`, Password `b` (Station A) - Jane Doe
- **Station B**: ID `0003`, Password `c` (Station B) - Bob Johnson
- **Station C**: ID `0004`, Password `d` (Station C) - Alice Williams
- **Station D**: ID `0005`, Password `e` (Station D) - Charlie Brown
- **Multi-Station**: ID `0006`, Password `f` (Station A + Station B) - David Wilson
- **Superadmin**: ID `0010`, Password `y` (all stations) - Admin User

## Usage

### For Users

1. **Login**: Enter your 4-digit ID and single-character password
   - **Auto-Attendance**: System automatically marks attendance for the latest active alarm
   - **Multiple Departments**: If you're in multiple departments with different alarms, you'll be prompted to choose
   - **Same Alarm**: If the same alarm affects multiple departments, attendance is marked for all
2. **NFC Login**: Tap your NFC tag on the reader (keyboard wedge mode)
   - **Tag-Specific Departments**: NFC scans use the tag's assigned departments (not user's departments)
   - **Same Auto-Attendance Logic**: Intelligent attendance marking based on tag's department assignments
3. **Manual Attendance**: Click "Markera närvaro" (Mark Attendance) for specific alarms if needed
4. **View Details**: Click "Visa detaljer" (View Details) to see attendance lists

#### Mobile Interface

![Incoming Alarm - Mobile](Img/Inkommet_larm_mobil.png)

![Incoming Alarm - Mobile with Multiple Vehicles](Img/Inkommet_larm_mobil_fler_kar.png)

### For Administrators

1. **Manage Users**: Create users, assign departments and roles
   - **Search Users**: Search for users by ID to add them to your departments
   - **Edit Users**: Update user information, roles, and department assignments
   - **User Cards**: Modern card-based interface for easy user management

![User Management Interface](Img/User_list.png)

2. **Manage Tags**: Create and revoke NFC tags for users
3. **Manage Alarms**: Create real/test/practice alarms, assign departments
   - **Alarm Cards**: Modern card-based interface showing alarm details
   - **Sort Controls**: Sort alarms by time, type, or status

![Alarm List](Img/Larmlista.png)

4. **Export Data**: Download CSV reports with attendance data

## NFC Integration

The system supports USB NFC readers that act as "keyboard wedge" devices:

1. **Focus Management**: Focus is automatically placed on NFC input fields
2. **Auto-Submission**: When a tag is scanned, the UID is automatically submitted
3. **Tag-Specific Logic**: Each NFC tag can be assigned to specific departments
4. **Smart Attendance**: System uses tag's assigned departments for attendance marking
5. **Department Selection**: Handles multiple active alarms with department selection
6. **Security**: All NFC UIDs are hashed using HMAC-SHA256 for security

### NFC Tag Management

- **Multiple Tags per User**: Users can have multiple NFC tags
- **Department Assignment**: Each tag can be assigned to specific departments
- **Flexible Setup**: Tags can be assigned to different departments than the user
- **Admin Control**: Administrators can create, assign, and revoke NFC tags

## Database Schema

The system uses a PostgreSQL database with the following key tables:

- `users`: User accounts with roles and permissions
- `departments`: Department/station definitions
- `nfc_tags`: NFC tag assignments (hashed UIDs only)
- `alarms`: Alarm events (real, test, practice)
- `attendance`: Attendance records per alarm/department
- `response_times`: Predefined response time options
- `quick_comments`: Predefined comment options
- `auth_events`: Audit log of all authentication attempts





## File Structure

```
├── app/
│   ├── __init__.py
│   ├── app.py              # Flask routes and views
│   ├── db.py               # Database connection and helpers
│   ├── auth.py             # Authentication and NFC handling
│   ├── sms/                # SMS integration module
│   │   ├── __init__.py
│   │   ├── config.py       # Department patterns and SMS settings
│   │   ├── parser.py       # SMS message parser
│   │   ├── handler.py      # Alarm creation from SMS
│   │   ├── webhook.py      # SMS webhook endpoints
│   │   └── README.md       # SMS integration documentation
│   ├── templates/          # Jinja2 templates
│   │   ├── base.html
│   │   ├── login.html
│   │   ├── home.html
│   │   ├── alarm_detail.html
│   │   ├── alarm_display.html
│   │   ├── department_selection.html
│   │   └── admin/
│   │       ├── users.html
│   │       ├── tags.html
│   │       └── alarms.html
│   └── static/
│       ├── app.js          # Vanilla JavaScript
│       ├── base.css        # Base styles
│       ├── home.css        # Home page styles
│       ├── users.css       # User management styles
│       ├── alarms.css      # Alarm management styles
│       ├── alarm_detail.css # Alarm detail styles
│       ├── alarm_display.css # Alarm display styles
│       └── styles.css      # Global styles
├── migrations/
│   ├── 001_init_with_data.sql    # Database schema + test data
│   └── 002_database_fixes.sql    # Database improvements
├── run.py                  # Application entry point
├── setup.py               # Setup script
├── requirements.txt        # Python dependencies
├── env.example            # Environment template
└── README.md              # This file
```

## SMS Integration

The system includes SMS gateway integration for automatic alarm creation:

- **Webhook Endpoint**: `/sms-webhook` receives SMS messages from your gateway
- **Automatic Parsing**: SMS content is parsed to detect departments and extract alarm details
- **Configurable Patterns**: Customize department detection patterns in `app/sms/config.py`
- **Multiple Formats**: Supports various SMS message formats (see `app/sms/parser.py`)

For detailed SMS integration documentation, see [app/sms/README.md](app/sms/README.md).

### Alarm Documentation

![Alarm Documentation 1](Img/larmdocumentation.png)

![Alarm Documentation 2](Img/larmdocumentation2.png)

![Alarm Documentation 3](Img/larmdocumentation3.png)

## Customization

This system is designed to be customized for your organization:

1. **Departments**: Update department codes and names in `migrations/001_init_with_data.sql`
2. **SMS Patterns**: Configure department detection patterns in `app/sms/config.py`
3. **Alarm Types**: Customize alarm type options in `app/templates/alarm_detail.html`
4. **Personnel Names**: Update personnel lists in the alarm detail template
5. **Database**: Modify the database schema as needed for your use case

## Production Deployment

1. **Environment Variables**: Set production values in `.env`
2. **Database**: Use a production PostgreSQL instance
3. **HTTPS**: Configure SSL/TLS for production
4. **Session Security**: Set `SESSION_COOKIE_SECURE=1`
5. **NFC Secret**: Use a strong, unique 32-byte secret
6. **SMS Gateway**: Configure your SMS gateway webhook URL in `app/sms/config.py`

## Database Schema Diagram

```mermaid
erDiagram

    %% ENUMS are omitted in ERD since Mermaid does not support them

    departments {
        SERIAL id PK
        TEXT code
        TEXT name
    }

    users {
        CHAR(4) id PK
        TEXT phone
        TEXT password
        BOOLEAN is_rd
        BOOLEAN is_chafoer
        BOOLEAN role_07
        BOOLEAN is_admin
        BOOLEAN is_superadmin
        BOOLEAN is_md
        VARCHAR first_name
        VARCHAR last_name
    }

    roles {
        SERIAL id PK
        TEXT code
        TEXT description
    }

    user_departments {
        CHAR(4) user_id FK
        INTEGER department_id FK
        INTEGER number
    }

    nfc_tags {
        SERIAL id PK
        VARCHAR tag_uid
        CHAR(4) user_id FK
        INTEGER department_id FK
        VARCHAR label
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    alarms {
        UUID id PK
        alarm_kind kind
        TEXT description
        TIMESTAMPTZ occurred_at
        TIMESTAMPTZ ended_at
        TEXT source
        TEXT alarm_type
        TEXT what
        TEXT where_location
        TEXT who_called
    }

    alarm_departments {
        UUID alarm_id FK
        INTEGER department_id FK
        TIMESTAMPTZ ended_at
    }

    attendance {
        SERIAL id PK
        UUID alarm_id FK
        CHAR(4) user_id FK
        INTEGER department_id FK
        INTEGER response_time
        TEXT comment
        TIMESTAMPTZ eta
        TIMESTAMPTZ attended_at
        TIMESTAMPTZ created_at
        BOOLEAN is_attending
    }

    alarm_responses {
        SERIAL id PK
        UUID alarm_id FK
        CHAR(4) user_id FK
        INTEGER department_id FK
        TEXT comment
        BOOLEAN is_attending
        TIMESTAMPTZ eta
        TIMESTAMPTZ responded_at
        TIMESTAMPTZ created_at
    }

    response_times {
        SERIAL id PK
        INT minutes
        TEXT label
        BOOLEAN active
        INT sort_order
    }

    quick_comments {
        SERIAL id PK
        TEXT text
        BOOLEAN active
        INT sort_order
    }

    auth_events {
        SERIAL id PK
        TEXT uid_hash
        INTEGER tag_id FK
        CHAR(4) user_id FK
        auth_result result
        TEXT reason
        TEXT client_info
        TIMESTAMPTZ created_at
    }

    alarm_comments {
        SERIAL id PK
        UUID alarm_id FK
        INTEGER department_id FK
        VARCHAR user_id FK
        TEXT comment
        TIMESTAMP created_at
    }

    alarm_who_was_07 {
        SERIAL id PK
        UUID alarm_id FK
        INTEGER department_id FK
        VARCHAR user_id FK
        TEXT name
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    sms_users {
        SERIAL id PK
        TEXT username
        TEXT password
        INTEGER department_id FK
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    %% RELATIONSHIPS

    users ||--o{ user_departments : "has departments"
    departments ||--o{ user_departments : "has users"

    users ||--o{ nfc_tags : "owns tag"
    departments ||--o{ nfc_tags : "tag for department"

    alarms ||--o{ alarm_departments : "involves dept"
    departments ||--o{ alarm_departments : "included in alarm"

    alarm_departments ||--o{ attendance : "attendance scoped to dept"
    users ||--o{ attendance : "attends"

    alarm_departments ||--o{ alarm_responses : "responses scoped to dept"
    users ||--o{ alarm_responses : "responds"

    users ||--o{ auth_events : "auth events"
    nfc_tags ||--o{ auth_events : "may use tag"

    alarm_departments ||--|| alarm_comments : "one comment per dept"
    users ||--o{ alarm_comments : "written by"

    alarm_departments ||--|| alarm_who_was_07 : "one 07 per dept"
    users ||--o{ alarm_who_was_07 : "optional ref"

    departments ||--o{ sms_users : "SMS accounts"
```

## License

This project is licensed under the MIT License.
