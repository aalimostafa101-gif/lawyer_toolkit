import streamlit as st
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.database import init_db
from utils.styles import apply_rtl_styles

st.set_page_config(
    page_title="أدوات المكتب الذكية",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

init_db()
apply_rtl_styles()

# Landing page content
st.title("⚖️ أدوات المكتب الذكية")
st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    st.markdown('''
    ### 🔍 تحليل العقود
    ارفع عقدًا بصيغة PDF أو Word أو الصق نصه مباشرةً،
    واحصل على ملخص فوري وقائمة بالبنود الحساسة.
    ''')
    # Link to contract analysis page

with col2:
    st.markdown('''
    ### 📊 إدارة القضايا والعملاء
    أضف وتابع القضايا والعملاء في مكان واحد
    مع إمكانية الفلترة والتعديل.
    ''')

st.markdown('---')
st.caption('نسخة تجريبية — MVP | جميع البيانات محفوظة محليًا')
