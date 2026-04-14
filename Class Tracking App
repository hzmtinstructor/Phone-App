import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime
from io import StringIO

DATA_FILE = "progress.json"
CLASS_FILE = "classes.json"

# -------------------------
# LOAD / SAVE
# -------------------------
def load_progress():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_progress(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def load_classes():
    if os.path.exists(CLASS_FILE):
        with open(CLASS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_classes(data):
    with open(CLASS_FILE, "w") as f:
        json.dump(data, f)

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
    st.session_state.progress = load_progress()
if "classes" not in st.session_state:
    st.session_state.classes = load_classes()

# -------------------------
# HEADER
# -------------------------
st.title("Class Setup Dashboard")

# -------------------------
# SEARCH
# -------------------------
search = st.text_input("Search Classes").lower()
class_names = [c for c in st.session_state.classes if search in c.lower()] if search else list(st.session_state.classes.keys())

# -------------------------
# CSV EXPORT (WORKS EVERYWHERE)
# -------------------------
def generate_csv():
    rows = []

    for cls, data in st.session_state.classes.items():
        row = {
            "Class Name": cls,
            "Course Code": data.get("course_code", ""),
            "OSFM Portal": data.get("osfm_portal", ""),
            "Instructor": data.get("instructor", ""),
            "Start Date": data.get("start_date", ""),
            "End Date": data.get("end_date", ""),
            "Location": data.get("location", ""),
            "Class Time 1": data.get("class_time1", ""),
            "Class Time 2": data.get("class_time2", ""),
            "Comments": data.get("comments", ""),
            "Visitation Date": data.get("visitation_date", "")
        }

        # Add checklist statuses
        for item in CHECKLIST_ITEMS:
            key = f"{cls}_{item}"
            status = st.session_state.progress.get(key, {}).get("status", "Not Started")
            row[item] = status

        rows.append(row)

    df = pd.DataFrame(rows)

    output = StringIO()
    df.to_csv(output, index=False)
    return output.getvalue()

# -------------------------
# DOWNLOAD BUTTON
# -------------------------
st.subheader("Export Data")

csv_data = generate_csv()

st.download_button(
    label="Download CSV Report (Open in Excel)",
    data=csv_data,
    file_name=f"class_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
    mime="text/csv"
)

# -------------------------
# OVERALL PROGRESS
# -------------------------
if class_names:
    st.subheader("Overall Class Progress")

    def get_date(c):
        try:
            return datetime.strptime(st.session_state.classes[c].get("start_date",""), "%Y-%m-%d")
        except:
            return datetime.today()

    for cls in sorted(class_names, key=get_date):
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
# ADD NEW CLASS
# -------------------------
st.subheader("Add New Class")

with st.form("add_class_form"):
    name = st.text_input("Class Name")
    course_code = st.text_input("Course Code and Section Number")
    osfm_portal = st.text_input("OSFM Portal Number")
    instructor = st.text_input("Instructor")

    col1, col2 = st.columns(2)
    start_date = col1.date_input("Start Date")
    end_date = col2.date_input("End Date")

    location = st.text_input("Location")
    class_time1 = st.text_input("Class Times 1")
    class_time2 = st.text_input("Class Times 2")
    comments = st.text_area("Comments", height=100)

    submitted = st.form_submit_button("Add Class")

    if submitted and name:
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

        save_classes(st.session_state.classes)
        st.success(f"Added class: {name}")
        st.rerun()

# -------------------------
# DELETE CLASSES
# -------------------------
st.subheader("Delete Classes")

if st.session_state.classes:
    to_delete = st.multiselect("Select classes", list(st.session_state.classes.keys()))
    if st.button("Delete Selected"):
        for cls in to_delete:
            st.session_state.classes.pop(cls, None)

        st.session_state.progress = {
            k:v for k,v in st.session_state.progress.items()
            if not any(k.startswith(f"{cls}_") for cls in to_delete)
        }

        save_classes(st.session_state.classes)
        save_progress(st.session_state.progress)

        st.success("Deleted")
        st.rerun()

# -------------------------
# CLASS CHECKLISTS
# -------------------------
if class_names:
    st.subheader("Class Checklists")

    for cls in class_names:
        with st.expander(cls):
            for item in CHECKLIST_ITEMS:
                key = f"{cls}_{item}"

                if key not in st.session_state.progress:
                    st.session_state.progress[key] = {"status":"Not Started"}

                val = st.session_state.progress[key]["status"]

                new_status = st.selectbox(
                    item,
                    STATUS_OPTIONS,
                    index=STATUS_OPTIONS.index(val),
                    key=key
                )

                st.session_state.progress[key]["status"] = new_status

    save_progress(st.session_state.progress)

else:
    st.info("No classes found")
