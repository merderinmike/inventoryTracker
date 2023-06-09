import streamlit as st
from streamlit_option_menu import option_menu
import time
import pandas as pd
import psycopg2
import calendar
import decimal
from dotenv import load_dotenv, find_dotenv

# ---page setup---
st.header("Project material tracker")

# ---config postgresql and connect to db---
load_dotenv(find_dotenv())
db_host = st.secrets["DB_HOST"]
db_port = st.secrets["DB_PORT"]
db_name = st.secrets["DB_NAME"]
db_user = st.secrets["DB_USER"]
db_password = st.secrets["DB_PASSWORD"]

conn = psycopg2.connect(
    host=db_host,
    port=db_port,
    dbname=db_name,
    user=db_user,
    password=db_password
)
cursor = conn.cursor()

# Create 'projects' table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        project_name VARCHAR(255) PRIMARY KEY,
        location VARCHAR(255),
        project_start DATE
    )
""")

# Create 'materials' table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS materials (
        material_name VARCHAR(255) PRIMARY KEY,
        cost NUMERIC(10, 2)
    )
""")

# Create 'project_materials' table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS project_materials (
        material_name VARCHAR(255),
        month_used VARCHAR(255),
        project_name VARCHAR(255),
        amount_used NUMERIC(10, 2),
        cost FLOAT,
        FOREIGN KEY (material_name) REFERENCES materials (material_name),
        FOREIGN KEY (project_name) REFERENCES projects (project_name)
    )
