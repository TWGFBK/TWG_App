-- Initial database setup with test data
-- Consolidated all migrations into a single file for fresh database setup

DO $$ BEGIN
  CREATE TYPE alarm_kind  AS ENUM ('real','test','practice');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE tag_status AS ENUM ('active','revoked','lost');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE auth_result AS ENUM ('success','unknown_tag','revoked','denied','not_member','ambiguous');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS departments (
  id    SERIAL PRIMARY KEY,
  code  TEXT NOT NULL UNIQUE,
  name  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
  id         CHAR(4) PRIMARY KEY CHECK (id ~ '^\d{4}$'),
  phone      TEXT,
  password   TEXT NOT NULL,
  is_rd      BOOLEAN NOT NULL DEFAULT FALSE,
  is_chafoer BOOLEAN NOT NULL DEFAULT FALSE,
  role_07    BOOLEAN NOT NULL DEFAULT FALSE,
  is_admin   BOOLEAN NOT NULL DEFAULT FALSE,
  is_superadmin BOOLEAN NOT NULL DEFAULT FALSE,
  is_md      BOOLEAN NOT NULL DEFAULT FALSE,
  first_name VARCHAR(11),
  last_name  VARCHAR(11)
);

CREATE TABLE IF NOT EXISTS roles (
  id          SERIAL PRIMARY KEY,
  code        TEXT NOT NULL UNIQUE,
  description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS user_departments (
  user_id       CHAR(4) REFERENCES users(id) ON DELETE CASCADE,
  department_id INTEGER REFERENCES departments(id) ON DELETE CASCADE,
  number        INTEGER CHECK (number >= 0 AND number <= 999),
  PRIMARY KEY (user_id, department_id)
);

CREATE TABLE IF NOT EXISTS nfc_tags (
  id          SERIAL PRIMARY KEY,
  tag_uid     VARCHAR(32) NOT NULL UNIQUE,
  user_id     CHARACTER(4) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
  label       VARCHAR(100),
  created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(tag_uid),
  UNIQUE(user_id, department_id)
);

-- Add trigger to update updated_at timestamp for nfc_tags
CREATE OR REPLACE FUNCTION update_nfc_tags_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_nfc_tags_updated_at ON nfc_tags;
CREATE TRIGGER update_nfc_tags_updated_at
    BEFORE UPDATE ON nfc_tags
    FOR EACH ROW
    EXECUTE FUNCTION update_nfc_tags_updated_at();

CREATE TABLE IF NOT EXISTS alarms (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  kind        alarm_kind NOT NULL,
  description TEXT,
  occurred_at TIMESTAMPTZ NOT NULL,
  ended_at    TIMESTAMPTZ,
  source      TEXT,
  alarm_type  TEXT,
  what        TEXT,
  where_location TEXT,
  who_called  TEXT
);

CREATE TABLE IF NOT EXISTS alarm_departments (
  alarm_id      UUID REFERENCES alarms(id) ON DELETE CASCADE,
  department_id INTEGER REFERENCES departments(id) ON DELETE CASCADE,
  ended_at      TIMESTAMPTZ,
  PRIMARY KEY (alarm_id, department_id)
);

-- Add index for better performance when querying active alarms
CREATE INDEX IF NOT EXISTS idx_alarm_departments_ended_at ON alarm_departments(ended_at);

CREATE TABLE IF NOT EXISTS attendance (
  id            SERIAL PRIMARY KEY,
  alarm_id      UUID NOT NULL,
  user_id       CHAR(4) NOT NULL,
  department_id INTEGER NOT NULL,
  response_time INTEGER,
  comment       TEXT,
  eta           TIMESTAMPTZ,
  attended_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  is_attending  BOOLEAN DEFAULT TRUE,
  UNIQUE (alarm_id, department_id, user_id),
  FOREIGN KEY (alarm_id, department_id) REFERENCES alarm_departments(alarm_id, department_id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS response_times (
  id    SERIAL PRIMARY KEY,
  minutes INT NOT NULL,
  label  TEXT NOT NULL,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  sort_order INT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS quick_comments (
  id    SERIAL PRIMARY KEY,
  text  TEXT NOT NULL UNIQUE,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  sort_order INT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS alarm_responses (
  id            SERIAL PRIMARY KEY,
  alarm_id      UUID NOT NULL,
  user_id       CHAR(4) NOT NULL,
  department_id INTEGER NOT NULL,
  comment       TEXT,
  is_attending  BOOLEAN DEFAULT FALSE,
  eta           TIMESTAMPTZ,
  responded_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (alarm_id, department_id, user_id),
  FOREIGN KEY (alarm_id, department_id) REFERENCES alarm_departments(alarm_id, department_id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS auth_events (
  id          SERIAL PRIMARY KEY,
  uid_hash    TEXT NOT NULL,
  tag_id      INTEGER REFERENCES nfc_tags(id) ON DELETE SET NULL,
  user_id     CHAR(4) REFERENCES users(id) ON DELETE SET NULL,
  result      auth_result NOT NULL,
  reason      TEXT,
  client_info TEXT,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Add alarm_comments table for department-specific comments on closed alarms
-- Includes report fields: larmtyp, raddningsledare, rapportforfattare_user_id, rapportforfattare_name, email
CREATE TABLE IF NOT EXISTS alarm_comments (
    id SERIAL PRIMARY KEY,
    alarm_id UUID NOT NULL REFERENCES alarms(id) ON DELETE CASCADE,
    department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    user_id CHARACTER VARYING NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    comment TEXT NOT NULL,
    larmtyp TEXT,
    raddningsledare TEXT,
    rapportforfattare_user_id CHARACTER(4) REFERENCES users(id),
    rapportforfattare_name TEXT,
    email TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(alarm_id, department_id) -- Only one comment per department per alarm
);

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_alarm_comments_alarm_id ON alarm_comments(alarm_id);
CREATE INDEX IF NOT EXISTS idx_alarm_comments_department_id ON alarm_comments(department_id);
CREATE INDEX IF NOT EXISTS idx_alarm_comments_user_id ON alarm_comments(user_id);

-- Add alarm_who_was_07 table for department-specific who_was_07 information
CREATE TABLE IF NOT EXISTS alarm_who_was_07 (
    id SERIAL PRIMARY KEY,
    alarm_id UUID NOT NULL REFERENCES alarms(id) ON DELETE CASCADE,
    department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    user_id CHARACTER VARYING REFERENCES users(id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(alarm_id, department_id) -- Only one who_was_07 per department per alarm
);

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_alarm_who_was_07_alarm_id ON alarm_who_was_07(alarm_id);
CREATE INDEX IF NOT EXISTS idx_alarm_who_was_07_department_id ON alarm_who_was_07(department_id);
CREATE INDEX IF NOT EXISTS idx_alarm_who_was_07_user_id ON alarm_who_was_07(user_id);

-- Add trigger to update updated_at timestamp for alarm_who_was_07
CREATE OR REPLACE FUNCTION update_alarm_who_was_07_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_alarm_who_was_07_updated_at ON alarm_who_was_07;
CREATE TRIGGER update_alarm_who_was_07_updated_at
    BEFORE UPDATE ON alarm_who_was_07
    FOR EACH ROW
    EXECUTE FUNCTION update_alarm_who_was_07_updated_at();

-- Add SMS users table for department-based SMS sending
CREATE TABLE IF NOT EXISTS sms_users (
  id          SERIAL PRIMARY KEY,
  username    TEXT NOT NULL UNIQUE,
  password    TEXT NOT NULL,
  department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Add index for faster lookups
CREATE INDEX IF NOT EXISTS idx_sms_users_username ON sms_users(username);
CREATE INDEX IF NOT EXISTS idx_sms_users_department_id ON sms_users(department_id);

-- Add trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_sms_users_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_sms_users_updated_at ON sms_users;
CREATE TRIGGER update_sms_users_updated_at
    BEFORE UPDATE ON sms_users
    FOR EACH ROW
    EXECUTE FUNCTION update_sms_users_updated_at();

-- Add department_cars table to store cars for each department
CREATE TABLE IF NOT EXISTS department_cars (
  id            SERIAL PRIMARY KEY,
  department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
  car_code      TEXT NOT NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(department_id, car_code)
);

-- Add index for faster lookups by department
CREATE INDEX IF NOT EXISTS idx_department_cars_department_id ON department_cars(department_id);

-- Add table to store user-to-car assignments for alarm reporting
-- Includes report fields: mantimmar_insats, mantimmar_bevakning, mantimmar_aterstallning, anvant_aa_rokdykning, anvant_aa_sjalvskydd
CREATE TABLE IF NOT EXISTS alarm_user_car_assignments (
  id SERIAL PRIMARY KEY,
  alarm_id UUID NOT NULL REFERENCES alarms(id) ON DELETE CASCADE,
  department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
  user_id CHARACTER(4) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  car_code TEXT NOT NULL,
  mantimmar_insats NUMERIC(5,2),
  mantimmar_bevakning NUMERIC(5,2),
  mantimmar_aterstallning NUMERIC(5,2),
  anvant_aa_rokdykning TEXT CHECK (anvant_aa_rokdykning IN ('Inte tillgänglig', 'Nej', 'Ja')),
  anvant_aa_sjalvskydd TEXT CHECK (anvant_aa_sjalvskydd IN ('Inte tillgänglig', 'Nej', 'Ja')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(alarm_id, department_id, user_id) -- One car per user per alarm/department
);

CREATE INDEX IF NOT EXISTS idx_alarm_user_car_assignments_alarm_dept 
  ON alarm_user_car_assignments(alarm_id, department_id);

-- Insert departments with proper UTF-8 encoding
INSERT INTO departments (code, name) VALUES
  ('DEPT01', 'Fire Department Station A'),
  ('DEPT02', 'Fire Department Station B'),
  ('DEPT03', 'Fire Department Station C'),
  ('DEPT04', 'Fire Department Station D'),
  ('DEPT05', 'Fire Department Station E')
ON CONFLICT (code) DO NOTHING;

-- Insert superadmin users
INSERT INTO users (id, phone, password, is_rd, role_07, is_admin, is_superadmin, is_md, first_name, last_name) VALUES
  ('0010', '+12345678901', 'y', FALSE, TRUE, TRUE, TRUE, TRUE, 'John', 'Smith'), -- Superadmin with MD role
  ('0011', '+12345678902', 'y', FALSE, TRUE, TRUE, TRUE, TRUE, 'Jane', 'Doe') -- Superadmin with MD role
ON CONFLICT (id) DO NOTHING;

-- Insert roles
INSERT INTO roles (code, description) VALUES
  ('RD', 'Rökdykare'),
  ('C', 'Lastbilskort'),
  ('R07', 'Roll 07'),
  ('ADMIN', 'Administratör'),
  ('MD', 'Multi-Department')
ON CONFLICT (code) DO NOTHING;

-- Assign superadmin users to all departments with department numbers
INSERT INTO user_departments (user_id, department_id, number) VALUES
  ('0010', (SELECT id FROM departments WHERE code = 'DEPT01'), 10),
  ('0010', (SELECT id FROM departments WHERE code = 'DEPT02'), 10),
  ('0010', (SELECT id FROM departments WHERE code = 'DEPT03'), 10),
  ('0010', (SELECT id FROM departments WHERE code = 'DEPT04'), 10),
  ('0010', (SELECT id FROM departments WHERE code = 'DEPT05'), 10),
  ('0011', (SELECT id FROM departments WHERE code = 'DEPT01'), 11),
  ('0011', (SELECT id FROM departments WHERE code = 'DEPT02'), 11),
  ('0011', (SELECT id FROM departments WHERE code = 'DEPT03'), 11),
  ('0011', (SELECT id FROM departments WHERE code = 'DEPT04'), 11),
  ('0011', (SELECT id FROM departments WHERE code = 'DEPT05'), 11)
ON CONFLICT (user_id, department_id) DO NOTHING;

-- Insert default NFC tags for user 0010
INSERT INTO nfc_tags (user_id, department_id, tag_uid, label) VALUES
  ('0010', (SELECT id FROM departments WHERE code = 'DEPT01'), '33253E35', 'Station A'),
  ('0010', (SELECT id FROM departments WHERE code = 'DEPT02'), '482974', 'Station B')
ON CONFLICT (tag_uid) DO NOTHING;

-- Insert initial car data for each department
-- Station A (DEPT01): A01, A02, A03
INSERT INTO department_cars (department_id, car_code)
SELECT d.id, car_code
FROM departments d
CROSS JOIN (VALUES ('A01'), ('A02'), ('A03')) AS cars(car_code)
WHERE d.code = 'DEPT01'
ON CONFLICT (department_id, car_code) DO NOTHING;

-- Station B (DEPT02): B01, B02, B03
INSERT INTO department_cars (department_id, car_code)
SELECT d.id, car_code
FROM departments d
CROSS JOIN (VALUES ('B01'), ('B02'), ('B03')) AS cars(car_code)
WHERE d.code = 'DEPT02'
ON CONFLICT (department_id, car_code) DO NOTHING;

-- Station C (DEPT03): C01, C02, C03
INSERT INTO department_cars (department_id, car_code)
SELECT d.id, car_code
FROM departments d
CROSS JOIN (VALUES ('C01'), ('C02'), ('C03')) AS cars(car_code)
WHERE d.code = 'DEPT03'
ON CONFLICT (department_id, car_code) DO NOTHING;

-- Station D (DEPT04): D01, D02, D03
INSERT INTO department_cars (department_id, car_code)
SELECT d.id, car_code
FROM departments d
CROSS JOIN (VALUES ('D01'), ('D02'), ('D03')) AS cars(car_code)
WHERE d.code = 'DEPT04'
ON CONFLICT (department_id, car_code) DO NOTHING;

-- Station E (DEPT05): E01, E02, E03
INSERT INTO department_cars (department_id, car_code)
SELECT d.id, car_code
FROM departments d
CROSS JOIN (VALUES ('E01'), ('E02'), ('E03')) AS cars(car_code)
WHERE d.code = 'DEPT05'
ON CONFLICT (department_id, car_code) DO NOTHING;

-- Insert response time options
INSERT INTO response_times (minutes, label, sort_order) VALUES
  (5, '5 minuter', 1),
  (7, '7 minuter', 2),
  (10, '10 minuter', 3),
  (0, 'På plats', 0)
ON CONFLICT DO NOTHING;

-- Insert quick comment options
INSERT INTO quick_comments (text, sort_order) VALUES
  ('Far direkt till platsen, Ta med mina kläder', 1),
  ('Ring om jag ska komma', 2),
  ('Upptagen, kommer inte!', 3)
ON CONFLICT (text) DO NOTHING;
