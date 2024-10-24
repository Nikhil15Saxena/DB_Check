import streamlit as st
import pandas as pd
import pyreadstat
import plotly.express as px
import tempfile

# Function to detect question type based on column data (simplified for ratings)
def detect_question_type(column):
    if pd.api.types.is_numeric_dtype(column):
        return "rating"
    return "other"

# Function to prepare the data for a stacked bar chart
def prepare_stacked_bar_data(data, columns, value_labels):
    # Melt the data for all brand columns into a long format
    melted_data = data[columns].melt(var_name="Brand", value_name="Rating")
    
    # Map the rating scale labels (if they exist in the metadata)
    if value_labels:
        for col in columns:
            melted_data['Rating'] = melted_data['Rating'].map(value_labels.get(col, {}))
    
    # Calculate the percentage distribution for each brand and rating
    rating_counts = melted_data.groupby(['Brand', 'Rating']).size().reset_index(name='Count')
    total_counts = melted_data.groupby('Brand')['Rating'].count().reset_index(name='Total')
    rating_counts = pd.merge(rating_counts, total_counts, on='Brand')
    rating_counts['Percentage'] = (rating_counts['Count'] / rating_counts['Total']) * 100
    
    return rating_counts

# Function to generate a stacked bar chart with percentages
def generate_stacked_bar_chart(data, value_labels):
    fig = px.bar(
        data, 
        x="Brand", 
        y="Percentage", 
        color="Rating", 
        barmode="stack", 
        text="Percentage",  # Display percentage as data labels
        color_discrete_sequence=px.colors.qualitative.Set1
    )
    fig.update_layout(
        yaxis=dict(title="Percentage", tickformat=".0%", range=[0, 100]),  # Y-axis range fixed to 0-100%
        xaxis=dict(title="Brands"),
        title="Proportion of Rating Scales for Each Brand",
        uniformtext_minsize=8,  # Uniform text size for labels
        uniformtext_mode="hide",  # Hide text that doesn't fit
    )
    fig.update_traces(texttemplate='%{text:.2f}%', textposition='inside')  # Format data labels as percentages
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
        st.write(f"Detected Question Type: Rating")

        # Prepare data for stacked bar chart
        rating_data = prepare_stacked_bar_data(survey_data, related_columns, meta.variable_value_labels)
        
        # Generate and display the stacked bar chart
        fig = generate_stacked_bar_chart(rating_data, meta.variable_value_labels)
        st.plotly_chart(fig)
    
    # Show basic statistics for the selected question
    st.subheader(f"Basic Statistics for {question_label} (All Brands)")
    st.write(survey_data[related_columns].describe())
