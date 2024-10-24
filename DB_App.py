import streamlit as st
import pandas as pd
import pyreadstat
import plotly.express as px
import tempfile

# Function to detect if a column is a rating question
def detect_question_type(column):
    if pd.api.types.is_numeric_dtype(column):
        return "rating"
    return "other"

# Function to generate a stacked bar chart for ratings
def generate_stacked_bar_chart(data, columns, value_labels):
    # Melt the data for all brand columns into a long format
    melted_data = data[columns].melt(var_name="Brand", value_name="Rating")
    
    # If value_labels exist, map them to the data
    if value_labels:
        for col in columns:
            melted_data['Rating'] = melted_data['Rating'].map(value_labels.get(col, {}))

    # Create a stacked bar chart showing proportions of different ratings for each brand
    fig = px.histogram(melted_data, x="Brand", color="Rating", barmode="relative",
                       histnorm='percent', text_auto=True)
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
    st.write("Data Preview:")
    st.write(survey_data.head())
    
    # Create a dictionary to map questions to their variable names
    # We'll map main question texts (without sub-question brand labels) to variable names
    question_map = {}
    for i, col_name in enumerate(meta.column_names):
        # Extract the base question text (ignoring sub-questions for brands)
        base_question = col_name.split("r")[0]  # e.g., Q_ABA
        if base_question not in question_map:
            question_map[base_question] = meta.column_labels[i]

    # Invert the question map to show labels as options in dropdown
    label_to_base = {v: k for k, v in question_map.items()}

    # Dropdown to select a main question (human-readable)
    question_label = st.selectbox("Select Question", list(label_to_base.keys()))

    # Get the base column name for the selected question (e.g., "Q_ABA")
    selected_base_column = label_to_base[question_label]

    # Find all related sub-questions (brand columns)
    related_columns = [col for col in survey_data.columns if col.startswith(selected_base_column)]

    # Detect question type based on the first brand column (assume rating)
    question_type = detect_question_type(survey_data[related_columns[0]])

    if question_type == "rating":
        # Create a stacked bar chart for rating questions
        st.write(f"Detected Question Type: Rating (Brands: {', '.join(related_columns)})")

        # Generate and display the stacked bar chart
        fig = generate_stacked_bar_chart(survey_data, related_columns, meta.variable_value_labels)
        st.plotly_chart(fig)
    
    # Show basic statistics for the selected question
    st.subheader(f"Basic Statistics for {question_label} (All Brands)")
    st.write(survey_data[related_columns].describe())