""")

# Commit the changes and close the connection
conn.commit()

def get_material_cost(material):
    cursor.execute("SELECT cost FROM materials WHERE material_name = %s", (material,))
    return cursor.fetchone()[0]
# ---Create tabs, columns---
menu = option_menu(
    menu_title=None,
    options=["Project", "Add Material", "Create Report"],
    icons=["clipboard", "clipboard-plus", "file-earmark-arrow-down"],
    orientation="horizontal",
)

# ---Add project----
if menu == "Project":
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Add a project to start tracking materials")
        with st.form("addProject", clear_on_submit=True):
            projectName = st.text_input("Enter the project name")
            projectLocation = st.text_input("Please enter the facility for the project")
            projectStart = str(st.date_input("What date did the project start?"))
            if st.form_submit_button("Submit"):
                cursor.execute(
                    "SELECT COUNT(*) FROM projects WHERE project_name = %s",
                    (projectName,)
                )
                if cursor.fetchone()[0] != 0:
                    st.error("Project already exists!")
                else:
                    cursor.execute(
                        "INSERT INTO projects (project_name, location, project_start) VALUES (%s, %s, %s)",
                        (projectName, projectLocation, projectStart)
                    )
                    conn.commit()
                    conn.close()
                    st.success("Project created successfully!")
                    time.sleep(2)
                    st.experimental_rerun()
    with col2:
        st.subheader("Add material to a project")
        cursor.execute("SELECT project_name FROM projects")
        projectSelect = cursor.fetchall()
        findMaterials = cursor.execute("SELECT material_name FROM materials")
        materialSelect = cursor.fetchall()
        selection = ["Select A Project"]
        material_list = []
        data = []
        for project in projectSelect:
            selection.append(f"{project[0]}")
        for material in materialSelect:
            material_list.append(f"{material[0]}")
        projectSelection = st.selectbox("Please select a Project", selection, key="projectSelection")
        month = calendar.month_name[1:]
        MonthSelection = st.selectbox("Please select the month the material was used", month, key="MonthSelection")
        if "Select A Project" not in projectSelection:
            amount = {}
            cost = {}
            multiSelect = st.multiselect("Select Material Used", material_list, key="multiSelect")
            for x in multiSelect:
                amount[x] = st.number_input(f"How much of {x} was used?", value=0, key=x)
                cost[x] = get_material_cost(x)

            if st.button("Submit"):
                data = []
                has_new_materials = False  # Flag to check if there are new materials to insert

                # Loop over selected materials and get amount and cost
                for material in amount:
                    if amount[material] > 0:
                        # Check if the material already exists for the project and month
                        cursor.execute(
                            """
                            SELECT COUNT(*)
                            FROM project_materials
                            WHERE project_name = %s
                            AND month_used = %s
                            AND material_name = %s
                            """,
                            (projectSelection, MonthSelection, material)
                        )
                        count = cursor.fetchone()[0]

                        if count == 0:
                            # Material does not exist, insert a new entry
                            data.append((projectSelection, material, amount[material], MonthSelection, cost[material]))
                            has_new_materials = True
                        else:
                            # Material exists, update the amount_used
                            cursor.execute(
                                """
                                UPDATE project_materials
                                SET amount_used = amount_used + %s
                                WHERE project_name = %s
                                AND month_used = %s
                                AND material_name = %s
                                """,
                                (amount[material], projectSelection, MonthSelection, material)
                            )

                # Execute the insert or update operation
                if has_new_materials:
                    cursor.executemany(
                        "INSERT INTO project_materials (project_name, material_name, amount_used, month_used, cost) VALUES (%s, %s, %s, %s, %s)",
                        data
                    )

                conn.commit()
                st.success("Material Successfully added to project!")
                time.sleep(1.2)
                st.session_state.clear()
                st.session_state.projectSelection = selection[0]
                st.session_state.multiSelect = []
                st.experimental_rerun()

# ---Add Material to DB---
if menu == "Add Material":
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("From spreadsheet")
        with st.form("material_from_csv", clear_on_submit=True):
            spreadsheet = st.file_uploader("Select a file to add material", type=['.csv'], key="spreadsheet")
            submit = st.form_submit_button("Submit")
            if submit:
                df = pd.read_csv(spreadsheet)
                df_dict = df.to_dict("records")
                for item in df_dict:
                    cursor.execute(
                        "INSERT INTO materials (material_name, cost) VALUES (%s, %s)",
                        (item["material_name"], item["cost"])
                    )
                conn.commit()

    with col2:
        st.subheader("Add Manually")
        with st.form("newMaterial", clear_on_submit=True):
            materialName = st.text_input("Enter material name: ")
            materialCost = st.number_input("Enter material cost (Please leave out the $): ", value=0)
            if st.form_submit_button("submit"):
                cursor.execute(
                    "SELECT COUNT(*) FROM materials WHERE material_name = %s",
                    (materialName,)
                )
                if cursor.fetchone()[0] != 0:
                    st.error("Material already exists!")
                else:
                    cursor.execute(
                        "INSERT INTO materials (material_name, cost) VALUES (%s, %s)",
                        (materialName, materialCost)
                    )
                    conn.commit()
                    st.success("Material added successfully!")
                    time.sleep(2)
                    st.experimental_rerun()

# ---Create Report---
if menu == "Create Report":
    st.subheader("Generate a CSV file report for a project")
    cursor.execute("SELECT project_name FROM projects")
    projectSelect = cursor.fetchall()
    selection = ["Select A Project"]
    for project in projectSelect:
        selection.append(f"{project[0]}")
    getProject = st.selectbox("Select a project", selection)
    month = calendar.month_name[1:]
    selected_month = st.selectbox("Select a month", ["All"] + month)
    if selected_month == "All":
        cursor.execute(
            """
            SELECT p.project_name, p.location, p.project_start, m.material_name, pm.amount_used, pm.cost
            FROM projects p
            JOIN project_materials pm ON p.project_name = pm.project_name
            JOIN materials m ON pm.material_name = m.material_name
            WHERE p.project_name = %s
            """,
            (getProject,)
        )
    else:
        cursor.execute(
            """
            SELECT p.project_name, p.location, p.project_start, m.material_name, pm.amount_used, pm.cost
            FROM projects p
            JOIN project_materials pm ON p.project_name = pm.project_name
            JOIN materials m ON pm.material_name = m.material_name
            WHERE p.project_name = %s
            AND pm.month_used = %s
            """,
            (getProject, selected_month)
        )
    createReport = cursor.fetchall()
    df = pd.DataFrame(createReport, columns=["Project Name", "Location", "Start Date", "Material Name", "Amount Used", "Cost"])
    
    # Calculate the total cost and add a "Total" row
    total_cost = sum(decimal.Decimal(row[4]) * decimal.Decimal(row[5]) for row in createReport)
    total_row = pd.Series(["", "", "", "", "Total", total_cost], index=df.columns)
    df = df.append(total_row, ignore_index=True)

    # Enlarge the table
    table = st.dataframe(df)

    file = df.to_csv(index=False)
    st.download_button(
        label="Generate Report",
        data=file,
        file_name=f"{getProject}.csv",
        mime='text/csv'
    )