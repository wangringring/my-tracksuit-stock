import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Tracksuit Factory System", layout="wide")
st.title("👕 ระบบจัดการสต็อกเสื้อวอร์ม (เชื่อมต่อ Google Sheets)")

# 1. เชื่อมต่อกับ Google Sheets
try:
    conn = st.connection("gsheets", type=GSheetsConnection, spreadsheet="https://docs.google.com/spreadsheets/d/1dmzmAN_HG5D38rtvmKDeW0bIqyQ7l6kkQ7woCN6UTBA/edit?usp=sharing")
    
    # ดึงข้อมูลจากแผ่นงานต่างๆ
    df_stock = conn.read(worksheet="Stock", ttl=0)
    df_tailors = conn.read(worksheet="Tailors", ttl=0)
    
    # แปลงข้อมูลเป็น Dictionary เพื่อให้โปรแกรมคำนวณง่าย
    stock_dict = dict(zip(df_stock['Item'], df_stock['Quantity']))
    tailors_dict = df_tailors.set_index('Tailor_Name').to_dict(orient='index')
except Exception as e:
    st.error("กำลังรอการเชื่อมต่อกับ Google Sheets... กรุณาตั้งค่า Secret ใน Streamlit Cloud")
    st.stop()

# ฟังก์ชันอัปเดตข้อมูลกลับไปยัง Google Sheets และบันทึกประวัติ
def save_data(dept_name, action_text):
    # เตรียมข้อมูลสต็อกส่งกลับ
    new_stock_df = pd.DataFrame(list(stock_dict.items()), columns=['Item', 'Quantity'])
    conn.update(worksheet="Stock", data=new_stock_df)
    
    # เตรียมข้อมูลช่างส่งกลับ
    new_tailors_df = pd.DataFrame.from_dict(tailors_dict, orient='index').reset_index()
    new_tailors_df.rename(columns={'index': 'Tailor_Name'}, inplace=True)
    conn.update(worksheet="Tailors", data=new_tailors_df)
    
    # บันทึกประวัติการทำงาน (Logs)
    try:
        df_logs = conn.read(worksheet="Logs", ttl=0)
    except:
        df_logs = pd.DataFrame(columns=['Timestamp', 'Department', 'Action'])
        
    new_log = pd.DataFrame([{
        'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'Department': dept_name,
        'Action': action_text
    }])
    df_logs = pd.concat([df_logs, new_log], ignore_index=True)
    conn.update(worksheet="Logs", data=df_logs)
    
    st.success("บันทึกข้อมูลลง Google Sheets สำเร็จ!")
    st.rerun()

# 2. ส่วนแสดงสถานะปัจจุบัน (Dashboard)
st.subheader("📊 สถานะสต็อกปัจจุบัน (ดึงข้อมูลเรียลไทม์)")
col1, col2, col3, col4 = st.columns(4)
col1.metric("🧵 ม้วนผ้าคงเหลือ", f"{stock_dict.get('fabric_rolls', 0)} ม้วน")
col2.metric("✂️ ชิ้นผ้าที่ตัดแล้ว", f"{stock_dict.get('cut_pieces', 0)} ชิ้น")
col3.metric("📦 รอ QC & แพ็ค", f"{stock_dict.get('ready_to_pack', 0)} ตัว")
col4.metric("🛍️ สินค้าพร้อมขาย", f"{stock_dict.get('finished_goods', 0)} ตัว")

st.markdown("---")

# 3. เมนูการทำงานแบ่งตามแผนก
tab1, tab2, tab3 = st.tabs(["1. แผนกตัดผ้า", "2. แผนกเย็บ (จ่ายงาน 4 ช่าง)", "3. แผนกแพ็ค & คลังสินค้า"])

