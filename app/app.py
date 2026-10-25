import streamlit as st
import pandas as pd
from modules.normalization_engine import normalize_schema
from modules.schema_generator import generate_relational_schema
from modules.sql_generator import generate_sql
from modules.erd_parser import parse_erd

# Initialize session state storage
if "entities" not in st.session_state:
    st.session_state.entities = {}

if "relationships" not in st.session_state:
    st.session_state.relationships = []

st.set_page_config(page_title="ER to Relational Schema Tool", layout="wide")

st.title("📌 Automated ER-to-Relational Schema & Normalization Tool")

# Sidebar Menu
menu = st.sidebar.radio(
    "Navigation",
    [
        "➕ Add Entities",
        "🔗 Add Relationships",
        "📄 Generate & View Schema / SQL",
        "🧠 Normalization Analysis",
        "📁 Export & Download",
        "ℹ About Project"
    ]
)


# ---------------------------------------------------------------
# 1️⃣ ADD ENTITY PAGE
# ---------------------------------------------------------------
if menu == "Home" or menu == "":
    st.markdown("<h1 style='text-align:center;'>📌 Automated ER-to-Relational Schema & Normalization Tool</h1>", unsafe_allow_html=True)
    st.write("Welcome! Use the navigation on the left to begin.")

if menu == "➕ Add Entities":
    st.header("➕ Add Entity")

    with st.form("entity_form"):
        entity_name = st.text_input("Enter Entity Name")
        attributes = st.text_input("Enter Attributes (comma separated)")
        primary_key = st.text_input("Enter Primary Key (comma separated)")

        is_weak = st.checkbox("Is this a Weak Entity?")
        owner = None
        if is_weak:
            existing_entities = list(st.session_state.entities.keys())

            owner_options = existing_entities.copy()  # individual

            # Add pair combinations (e.g., Student & Course)
            if len(existing_entities) > 1:
                for i in range(len(existing_entities)):
                    for j in range(i + 1, len(existing_entities)):
                        owner_options.append(existing_entities[i] + " & " + existing_entities[j])

            owner = st.selectbox("Select Owner Entity (Single or Combined)", owner_options)

        else:
            st.warning("Add at least one main entity before creating a weak entity.")

        submit_entity = st.form_submit_button("Add Entity")

    if submit_entity:
        attribute_list = [x.strip() for x in attributes.split(",")] if attributes else []
        primary_key_list = [x.strip() for x in primary_key.split(",")] if primary_key else []

        # If entity already exists, update it
        if entity_name in st.session_state.entities:
            st.session_state.entities[entity_name]["attributes"] = attribute_list
            st.session_state.entities[entity_name]["primary_key"] = primary_key_list
            st.session_state.entities[entity_name]["weak"] = is_weak
            st.session_state.entities[entity_name]["owner"] = owner
        else:
            # If new entity
            st.session_state.entities[entity_name] = {
                "attributes": attribute_list,
                "primary_key": primary_key_list,
                "weak": is_weak,
                "owner": owner,
            }

        st.success(f"Entity '{entity_name}' saved successfully!")


    # Display all added entities
    st.subheader("📋 Current Entities")
    st.write(st.session_state.entities)


# ---------------------------------------------------------------
# 2️⃣ ADD RELATIONSHIP PAGE
# ---------------------------------------------------------------
elif menu == "🔗 Add Relationships":
    st.header("🔗 Add Relationship")

    with st.form("relation_form"):
        rel_name = st.text_input("Relationship Name")
        entity1 = st.selectbox("Select First Entity", list(st.session_state.entities.keys()))
        entity2 = st.selectbox("Select Second Entity", list(st.session_state.entities.keys()))
        cardinality = st.selectbox("Select Cardinality", ["1:1", "1:N", "N:1", "M:N"])
        rel_attributes = st.text_input("Relationship Attributes (comma separated)")

        submit_rel = st.form_submit_button("Add Relationship")

    if submit_rel:
        st.session_state.relationships.append({
            "name": rel_name,
            "entity1": entity1,
            "entity2": entity2,
            "cardinality": cardinality,
            "attributes": [x.strip() for x in rel_attributes.split(",")] if rel_attributes else []
        })
        st.success(f"Relationship '{rel_name}' added successfully!")

    # Display all relationships
    st.subheader("📋 Current Relationships")
    st.write(st.session_state.relationships)


