import streamlit as st
import sys
import os
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.styles import apply_rtl_styles
from db.database import (
    get_all_clients, get_client_by_id, add_client, update_client, delete_client,
    get_cases, add_case, update_case, delete_case, get_client_case_count
)

st.set_page_config(page_title="إدارة القضايا والعملاء", page_icon="📊", layout="wide")
apply_rtl_styles()

st.title("📊 إدارة القضايا والعملاء")

tab_cases, tab_clients = st.tabs(["📁 القضايا", "👤 العملاء"])

# --- TAB 1: القضايا ---
with tab_cases:
    st.subheader("فلترة القضايا")
    col1, col2 = st.columns(2)
    with col1:
        case_type_filter = st.selectbox("نوع القضية", ["الكل", "مدني", "جنائي", "عقاري", "تجاري/شركات"], key="filter_type")
    with col2:
        status_filter = st.selectbox("حالة القضية", ["الكل", "جارية", "متوقفة", "مُغلقة"], key="filter_status")
    
    # Apply filters
    filter_type = case_type_filter if case_type_filter != "الكل" else None
    filter_status = status_filter if status_filter != "الكل" else None
    
    cases_list = get_cases(case_type=filter_type, status=filter_status)
    clients_list = get_all_clients()
    client_map = {c['id']: c['name'] for c in clients_list}
    
    if cases_list:
        # Add client name for display
        display_data = []
        for c in cases_list:
            display_data.append({
                "رقم القضية": c.get('case_number', ''),
                "العميل": client_map.get(c.get('client_id'), '—'),
                "النوع": c.get('case_type', ''),
                "الحالة": c.get('status', ''),
                "آخر جلسة": c.get('last_session', ''),
                "الجلسة القادمة": c.get('next_session', ''),
                "ملاحظات": c.get('notes', ''),
            })
        df_cases = pd.DataFrame(display_data)
        st.dataframe(df_cases, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        for case in cases_list:
            c1, c2, c3 = st.columns([6, 1, 1])
            c1.write(f"📁 قضية **{case.get('case_number', '—')}** — {case.get('case_type', '')} ({case.get('status', '')})")
            if c2.button("✏️", key=f"edit_case_{case['id']}"):
                st.session_state['edit_case_id'] = case['id']
            if c3.button("🗑️", key=f"del_case_{case['id']}"):
                st.session_state['delete_case_id'] = case['id']
        
        # Handle delete
        if 'delete_case_id' in st.session_state:
            st.warning("⚠️ هل أنت متأكد من حذف هذه القضية؟")
            d1, d2 = st.columns(2)
            if d1.button("✅ تأكيد الحذف", key="confirm_del_case"):
                delete_case(st.session_state['delete_case_id'])
                del st.session_state['delete_case_id']
                st.success("تم حذف القضية بنجاح!")
                st.rerun()
            if d2.button("❌ إلغاء", key="cancel_del_case"):
                del st.session_state['delete_case_id']
                st.rerun()
        
        # Handle edit
        if 'edit_case_id' in st.session_state:
            edit_id = st.session_state['edit_case_id']
            edit_case = next((c for c in cases_list if c['id'] == edit_id), None)
            if edit_case:
                st.markdown("---")
                st.subheader(f"✏️ تعديل القضية: {edit_case.get('case_number', '')}")
                with st.form("edit_case_form"):
                    e_number = st.text_input("رقم القضية", value=edit_case.get('case_number', ''))
                    e_type = st.selectbox("النوع", ["مدني", "جنائي", "عقاري", "تجاري/شركات"],
                                          index=["مدني", "جنائي", "عقاري", "تجاري/شركات"].index(edit_case.get('case_type', 'مدني')) if edit_case.get('case_type') in ["مدني", "جنائي", "عقاري", "تجاري/شركات"] else 0)
                    e_status = st.selectbox("الحالة", ["جارية", "متوقفة", "مُغلقة"],
                                            index=["جارية", "متوقفة", "مُغلقة"].index(edit_case.get('status', 'جارية')) if edit_case.get('status') in ["جارية", "متوقفة", "مُغلقة"] else 0)
                    e_notes = st.text_area("ملاحظات", value=edit_case.get('notes', '') or '')
                    if st.form_submit_button("💾 حفظ التعديلات"):
                        update_case(edit_id, case_number=e_number, case_type=e_type, status=e_status,
                                    last_session=edit_case.get('last_session'), next_session=edit_case.get('next_session'), notes=e_notes)
                        del st.session_state['edit_case_id']
                        st.success("تم التعديل بنجاح!")
                        st.rerun()
    else:
        st.info("لا توجد قضايا مطابقة للفلتر. أضف قضية جديدة من الأسفل.")
    
    # Add new case
    with st.expander("➕ إضافة قضية جديدة"):
        if not clients_list:
            st.warning("يجب إضافة عميل أولاً قبل إضافة قضية. انتقل لتبويب العملاء.")
        else:
            with st.form("add_case_form"):
                new_number = st.text_input("رقم القضية")
                new_client = st.selectbox("العميل", options=[c['id'] for c in clients_list],
                                          format_func=lambda x: client_map.get(x, ''))
                new_type = st.selectbox("نوع القضية", ["مدني", "جنائي", "عقاري", "تجاري/شركات"])
                new_status = st.selectbox("الحالة", ["جارية", "متوقفة", "مُغلقة"])
                new_last = st.date_input("تاريخ آخر جلسة")
                new_next = st.date_input("تاريخ الجلسة القادمة")
                new_notes = st.text_area("ملاحظات")
                
                if st.form_submit_button("💾 حفظ القضية"):
                    if not new_number:
                        st.error("يرجى إدخال رقم القضية.")
                    else:
                        add_case(new_client, case_number=new_number, case_type=new_type, status=new_status,
                                 last_session=str(new_last), next_session=str(new_next), notes=new_notes)
                        st.success("تم إضافة القضية بنجاح! ✅")
                        st.rerun()

# --- TAB 2: العملاء ---
with tab_clients:
    clients_with_count = get_client_case_count()
    clients_list = get_all_clients()
    
    if clients_list:
        display_clients = []
        count_map = {c['id']: c.get('case_count', 0) for c in clients_with_count}
        for cl in clients_list:
            display_clients.append({
                "الاسم": cl.get('name', ''),
                "الهاتف": cl.get('phone', ''),
                "البريد": cl.get('email', ''),
                "عدد القضايا": count_map.get(cl['id'], 0),
                "ملاحظات": cl.get('notes', ''),
            })
        df_clients = pd.DataFrame(display_clients)
        st.dataframe(df_clients, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        for client in clients_list:
            c1, c2, c3 = st.columns([6, 1, 1])
            cnt = count_map.get(client['id'], 0)
            c1.write(f"👤 **{client.get('name', '')}** — {client.get('phone', '')} ({cnt} قضايا)")
            if c2.button("✏️", key=f"edit_cl_{client['id']}"):
                st.session_state['edit_client_id'] = client['id']
            if c3.button("🗑️", key=f"del_cl_{client['id']}"):
                st.session_state['delete_client_id'] = client['id']
        
        # Handle delete client
        if 'delete_client_id' in st.session_state:
            del_id = st.session_state['delete_client_id']
            cnt = count_map.get(del_id, 0)
            if cnt > 0:
                st.warning(f"⚠️ هذا العميل مرتبط بـ {cnt} قضايا. حذفه سيحذف جميع قضاياه.")
            else:
                st.warning("⚠️ هل أنت متأكد من حذف هذا العميل؟")
            d1, d2 = st.columns(2)
            if d1.button("✅ تأكيد الحذف", key="confirm_del_cl"):
                delete_client(del_id)
                del st.session_state['delete_client_id']
                st.success("تم حذف العميل بنجاح!")
                st.rerun()
            if d2.button("❌ إلغاء", key="cancel_del_cl"):
                del st.session_state['delete_client_id']
                st.rerun()
        
        # Handle edit client
        if 'edit_client_id' in st.session_state:
            edit_cl = get_client_by_id(st.session_state['edit_client_id'])
            if edit_cl:
                st.markdown("---")
                st.subheader(f"✏️ تعديل العميل: {edit_cl.get('name', '')}")
                with st.form("edit_client_form"):
                    e_name = st.text_input("الاسم", value=edit_cl.get('name', ''))
                    e_phone = st.text_input("الهاتف", value=edit_cl.get('phone', '') or '')
                    e_email = st.text_input("البريد", value=edit_cl.get('email', '') or '')
                    e_notes = st.text_area("ملاحظات", value=edit_cl.get('notes', '') or '')
                    if st.form_submit_button("💾 حفظ التعديلات"):
                        update_client(st.session_state['edit_client_id'], name=e_name, phone=e_phone, email=e_email, notes=e_notes)
                        del st.session_state['edit_client_id']
                        st.success("تم التعديل بنجاح!")
                        st.rerun()
    else:
        st.info("لا يوجد عملاء حالياً. أضف عميلك الأول من الأسفل.")
    
    # Add new client
    with st.expander("➕ إضافة عميل جديد"):
        with st.form("add_client_form"):
            new_name = st.text_input("اسم العميل")
            new_phone = st.text_input("رقم الهاتف")
            new_email = st.text_input("البريد الإلكتروني")
            new_notes = st.text_area("ملاحظات")
            
            if st.form_submit_button("💾 حفظ العميل"):
                if not new_name:
                    st.error("يرجى إدخال اسم العميل.")
                else:
                    add_client(new_name, phone=new_phone, email=new_email, notes=new_notes)
                    st.success("تم إضافة العميل بنجاح! ✅")
                    st.rerun()