# --- TAB 1: แผนกตัดผ้า ---
with tab1:
    st.header("🧵 การจัดการวัตถุดิบและงานตัด")
    col_input1, col_input2 = st.columns(2)
    with col_input1:
        add_rolls = st.number_input("ซื้อผ้าเข้าคลัง (ม้วน)", min_value=0, step=1)
        if st.button("บันทึกรับผ้าเข้า"):
            if add_rolls > 0:
                stock_dict["fabric_rolls"] += add_rolls
                save_data("แผนกตัดผ้า", f"ซื้อผ้าเข้าคลังเพิ่ม {add_rolls} ม้วน")
            
    with col_input2:
        max_rolls = int(stock_dict.get('fabric_rolls', 0))
        use_rolls = st.number_input("นำผ้าไปตัด (1 ม้วน = 20 ชิ้น)", min_value=0, max_value=max_rolls, step=1)
        if st.button("ยืนยันการตัดผ้า"):
            if use_rolls > 0:
                stock_dict["fabric_rolls"] -= use_rolls
                stock_dict["cut_pieces"] += (use_rolls * 20)
                save_data("แผนกตัดผ้า", f"เบิกผ้าไปตัด {use_rolls} ม้วน (ได้ชิ้นงาน {use_rolls * 20} ชิ้น)")

# --- TAB 2: แผนกเย็บ ---
with tab2:
    st.header("🪡 การจ่ายงานและรับงานช่างเย็บ")
    st.subheader("📋 ตารางสถานะงานช่าง")
    for name, info in tailors_dict.items():
        st.write(f"**{name}**: กำลังเย็บอยู่ `{info['Assigned']}` ตัว | เย็บเสร็จสะสมทั้งหมด `{info['Completed_Total']}` ตัว")
        
    st.markdown("---")
    col_sew1, col_sew2 = st.columns(2)
    with col_sew1:
        st.subheader("➕ จ่ายงานให้ช่าง")
        tailor_select = st.selectbox("เลือกช่างเย็บ", list(tailors_dict.keys()), key="sel_assign")
        max_cut = int(stock_dict.get('cut_pieces', 0))
        assign_amount = st.number_input("จำนวนชิ้นผ้าที่จ่ายให้เย็บ", min_value=0, max_value=max_cut, step=1)
        if st.button("ยืนยันจ่ายงาน"):
            if assign_amount > 0:
                stock_dict["cut_pieces"] -= assign_amount
                tailors_dict[tailor_select]["Assigned"] += assign_amount
                save_data("แผนกเย็บ", f"จ่ายงานให้ {tailor_select} จำนวน {assign_amount} ชิ้น")

    with col_sew2:
        st.subheader("✅ รับงานจากช่าง (เย็บเสร็จ)")
        tailor_select_recv = st.selectbox("เลือกช่างเย็บ", list(tailors_dict.keys()), key="sel_recv")
        max_recv = int(tailors_dict[tailor_select_recv]["Assigned"])
        recv_amount = st.number_input("จำนวนเสื้อที่เย็บเสร็จมาส่ง", min_value=0, max_value=max_recv, step=1)
        if st.button("ยืนยันรับเสื้อ"):
            if recv_amount > 0:
                tailors_dict[tailor_select_recv]["Assigned"] -= recv_amount
                tailors_dict[tailor_select_recv]["Completed_Total"] += recv_amount
                stock_dict["ready_to_pack"] += recv_amount
                save_data("แผนกเย็บ", f"รับเสื้อเย็บเสร็จจาก {tailor_select_recv} จำนวน {recv_amount} ตัว")

# --- TAB 3: แผนกแพ็ค & คลังสินค้า ---
with tab3:
    st.header("📦 งานแพ็คและตรวจนับสินค้าพร้อมขาย")
    max_pack = int(stock_dict.get('ready_to_pack', 0))
    pack_amount = st.number_input("จำนวนเสื้อวอร์มที่แพ็คเสร็จเรียบร้อย", min_value=0, max_value=max_pack, step=1)
    if st.button("บันทึกเข้าสต็อกพร้อมขาย"):
        if pack_amount > 0:
            stock_dict["ready_to_pack"] -= pack_amount
            stock_dict["finished_goods"] += pack_amount
            save_data("แผนกแพ็คสินค้า", f"แพ็คเสื้อวอร์มเสร็จเข้าหน้าร้าน {pack_amount} ตัว")
