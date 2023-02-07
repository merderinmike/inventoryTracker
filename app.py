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

# ---Create tabs, columns---
tab1, tab2 = st.tabs(['Add Project', 'Add Project Material'])

# ---Add project----

with tab1:
    with st.form("addProject", clear_on_submit=True):
        projectName = st.text_input("Enter the project name")
        projectLocation = st.text_input("Please enter the facility for the project")
        projectStart = st.date_input("What date did the project start?")
        #projectEnd = st.date_input("What date did the project end?")
        #projectLength = projectEnd - projectStart
        if st.form_submit_button("Submit"):
            if projects.count_documents({'_id': projectName}) != 0:
                st.error("Project already exists!")
            else:
                db['Projects'].insert_one({"_id":projectName, "Location":projectLocation,"Start":projectStart})
                st.success("Project created successfully!")
                time.sleep(2)
                st.experimental_rerun()

with tab2:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Add material to a project")
        #projectSelect = list(projects.find())
        #findMaterials = list(materials.find())
        selection = ["Select A Project"]
        material = []
        #for project in projectSelect:
            #selection.append(f"{project['_id']}")
        #for item in findMaterials:
            #material.append(f"{item['_id']}")
        if "Select A Project" not in st.selectbox("Please select a Project", [selection]):
            with st.form("projectMaterial"):
                multiSelect = st.multiselect("Select Material Used", [material])
                for x in multiSelect:
                    amount = st.number_input(f"How much of {x} was used?")
                if st.form_submit_button("Submit"):
                    st.experimental_rerun()
    with col2:
        st.subheader("Add a new material!")
        with st.form("newMaterial", clear_on_submit=True):
            st.text_input("Enter material name: ")
            st.number_input("Enter material cost(Please leave out the $): ", value=0)
            st.form_submit_button("submit")