import os
import psycopg2
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DB_URL = os.getenv("NEON_DB_URL")


def get_staff_list():
    try:
        with psycopg2.connect(DB_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT staff_id, name FROM staff ORDER BY name;")
                return cur.fetchall()
    except Exception as e:
        st.error(f"Error fetching staff list: {e}")
        return []


def get_lead_by_phone(phone_number: str):
    if not phone_number:
        return None
    try:
        with psycopg2.connect(DB_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT name, college_name, degree, employed, course_interested, status
                    FROM public.get_lead_by_phone(%s::varchar(15))
                    """,
                    (phone_number,),
                )
                row = cur.fetchone()
                if not row:
                    return None
                return {
                    "name": row[0] or "",
                    "college_name": row[1] or "",
                    "degree": row[2] or "",
                    "employed": bool(row[3]) if row[3] is not None else False,
                    "course_interested": row[4] or "",
                    "status": row[5] or "open",
                }
    except Exception as e:
        st.error(f"Error fetching lead details: {e}")
        return None


def upsert_lead_and_log(
    phone_number: str,
    name: str,
    college_name: str,
    degree: str,
    employed: bool,
    course_interested: str,
    status: str,
    staff_id: int,
    log_text: str | None,
):
    try:
        with psycopg2.connect(DB_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT upsert_lead_and_log(
                        %s, %s, %s, %s, %s, %s, %s, %s, %s
                    );
                    """,
                    (
                        phone_number,
                        name,
                        college_name,
                        degree,
                        employed,
                        course_interested,
                        status,
                        staff_id,
                        log_text,
                    ),
                )
                conn.commit()
        return True
    except Exception as e:
        st.error(f"Error saving lead: {e}")
        return False


def get_call_logs(phone_number: str, limit: int = 10):
    if not phone_number:
        return []
    try:
        with psycopg2.connect(DB_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT cl.timestamp, s.name AS staff_name, cl.log_text
                    FROM call_logs cl
                    JOIN staff s ON s.staff_id = cl.staff_id
                    WHERE cl.phone_number = %s
                    ORDER BY cl.timestamp DESC
                    LIMIT %s
                    """,
                    (phone_number, limit),
                )
                return cur.fetchall()
    except Exception as e:
        st.error(f"Error fetching call logs: {e}")
        return []


def get_open_leads(limit: int = 100):
    try:
        with psycopg2.connect(DB_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT phone_number, name, college_name, degree, employed, course_interested, status, created_at
                    FROM lead_form
                    WHERE status = 'open'
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                return cur.fetchall()
    except Exception as e:
        st.error(f"Error fetching open leads: {e}")
        return []


