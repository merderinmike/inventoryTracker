import streamlit as st
import time
import pandas as pd
from streamlit_option_menu import option_menu
from pymongo import MongoClient
from dotenv import load_dotenv, find_dotenv

# ---page setup---
st.header("Project material tracker")
# ---config mongodb and connect to db---
load_dotenv(find_dotenv())
password = st.secrets["MONGOPW"]
cluster = MongoClient(
    f"""mongodb+srv://ashehorn:{password}@cluster0.soozxfm.mongodb.net/?retryWrites=true&w=majority""")
db = cluster["materialTracker"]
projects = db['Projects']
materials = db['Materials']
projectsMaterial = db['projectMaterial']

# ---Create tabs, columns---
menu = option_menu(
    menu_title=None,
    options=["Add Project", "Add Material", "Create Report"],
    icons=["clipboard", "clipboard-plus", "file-earmark-arrow-down"],
    orientation="horizontal",
)
# ---Add project----
if menu == "Add Project":
    st.subheader("Add a project to start tracking materials")
    with st.form("addProject", clear_on_submit=True):
        projectName = st.text_input("Enter the project name")
        projectLocation = st.text_input("Please enter the facility for the project")
        projectStart = str(st.date_input("What date did the project start?"))
        if st.form_submit_button("Submit"):
            if projects.count_documents({'_id': projectName}) != 0:
                st.error("Project already exists!")
            else:
                db['Projects'].insert_one(
                    {"_id": projectName, "Location": projectLocation, "Start": projectStart, "materials": []})
                projectsMaterial.insert_one({'_id': projectName})
                st.success("Project created successfully!")
                time.sleep(2)
                st.experimental_rerun()

# ---Add Material to project---
if menu == "Add Material":
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Add material to a project")
        projectSelect = list(projects.find())
        findMaterials = list(materials.find())
        selection = ["Select A Project"]
        material = []
        data = []
        for project in projectSelect:
            selection.append(f"{project['_id']}")
        for item in findMaterials:
            material.append(f"{item['_id']}")
        projectSelection = st.selectbox("Please select a Project", selection, key="projectSelection")
        location = st.text_input("Please enter the location where the material was used (Floor, building, etc.)", key="location")
        if "Select A Project" not in projectSelection:
            amount = {}
            multiSelect = st.multiselect("Select Material Used", material, key="multiSelect")
            for x in multiSelect:
                amount[x] = st.number_input(f"How much of {x} was used?",value=0)
            if st.button("Submit"):
                projectsMaterial.update_one({'_id': projectSelection}, {'$inc': amount})
                st.experimental_rerun()
    # ---Add Material to DB---
    with col2:
        st.subheader("Add a new material")
        with st.form("newMaterial", clear_on_submit=True):
            materialName = st.text_input("Enter material name: ")
            materialCost = st.number_input("Enter material cost (Please leave out the $): ", value=0)
            if st.form_submit_button("submit"):
                if materials.count_documents({'_id': materialName}) != 0:
                    st.error("Material already exists!")
                else:
                    materials.insert_one({"_id": materialName, "cost": materialCost})
                    st.success("Material added successfully!")
                    time.sleep(2)
                    st.experimental_rerun()
# ---Create Report---
if menu == "Create Report":
    st.subheader("Generate a CSV file report for a project")
    projectSelect = list(projects.find())
    selection = ["Select A Project"]
    for project in projectSelect:
        selection.append(f"{project['_id']}")
    getProject = st.selectbox("Select a project", selection)
    createReport = list(projects.find({'_id': getProject}))
    getMaterials = list(projectsMaterial.find({'_id': getProject}))
    get_cost = list(materials.find())
    for report in createReport:
        createReport = report
    for item in getMaterials:
        createReport.update(item)
        df = pd.DataFrame.from_dict(createReport, orient="index")
        col1, col2, col3 = st.columns(3)
        col2.dataframe(df)
        file = df.to_csv()
        col2.download_button(
            label="Generate Report",
            data=file,
            file_name=f"{getProject}.csv",
            mime='text/csv')
