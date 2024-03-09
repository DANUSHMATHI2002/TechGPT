

import streamlit as st
from streamlit_option_menu import option_menu
from pandasai import PandasAI
from pandasai.llm.openai import OpenAI
from dotenv import load_dotenv
import os
import pandas as pd

load_dotenv()

openai_api_key = ""
llm = OpenAI(api_token=openai_api_key)

def chat_with_csv(df,prompt):
    pandas_ai = PandasAI(llm)
    result = pandas_ai.run(df, prompt=prompt)
    return result

st.set_page_config(layout='wide')

# Create a navigation bar
with st.sidebar:
    selected = option_menu("Main Menu", ["Home", 'Techgpt', 'Help'], 
        icons=['house', 'terminal', 'question-circle'], menu_icon="cast", default_index=0)

if selected == "Home":
    st.title("Welcome to TechGPT")
    st.write("Upload your CSV file and chat with it")

elif selected == "Techgpt":
    st.title("Techgpt")
    st.write("This is the Techgpt section")

    input_csv = st.file_uploader("Upload your CSV file", type=['csv'])

    if input_csv is not None:

        col1, col2 = st.columns([1,1])

        with col1:
            st.info("CSV Uploaded Successfully")
            data = pd.read_csv(input_csv)
            st.dataframe(data, use_container_width=True)

        with col2:

            st.info("Chat Below")
            
            input_text = st.text_area("Enter your query")

            if input_text is not None:
                if st.button("Chat with CSV"):
                    st.info("Your Query: "+input_text)
                    result = chat_with_csv(data, input_text)
                    st.success(result)

elif selected == "Help":
    st.title("Help")
    st.write("This is the help section")
    st.write("Upload your CSV file and chat with it")
    st.write("You can ask questions related to the data in the CSV file")
    st.write("The TechGPT will answer your questions based on the data in the CSV file")



