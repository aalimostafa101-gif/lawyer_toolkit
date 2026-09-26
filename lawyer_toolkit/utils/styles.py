import streamlit as st

def apply_rtl_styles():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&family=Tajawal:wght@400;700&display=swap');
        
        * {
            font-family: 'Tajawal', 'Cairo', sans-serif !important;
        }

        /* Full RTL */
        body, .stApp, .stMainBlockContainer, .stSidebar, [data-testid="stSidebarNav"] {
            direction: rtl;
            text-align: right;
        }

        /* Theming */
        .stButton>button {
            background-color: #C9A84C !important;
            color: white !important;
            border-radius: 4px;
            border: none;
        }
        
        .stButton>button:hover {
            background-color: #b59540 !important;
            color: white !important;
        }

        h1, h2, h3, h4, h5, h6 {
            color: #1B2A4A !important;
        }

        /* Sensitive clause cards with colored left border */
        .sensitive-card {
            background-color: #ffffff;
            border-right: 4px solid #C9A84C; /* Changed to border-right for RTL */
            padding: 15px;
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 10px;
        }

        /* Dataframes and Tables RTL */
        .stDataFrame, .stTable {
            direction: rtl;
        }
        table {
            text-align: right;
        }
        th, td {
            text-align: right !important;
        }
        
        /* White cards for general usage */
        .card {
            background-color: #ffffff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        </style>
    """, unsafe_allow_html=True)
