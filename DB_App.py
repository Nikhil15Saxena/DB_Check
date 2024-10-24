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
        # Create a dataframe for all brand columns
        melted_data = data[columns].melt(var_name="Brand", value_name="Rating")
        fig = px.bar(melted_data, x="Brand", y="Rating", text="Rating")
    elif question_type == "categorical":
        # Pie chart showing distribution for each brand
        fig = px.pie(data, names=columns[0])  # For simplicity, just showing one brand pie chart
    else:
        # Fallback to bar chart for other types of data
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
    
    # Display questions (variable labels from metadata) in dropdown for selection
    question_map = {meta.column_labels[i]: meta.column_names[i] for i in range(len(meta.column_names))}
    question_label = st.selectbox("Select Question", list(question_map.keys()))

    # Get the associated column(s) for the selected question
    selected_column = question_map[question_label]
    
    # Check if there are multiple columns for this question (e.g., for different brands)
    # This assumes that brands have similar names or patterns in the column names, e.g., "Brand1_Q1", "Brand2_Q1"
    related_columns = [col for col in survey_data.columns if selected_column in col]
    
    if len(related_columns) > 1:
        st.write(f"Detected multiple brands for the question: {', '.join(related_columns)}")
    else:
        related_columns = [selected_column]  # Just the one column
    
    # Automatically detect question type based on first brand column
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