# ---------------------------------------------------------------
# 3️⃣ VIEW SCHEMA PAGE (Next Phase of Development)
# ---------------------------------------------------------------
elif menu == "ℹ About Project":
    st.header("ℹ About This Tool")
    st.write("""
    This Automated ER-to-Relational Schema Tool converts ER model inputs 
    into normalized relational tables and SQL scripts using Streamlit.
    Developed as a DBMS Mini Project.
    """)

elif menu == "📄 Generate & View Schema / SQL":
    st.title("Generate & View Schema")

    # Show schema first
    if "schema" in st.session_state:
        st.json(st.session_state.schema)

    # Display SQL only on this page
    if "sql_script" in st.session_state:
        st.subheader("🧾 SQL Script")
        st.code(st.session_state.sql_script, language="sql")

        st.download_button(
            label="Download SQL File",
            data=st.session_state.sql_script,
            file_name="generated_schema.sql",
            mime="text/plain"
        )

    # Show current ERD
    st.subheader("Entities")
    st.write(st.session_state.entities)

    st.subheader("Relationships")
    st.write(st.session_state.relationships)

    # Generate Schema button
    if st.button("Generate Relational Schema"):
        success, result = parse_erd(st.session_state.entities, st.session_state.relationships)

        if not success:
            st.error("Errors found during ERD parsing:")
            for err in result:
                st.write("⚠", err)
            st.stop()
        else:
            st.success("ERD Parsing Successful!")

            schema = generate_relational_schema(st.session_state.entities, st.session_state.relationships)
            st.session_state.schema = schema

            st.subheader("📌 Relational Schema Output")
            st.write(schema)

            # Generate SQL NOW (Create variable here)
            st.session_state.sql_script = generate_sql(schema)

# NORMALIZATION CHECK
elif menu == "🧠 Normalization Analysis":
    st.header("🧠 Full Normalization Summary (1NF → 3NF)")

    if "schema" not in st.session_state:
        st.warning("⚠ Please generate the schema first.")
    else:
        norm_result = normalize_schema(st.session_state.schema)

        for table, result in norm_result.items():
            st.markdown(f"#### 🗂 Table: **{table}**")

            if not any(result.values()):
                st.success("✔ No issues — Table satisfies 3NF.")
            else:
                if result["1NF"]:
                    st.error("❌ 1NF Issues:")
                    for issue in result["1NF"]:
                        st.write("•", issue)

                if result["2NF"]:
                    st.warning("⚠ 2NF Issues:")
                    for issue in result["2NF"]:
                        st.write("•", issue)

                if result["3NF"]:
                    st.info("ℹ 3NF Issues:")
                    for issue in result["3NF"]:
                        st.write("•", issue)

                st.write("🔧 **General Fix:** Split the table and create new relations to remove dependencies.")

            st.markdown("---")

elif menu == "📁 Export & Download":
    st.header("📁 Export Options")

    if "sql_script" not in st.session_state:
        st.warning("⚠ Please generate the SQL script first from 'Generate & View Schema / SQL' page.")
    else:
        st.subheader("⬇ Download Generated SQL File")

        st.download_button(
            label="💾 Download SQL File",
            data=st.session_state.sql_script,
            file_name="generated_schema.sql",
            mime="text/plain"
        )

        st.write("---")
        st.info("A PDF export feature for Schema + Normalization Report can be added for documentation purposes!")


elif menu == " ℹ About Project":
    st.header("ℹ About Automated ER-to-Relational Tool")

    st.write("""
    This project converts ER model data into a normalized relational schema 
    and SQL script using rule-based mapping and normalization checks.
    It is built using Python and Streamlit framework.
    """)

    st.write("""
    **Features:**
    - Entity & Relationship Input
    - Relational Schema Generation
    - SQL Code Generation
    - Normalization Check (1NF, 2NF, 3NF)
    - Export Options
    """)

    st.write("""
    **Developed By:** _Your Name_  
    **Course:** DBMS / Mini Project  
    **Technology Stack:** Python, Streamlit  
    """)


# Download button
# Display SQL only if schema exists
if "sql_script" in st.session_state:
    st.subheader("🧾 SQL Script")
    st.code(st.session_state.sql_script, language="sql")

    st.download_button(
        label="💾 Download SQL",
        data=st.session_state.sql_script,
        file_name="generated_schema.sql",
        mime="text/plain"
    )