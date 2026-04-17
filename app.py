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
# STATE INIT
# -------------------------
if "progress" not in st.session_state:
    st.session_state.progress = load_json(DATA_FILE)

if "classes" not in st.session_state:
    st.session_state.classes = load_json(CLASS_FILE)

# -------------------------
# FORM RESET SYSTEM (SAFE)
# -------------------------
defaults = {
    "form_name": "",
    "form_course": "",
    "form_osfm": "",
    "form_instructor": "",
    "form_start": datetime.today(),
    "form_end": datetime.today(),
    "form_location": "",
    "form_t1": "",
    "form_t2": "",
    "form_comments": ""
}

if "reset_form" not in st.session_state:
    st.session_state.reset_form = False

if st.session_state.reset_form:
    for k, v in defaults.items():
        st.session_state[k] = v
    st.session_state.reset_form = False

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# -------------------------
# HEADER
# -------------------------
st.title("Stanly Community College Class Setup Dashboard")

# -------------------------
# SEARCH
# -------------------------
search = st.text_input("Search Classes").lower()
class_names = [
    c for c in st.session_state.classes
    if search in c.lower()
] if search else list(st.session_state.classes.keys())

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
# DASHBOARD
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

    st.text_input("Class Name", key="form_name")
    st.text_input("Course Code", key="form_course")
    st.text_input("OSFM Portal", key="form_osfm")
    st.text_input("Instructor", key="form_instructor")

    col1, col2 = st.columns(2)
    col1.date_input("Start Date", key="form_start")
    col2.date_input("End Date", key="form_end")

    st.text_input("Location", key="form_location")
    st.text_input("Class Times 1", key="form_t1")
    st.text_input("Class Times 2", key="form_t2")
    st.text_area("Comments", key="form_comments")

    col_add, col_clear = st.columns(2)
    submitted = col_add.form_submit_button("Add Class")
    cleared = col_clear.form_submit_button("Clear Fields")

# Handle actions AFTER form
if submitted and st.session_state.form_name:

    name = st.session_state.form_name

    st.session_state.classes[name] = {
        "course_code": st.session_state.form_course,
        "osfm_portal": st.session_state.form_osfm,
        "start_date": st.session_state.form_start.strftime("%Y-%m-%d"),
        "end_date": st.session_state.form_end.strftime("%Y-%m-%d"),
        "instructor": st.session_state.form_instructor,
        "location": st.session_state.form_location,
        "class_time1": st.session_state.form_t1,
        "class_time2": st.session_state.form_t2,
        "comments": st.session_state.form_comments,
        "visitation_date": ""
    }

    log_change(name, "Class Created", "", "New Class")
    save_json(CLASS_FILE, st.session_state.classes)

    st.session_state.reset_form = True
    st.success(f"Added class: {name}")
    st.rerun()

if cleared:
    st.session_state.reset_form = True
    st.rerun()

# -------------------------
# DELETE
# -------------------------
st.subheader("Delete Classes")

if st.session_state.classes:
    to_delete = st.multiselect("Select classes", list(st.session_state.classes.keys()))

    if st.button("Delete Selected"):
        for cls in to_delete:
            log_change(cls, "Class Deleted", "Exists", "Deleted")
            st.session_state.classes.pop(cls, None)

        st.session_state.progress = {
            k:v for k,v in st.session_state.progress.items()
            if not any(k.startswith(f"{cls}_") for cls in to_delete)
        }

        save_json(CLASS_FILE, st.session_state.classes)
        save_json(DATA_FILE, st.session_state.progress)
        st.rerun()

# -------------------------
# CLASS DETAILS + CHECKLIST (FULL RESTORE)
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

            try:
                start_val = datetime.strptime(data.get("start_date",""), "%Y-%m-%d")
            except:
                start_val = datetime.today()

            try:
                end_val = datetime.strptime(data.get("end_date",""), "%Y-%m-%d")
            except:
                end_val = datetime.today()

            new_start = col1.date_input("Start Date", start_val, key=f"{cls}_start")
            new_end = col2.date_input("End Date", end_val, key=f"{cls}_end")

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

                new_status = st.selectbox(item, STATUS_OPTIONS,
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

            if st.button(f"Save {cls}", key=f"{cls}_save"):

                final_name = new_name.strip()

                if final_name and final_name != cls:
                    st.session_state.classes[final_name] = st.session_state.classes.pop(cls)

                st.session_state.classes[final_name].update({
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

                st.success(f"Updated {final_name}")
                st.rerun()

    save_json(DATA_FILE, st.session_state.progress)

else:
    st.info("No classes found")
