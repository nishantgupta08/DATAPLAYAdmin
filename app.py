import streamlit as st
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
import os
from utils import get_staff_list, get_lead_by_phone, upsert_lead_and_log, get_call_logs, get_open_leads

# Load environment variables
load_dotenv()
DB_URL = os.getenv("NEON_DB_URL")

# Helper function to connect to NeonDB
def get_connection():
    return psycopg2.connect(DB_URL)

# Page setup
st.set_page_config(page_title="Lead Entry Form", page_icon="📞", layout="centered")

st.title("📋 Lead Form")
st.write("Staff can fill this form after receiving a lead call.")

# Open leads panel
open_leads = get_open_leads(limit=100)
if open_leads:
    st.subheader("Open Leads")
    st.dataframe(
        {
            "Phone": [row[0] for row in open_leads],
            "Name": [row[1] for row in open_leads],
            "College": [row[2] for row in open_leads],
            "Degree": [row[3] for row in open_leads],
            "Employed": [row[4] for row in open_leads],
            "Course": [row[5] for row in open_leads],
            "Status": [row[6] for row in open_leads],
            "Created": [row[7] for row in open_leads],
        },
        use_container_width=True,
    )

staff_list = get_staff_list()
staff_dict = {name: staff_id for staff_id, name in staff_list}


def _on_phone_change():
    phone = st.session_state.get("phone_number", "").strip()
    lead = get_lead_by_phone(phone)
    if lead:
        st.session_state["lead_name"] = lead.get("name", "")
        st.session_state["college_name"] = lead.get("college_name", "")
        st.session_state["degree"] = lead.get("degree", "")
        st.session_state["employed"] = lead.get("employed", False)
        st.session_state["course_interested"] = lead.get("course_interested", "")
        st.session_state["lead_status"] = lead.get("status", "open")
    else:
        # Clear fields when no lead found
        st.session_state.setdefault("lead_name", "")
        st.session_state.setdefault("college_name", "")
        st.session_state.setdefault("degree", "")
        st.session_state.setdefault("employed", False)
        st.session_state.setdefault("course_interested", "")
        st.session_state.setdefault("lead_status", "open")

# Phone input outside the form to allow on_change callback
st.text_input(
    "Phone Number",
    max_chars=15,
    key="phone_number",
    on_change=_on_phone_change,
)

# Call logs panel for the current phone number
current_phone = st.session_state.get("phone_number", "")
if current_phone:
    st.subheader("Recent Call Logs")
    logs = get_call_logs(current_phone, limit=10)
    if logs:
        # Convert to a simple tabular form
        st.dataframe(
            {
                "Time": [row[0] for row in logs],
                "Staff": [row[1] for row in logs],
                "Log": [row[2] for row in logs],
            },
            use_container_width=True,
        )
    else:
        st.info("No call logs for this phone number yet.")

# --- Lead Form ---
with st.form("lead_form"):
    st.subheader("Lead Details")

    staff_name = st.selectbox(
        "Staff Name",
        options=list(staff_dict.keys()) if staff_list else ["No staff found"],
    )
    name = st.text_input("Lead Name", key="lead_name", value=st.session_state.get("lead_name", ""))
    college_name = st.text_input("College Name", key="college_name", value=st.session_state.get("college_name", ""))
    degree = st.text_input("Degree", key="degree", value=st.session_state.get("degree", ""))
    employed = st.checkbox("Currently Employed?", key="employed", value=st.session_state.get("employed", False))
    course_interested = st.text_input("Course Interested In", key="course_interested", value=st.session_state.get("course_interested", ""))
    status_options = ["open", "closed", "enrolled"]
    current_status = st.session_state.get("lead_status", "open")
    status_index = status_options.index(current_status) if current_status in status_options else 0
    status = st.selectbox(
        "Lead Status",
        options=status_options,
        index=status_index,
        key="lead_status"
    )
    log_text = st.text_area("Call Log", key="log_text", value=st.session_state.get("log_text", ""))

    submitted = st.form_submit_button("Submit Lead")

    if submitted:
        if not st.session_state.get("phone_number", "") or not name:
            st.warning("⚠️ Please fill in at least the phone number and name.")
        else:
            ok = upsert_lead_and_log(
                phone_number=st.session_state.get("phone_number", ""),
                name=name,
                college_name=college_name,
                degree=degree,
                employed=employed,
                course_interested=course_interested,
                status=status,
                staff_id=staff_dict.get(staff_name),
                log_text=log_text or None,
            )
            if ok:
                st.success("✅ Lead saved successfully!")
