import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime
from io import StringIO

DATA_FILE = "progress.json"
CLASS_FILE = "classes.json"
AUDIT_FILE = "audit.json"

# -------------------------
# LOAD / SAVE
# -------------------------
def load_json(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return {}

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

# -------------------------
# AUDIT LOGGING
# -------------------------
def log_change(cls, field, old, new):
    if old == new:
        return
    audit = load_json(AUDIT_FILE)
    audit.setdefault("history", []).append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "class": cls,
        "field": field,
        "old_value": old,
        "new_value": new
    })
    save_json(AUDIT_FILE, audit)

# -------------------------
# CONSTANTS
# -------------------------
CHECKLIST_ITEMS = [
    "Set up to Allison","Packet Made","Packet Completed","Packet Delivered",
    "OSFM Portal","Notifications","Packet Picked Up","Test Graded",
    "Completed Class to Allison","OSFM Report Confirmed",
    "Class Visitation"
]

STATUS_OPTIONS = ["Not Started", "Complete", "Not Applicable"]

# -------------------------
# STATE
# -------------------------
if "progress" not in st.session_state:
    st.session_state.progress = load_json(DATA_FILE)

if "classes" not in st.session_state:
    st.session_state.classes = load_json(CLASS_FILE)

# -------------------------
# HEADER
# -------------------------
st.title("Stanly Community College Class Setup Dashboard")

# -------------------------
# SEARCH
# -------------------------
search = st.text_input("Search Classes").lower()
class_names = [c for c in st.session_state.classes if search in c.lower()] if search else list(st.session_state.classes.keys())

# -------------------------
# EXPORTS
# -------------------------
def generate_csv():
    rows = []
    for cls, data in st.session_state.classes.items():
        row = {"Class Name": cls, **data}
        for item in CHECKLIST_ITEMS:
            key = f"{cls}_{item}"
            row[item] = st.session_state.progress.get(key, {}).get("status", "Not Started")
        rows.append(row)

    df = pd.DataFrame(rows)
    output = StringIO()
    df.to_csv(output, index=False)
    return output.getvalue()

def generate_audit_csv():
    audit = load_json(AUDIT_FILE)
    df = pd.DataFrame(audit.get("history", []))
    output = StringIO()
    df.to_csv(output, index=False)
    return output.getvalue()

st.subheader("Export Data")

st.download_button("Download Class Report", generate_csv(), "class_report.csv")
st.download_button("Download Audit History", generate_audit_csv(), "audit_history.csv")

# -------------------------
# PROGRESS DASHBOARD
# -------------------------
if class_names:
    st.subheader("Overall Class Progress")

    for cls in class_names:
        data = st.session_state.classes[cls]

        completed = sum(
            1 for item in CHECKLIST_ITEMS
            if st.session_state.progress.get(f"{cls}_{item}", {}).get("status","Not Started")
            in ["Complete","Not Applicable"]
        )

        total = len(CHECKLIST_ITEMS)
        pct = completed / total if total else 0

        color = "#28a745" if pct == 1 else "#ffc107" if pct > 0 else "#dc3545"

        st.markdown(f"**{cls} — {data.get('start_date','')}** ({completed}/{total})")

        st.markdown(f"""
        <div style="background:#eee;height:20px;border-radius:5px;">
            <div style="width:{pct*100}%;background:{color};height:20px;border-radius:5px;"></div>
        </div>
        """, unsafe_allow_html=True)

# -------------------------
# ADD CLASS
# -------------------------
st.subheader("Add New Class")

with st.form("add_class_form"):
    name = st.text_input("Class Name")
    course_code = st.text_input("Course Code")
    osfm_portal = st.text_input("OSFM Portal")
    instructor = st.text_input("Instructor")

    col1, col2 = st.columns(2)
    start_date = col1.date_input("Start Date")
    end_date = col2.date_input("End Date")

    location = st.text_input("Location")
    class_time1 = st.text_input("Class Times 1")
    class_time2 = st.text_input("Class Times 2")
    comments = st.text_area("Comments")

    if st.form_submit_button("Add Class") and name:
        st.session_state.classes[name] = {
            "course_code": course_code,
            "osfm_portal": osfm_portal,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "instructor": instructor,
            "location": location,
            "class_time1": class_time1,
            "class_time2": class_time2,
            "comments": comments,
            "visitation_date": ""
        }

        log_change(name, "Class Created", "", "New Class")

        save_json(CLASS_FILE, st.session_state.classes)
        st.rerun()

# -------------------------
# CLASS DETAILS + CHECKLIST (FULLY RESTORED)
# -------------------------
if class_names:
    st.subheader("Class Checklists")

    for cls in class_names:
        data = st.session_state.classes[cls]

        with st.expander(cls):

            st.markdown("### Class Setup Information")

            new_name = st.text_input("Class Name", cls, key=f"{cls}_name")
            new_course = st.text_input("Course Code", data.get("course_code",""), key=f"{cls}_course")
            new_osfm = st.text_input("OSFM Portal", data.get("osfm_portal",""), key=f"{cls}_osfm")
            new_inst = st.text_input("Instructor", data.get("instructor",""), key=f"{cls}_inst")

            col1, col2 = st.columns(2)
            new_start = col1.date_input("Start Date", datetime.today(), key=f"{cls}_start")
            new_end = col2.date_input("End Date", datetime.today(), key=f"{cls}_end")

            new_loc = st.text_input("Location", data.get("location",""), key=f"{cls}_loc")
            new_t1 = st.text_input("Class Times 1", data.get("class_time1",""), key=f"{cls}_t1")
            new_t2 = st.text_input("Class Times 2", data.get("class_time2",""), key=f"{cls}_t2")
            new_comm = st.text_area("Comments", data.get("comments",""), key=f"{cls}_comm")

            st.markdown("### Checklist")

            for item in CHECKLIST_ITEMS:
                key = f"{cls}_{item}"

                if key not in st.session_state.progress:
                    st.session_state.progress[key] = {"status": "Not Started"}

                old_status = st.session_state.progress[key]["status"]

                new_status = st.selectbox(
                    item,
                    STATUS_OPTIONS,
                    index=STATUS_OPTIONS.index(old_status),
                    key=f"{key}_status"
                )

                if new_status != old_status:
                    log_change(cls, item, old_status, new_status)

                st.session_state.progress[key]["status"] = new_status

                if item == "Class Visitation":
                    if new_status == "Complete":
                        visit_date = st.date_input("Visitation Date", datetime.today(), key=f"{cls}_visit")
                        st.session_state.classes[cls]["visitation_date"] = visit_date.strftime("%Y-%m-%d")

            if st.button(f"Save {cls}"):

                # rename logic
                if new_name != cls:
                    st.session_state.classes[new_name] = st.session_state.classes.pop(cls)

                st.session_state.classes[new_name].update({
                    "course_code": new_course,
                    "osfm_portal": new_osfm,
                    "start_date": new_start.strftime("%Y-%m-%d"),
                    "end_date": new_end.strftime("%Y-%m-%d"),
                    "instructor": new_inst,
                    "location": new_loc,
                    "class_time1": new_t1,
                    "class_time2": new_t2,
                    "comments": new_comm
                })

                save_json(CLASS_FILE, st.session_state.classes)
                save_json(DATA_FILE, st.session_state.progress)

                st.success(f"Updated {new_name}")
                st.rerun()
