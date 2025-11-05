-- =========================================================
-- 1. STAFF TABLE
-- =========================================================
CREATE TABLE IF NOT EXISTS staff (
    staff_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

-- =========================================================
-- 2. LEAD FORM TABLE
-- =========================================================
CREATE TABLE IF NOT EXISTS lead_form (
    phone_number VARCHAR(15) PRIMARY KEY,
    name VARCHAR(100),
    college_name VARCHAR(100),
    degree VARCHAR(50),
    employed BOOLEAN DEFAULT FALSE,
    course_interested VARCHAR(100),
    status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'closed', 'enrolled')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- 3. CALL LOGS TABLE
-- =========================================================
CREATE TABLE IF NOT EXISTS call_logs (
    log_id SERIAL PRIMARY KEY,
    phone_number VARCHAR(15) NOT NULL,
    staff_id INT NOT NULL,
    log_text TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (phone_number) REFERENCES lead_form(phone_number) ON DELETE CASCADE,
    FOREIGN KEY (staff_id) REFERENCES staff(staff_id) ON DELETE CASCADE
);

-- =========================================================
-- 4. COURSES TABLE
-- =========================================================
CREATE TABLE IF NOT EXISTS courses (
    course_id SERIAL PRIMARY KEY,
    course_name VARCHAR(100) NOT NULL,
    duration_weeks INT
);

-- =========================================================
-- 5. ENROLLMENT TABLE
-- (Maps each lead to a course)
-- =========================================================
CREATE TABLE IF NOT EXISTS enrollment (
    enrollment_id SERIAL PRIMARY KEY,
    phone_number VARCHAR(15) NOT NULL,
    course_id INT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (phone_number) REFERENCES lead_form(phone_number) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
    UNIQUE (phone_number, course_id)   -- One enrollment per course per lead
);

-- =========================================================
-- 6. ATTENDANCE TABLE
-- (Tracks attendance using enrollment_id only)
-- =========================================================
CREATE TABLE IF NOT EXISTS attendance (
    attendance_id SERIAL PRIMARY KEY,
    enrollment_id INT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    attendance BOOLEAN,
    FOREIGN KEY (enrollment_id) REFERENCES enrollment(enrollment_id) ON DELETE CASCADE
);

-- =========================================================
-- 7. SEED DATA (Idempotent)
-- =========================================================
-- Seed staff
INSERT INTO staff (name)
SELECT 'Nishant'
WHERE NOT EXISTS (
    SELECT 1 FROM staff WHERE name = 'Nishant'
);

INSERT INTO staff (name)
SELECT 'Mahima'
WHERE NOT EXISTS (
    SELECT 1 FROM staff WHERE name = 'Mahima'
);

INSERT INTO staff (name)
SELECT 'BSG'
WHERE NOT EXISTS (
    SELECT 1 FROM staff WHERE name = 'BSG'
);

-- Seed courses
INSERT INTO courses (course_name, duration_weeks)
SELECT 'Data Analyst', 16
WHERE NOT EXISTS (
    SELECT 1 FROM courses WHERE course_name = 'Data Analyst'
);

INSERT INTO courses (course_name, duration_weeks)
SELECT 'Data Engineering', 20
WHERE NOT EXISTS (
    SELECT 1 FROM courses WHERE course_name = 'Data Engineering'
);

INSERT INTO courses (course_name, duration_weeks)
SELECT 'Web Development', NULL
WHERE NOT EXISTS (
    SELECT 1 FROM courses WHERE course_name = 'Web Development'
);

-- =========================================================
-- 8. SQL HELPERS (Functions for app queries)
-- =========================================================
-- Drop old versions to allow signature/return-type changes
DROP FUNCTION IF EXISTS public.get_lead_by_phone(VARCHAR(15));
DROP FUNCTION IF EXISTS public.upsert_lead_and_log(VARCHAR(15), VARCHAR(100), VARCHAR(100), VARCHAR(50), BOOLEAN, VARCHAR(100), INT, TEXT);

-- Upsert into lead_form and insert into call_logs in one call
CREATE OR REPLACE FUNCTION upsert_lead_and_log(
    p_phone_number VARCHAR(15),
    p_name VARCHAR(100),
    p_college_name VARCHAR(100),
    p_degree VARCHAR(50),
    p_employed BOOLEAN,
    p_course_interested VARCHAR(100),
    p_status VARCHAR(20),
    p_staff_id INT,
    p_log_text TEXT
) RETURNS VOID AS $$
BEGIN
    -- Upsert lead form entry
    INSERT INTO lead_form (phone_number, name, college_name, degree, employed, course_interested, status)
    VALUES (p_phone_number, p_name, p_college_name, p_degree, p_employed, p_course_interested, COALESCE(p_status, 'open'))
    ON CONFLICT (phone_number)
    DO UPDATE SET
        name = EXCLUDED.name,
        college_name = EXCLUDED.college_name,
        degree = EXCLUDED.degree,
        employed = EXCLUDED.employed,
        course_interested = EXCLUDED.course_interested,
        status = EXCLUDED.status,
        created_at = CURRENT_TIMESTAMP;

    -- Insert call log
    INSERT INTO call_logs (phone_number, staff_id, log_text)
    VALUES (p_phone_number, p_staff_id, COALESCE(p_log_text, 'Lead received via Streamlit form.'));
END;
$$ LANGUAGE plpgsql;

-- Lookup a lead by phone number
CREATE OR REPLACE FUNCTION get_lead_by_phone(
    p_phone_number VARCHAR(15)
) RETURNS TABLE (
    name VARCHAR(100),
    college_name VARCHAR(100),
    degree VARCHAR(50),
    employed BOOLEAN,
    course_interested VARCHAR(100),
    status VARCHAR(20)
) AS $$
    SELECT lf.name, lf.college_name, lf.degree, lf.employed, lf.course_interested, lf.status
    FROM lead_form lf
    WHERE lf.phone_number = p_phone_number;
$$ LANGUAGE sql STABLE;

-- Usage examples (for reference):
-- SELECT * FROM get_lead_by_phone('1234567890');
-- SELECT upsert_lead_and_log('1234567890', 'Alice', 'ABC College', 'BSc', FALSE, 'Data Analyst', 1, 'Initial call');
