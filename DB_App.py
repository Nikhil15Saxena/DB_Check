import streamlit as st
import pandas as pd
import pyreadstat
import plotly.express as px
import tempfile

# Function to detect question type based on column data
def detect_question_type(column, value_labels):
    if pd.api.types.is_numeric_dtype(column):
        if column.nunique() <= 5:  # Assuming Likert scale rating
            return "rating"
        else:
            return "numerical"
    elif column.nunique() <= 10 or column.name in value_labels:  # Categorical or labeled data
        return "categorical"
    else:
        return "other"

# Function to generate visualizations for multiple brands under a question
def generate_brand_visualization(data, columns, question_type, value_labels):
    if question_type == "rating" or question_type == "numerical":
        # Combine data from multiple brands (sub-questions) into a single dataframe
        melted_data = data[columns].melt(var_name="Brand", value_name="Rating")
        fig = px.bar(melted_data, x="Brand", y="Rating", text="Rating")
    elif question_type == "categorical":
        # For categorical, we will show a pie chart for the first brand (for simplicity)
        fig = px.pie(data, names=columns[0])
    else:
        fig = px.bar(data, x=columns[0])
    return fig

# Streamlit app
st.title("Survey Dashboard with Brand Visualization (SPSS .sav support)")

# File uploader for .sav files
uploaded_file = st.file_uploader("Upload your survey data (.sav)", type="sav")

if uploaded_file is not None:
    # Create a temporary file to store the uploaded .sav file
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_file_path = tmp_file.name

    # Read the SPSS file (both data and meta data)
    survey_data, meta = pyreadstat.read_sav(tmp_file_path)

    # Display dataset and metadata
    st.write("Data:")
    st.write(survey_data.head())
    
    st.write("Metadata (Variable Labels):")
    st.write(meta.column_labels)
    
    # Create a dictionary to store value labels (mappings) from the metadata
    value_labels = meta.variable_value_labels
    
    # Show human-readable question labels in the dropdown
    question_map = {meta.column_labels[i]: meta.column_names[i] for i in range(len(meta.column_names))}
    question_label = st.selectbox("Select Question", list(question_map.keys()))

    # Get the base column name for the selected question (e.g., "Q_ABA")
    selected_base_column = question_map[question_label].split('r')[0]

    # Find all related columns (e.g., Q_ABAp1r1, Q_ABAp1r2, etc.)
    related_columns = [col for col in survey_data.columns if col.startswith(selected_base_column)]

    # Automatically detect question type based on the first related column
    question_type = detect_question_type(survey_data[related_columns[0]], value_labels)

    # Display detected question type
    st.write(f"Detected Question Type: {question_type.capitalize()}")

    # Generate and display the appropriate visualization for all brands under this question
    fig = generate_brand_visualization(survey_data, related_columns, question_type, value_labels)
    st.plotly_chart(fig)

    # Show some basic statistics about the selected question
    st.subheader(f"Basic Statistics for {question_label} (All Brands)")
    if pd.api.types.is_numeric_dtype(survey_data[related_columns[0]]):
        st.write(survey_data[related_columns].describe())
    else:
        st.write(survey_data[related_columns].apply(lambda col: col.value_counts()))
