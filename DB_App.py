import streamlit as st
import pandas as pd
import pyreadstat
import plotly.express as px

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

# Function to generate appropriate visualizations based on the question type
def generate_visualization(data, column_name, question_type, value_labels):
    if question_type == "rating":
        fig = px.bar(data, x=column_name, text=column_name)
    elif question_type == "ranking":
        fig = px.bar(data, x=column_name)
    elif question_type == "categorical":
        if column_name in value_labels:
            # Apply value labels for better interpretation
            labeled_data = data[column_name].map(value_labels[column_name])
            fig = px.pie(labeled_data, names=labeled_data)
        else:
            fig = px.pie(data, names=column_name)
    elif question_type == "numerical":
        fig = px.histogram(data, x=column_name)
    else:
        fig = px.bar(data, x=column_name)
    return fig

# Streamlit app
st.title("Survey Dashboard (SPSS .sav file support)")

# File uploader for .sav files
uploaded_file = st.file_uploader("Upload your survey data (.sav)", type="sav")

if uploaded_file is not None:
    # Read the SPSS file (both data and meta data)
    survey_data, meta = pyreadstat.read_sav(uploaded_file)

    # Display dataset and metadata
    st.write("Data:")
    st.write(survey_data.head())
    
    st.write("Metadata (Variable Labels):")
    st.write(meta.column_labels)
    
    # Create a dictionary to store value labels (mappings) from the metadata
    value_labels = meta.variable_value_labels

    # Dropdown to select a question (columns in dataset)
    question = st.selectbox("Select Question", survey_data.columns)

    # Automatically detect question type
    question_type = detect_question_type(survey_data[question], value_labels)

    # Display detected question type
    st.write(f"Detected Question Type: {question_type.capitalize()}")

    # Generate and display the appropriate visualization
    fig = generate_visualization(survey_data, question, question_type, value_labels)
    st.plotly_chart(fig)

    # Show some basic statistics about the selected question
    st.subheader(f"Basic Statistics for {question}")
    if pd.api.types.is_numeric_dtype(survey_data[question]):
        st.write(survey_data[question].describe())
    else:
        st.write(survey_data[question].value_counts())
