import streamlit as st
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()

APP_TITLE=os.getenv("APP_TITLE")

st.markdown('# '+ APP_TITLE)