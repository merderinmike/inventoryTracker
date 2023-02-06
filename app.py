import streamlit as st
import time
from pymongo import MongoClient
from dotenv import load_dotenv, find_dotenv
# ---page setup---
st.header("Project material tracker")
st.subheader("Add project material data to a database and create a spreadsheet from the data")

# ---config mongodb and connect to db---
load_dotenv(find_dotenv())
password = st.secrets["MONGOPW"]

cluster = MongoClient(
    f"""mongodb+srv://ashehorn:{password}@cluster0.soozxfm.mongodb.net/?retryWrites=true&w=majority""")
db = cluster["materialTracker"]
projects = db['Projects']
materials = db['Materials']
# ---Create tabs---
tab1, tab2 = st.tabs(['Add Project', 'Add Project Material'])

# ---Add project----

with tab1:
    with st.form("addProject", clear_on_submit=True):
        projectName = st.text_input("Enter the project name")
        projectLocation = st.text_input("Please enter the facility for the project")
        projectStart = st.date_input("What date did the project start?")
        projectEnd = st.date_input("What date did the project end?")
        projectLength = projectStart - projectEnd

        submit = st.form_submit_button("Submit")
        if submit:
            time.sleep(2)
            st.experimental_rerun()