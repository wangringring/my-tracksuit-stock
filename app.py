import streamlit as st

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Tracksuit Factory Inventory", layout="wide")
st.title("👕 ระบบจัดการสต็อกและผลิตเสื้อวอร์ม")

# 1. จำลองฐานข้อมูลภายในระบบ (In-Memory Database)
if "db" not in st.session_state:
    st.session_state.db = {
        "fabric_rolls": 10,       # ม้วนผ้าคงเหลือ
        "cut_pieces": 50,         # ผ้าที่ตัดแล้ว รอจ่ายงาน
        "ready_to_pack": 20,      # เสื้อที่เย็บเสร็จ รอแพ็ค
        "finished_goods": 100,    # เสื้อวอร์มพร้อมขาย
        # สต็อกงานของช่างเย็บ 4 คน
        "tailors": {
            "ช่างแดง": {"assigned": 0, "completed_total": 0},
            "ช่างดำ": {"assigned": 0, "completed_total": 0},
            "ช่างขาว": {"assigned": 0, "completed_total": 0},
            "ช่างเขียว": {"assigned": 0, "completed_total": 0}
        }
    }

db = st.session_state.db

# 2. ส่วนแสดงสถานะปัจจุบัน (Dashboard)
st.subheader("📊 สถานะสต็อกปัจจุบัน")
col1, col2, col3, col4 = st.columns(4)
col1.metric("🧵 ม้วนผ้าคงเหลือ", f"{db['fabric_rolls']} ม้วน")
col2.metric("✂️ ชิ้นผ้าที่ตัดแล้ว", f"{db['cut_pieces']} ชิ้น")
col3.metric("📦 รอ QC & แพ็ค", f"{db['ready_to_pack']} ตัว")
col4.metric("🛍️ สินค้าพร้อมขาย", f"{db['finished_goods']} ตัว")

st.markdown("---")

# 3. เมนูการทำงานแบ่งตามแผนก
tab1, tab2, tab3 = st.tabs(["1. แผนกตัดผ้า", "2. แผนกเย็บ (จ่ายงาน 4 ช่าง)", "3. แผนกแพ็ค & คลังสินค้า"])

# --- TAB 1: แผนกตัดผ้า ---
with tab1:
    st.header("🧵 การจัดการวัตถุดิบและงานตัด")
    col_input1, col_input2 = st.columns(2)
    with col_input1:
        add_rolls = st.number_input("ซื้อผ้าเข้าคลัง (ม้วน)", min_value=0, step=1, key="add_rolls")
        if st.button("บันทึกรับผ้าเข้า"):
            db["fabric_rolls"] += add_rolls
            st.success(f"เพิ่มผ้าเข้าคลังสำเร็จ! ตอนนี้มีผ้า {db['fabric_rolls']} ม้วน")
            st.rerun()
            
    with col_input2:
        use_rolls = st.number_input("นำผ้าไปตัด (1 ม้วน = 20 ชิ้น)", min_value=0, max_value=db["fabric_rolls"], step=1, key="use_rolls")
        if st.button("ยืนยันการตัดผ้า"):
            if use_rolls > 0:
                db["fabric_rolls"] -= use_rolls
                db["cut_pieces"] += (use_rolls * 20)
                st.success(f"ตัดผ้าสำเร็จ! ได้ชิ้นงานเพิ่มขึ้น {use_rolls * 20} ชิ้น")
                st.rerun()

# --- TAB 2: แผนกเย็บ (แยกรายคน) ---
with tab2:
    st.header("🪡 การจ่ายงานและรับงานช่างเย็บ")
    
    # แสดงตารางงานปัจจุบันของช่างทุกคน
    st.subheader("📋 ตารางสถานะงานช่าง")
    for name, info in db["tailors"].items():
        st.write(f"**{name}**: กำลังเย็บอยู่ `{info['assigned']}` ตัว | เย็บเสร็จสะสมทั้งหมด `{info['completed_total']}` ตัว")
        
    st.markdown("---")
    
    col_sew1, col_sew2 = st.columns(2)
    with col_sew1:
        st.subheader("➕ จ่ายงานให้ช่าง")
        tailor_select = st.selectbox("เลือกช่างเย็บ", list(db["tailors"].keys()), key="select_tailor_assign")
        assign_amount = st.number_input("จำนวนชิ้นผ้าที่จ่ายให้เย็บ", min_value=0, max_value=db["cut_pieces"], step=1, key="assign_amount")
        if st.button("ยืนยันจ่ายงาน"):
            if assign_amount > 0:
                db["cut_pieces"] -= assign_amount
                db["tailors"][tailor_select]["assigned"] += assign_amount
                st.success(f"จ่ายงานให้ {tailor_select} จำนวน {assign_amount} ชิ้น เรียบร้อย")
                st.rerun()

    with col_sew2:
        st.subheader("✅ รับงานจากช่าง (เย็บเสร็จ)")
        tailor_select_recv = st.selectbox("เลือกช่างเย็บ", list(db["tailors"].keys()), key="select_tailor_recv")
        max_recv = db["tailors"][tailor_select_recv]["assigned"]
        recv_amount = st.number_input("จำนวนเสื้อที่เย็บเสร็จมาส่ง", min_value=0, max_value=max_recv, step=1, key="recv_amount")
        if st.button("ยืนยันรับเสื้อ"):
            if recv_amount > 0:
                db["tailors"][tailor_select_recv]["assigned"] -= recv_amount
                db["tailors"][tailor_select_recv]["completed_total"] += recv_amount
                db["ready_to_pack"] += recv_amount
                st.success(f"รับเสื้อจาก {tailor_select_recv} จำนวน {recv_amount} ตัว เข้ารอรอบแพ็ค")
                st.rerun()

# --- TAB 3: แผนกแพ็ค & คลังสินค้า ---
with tab3:
    st.header("📦 งานแพ็คและตรวจนับสินค้าพร้อมขาย")
    pack_amount = st.number_input("จำนวนเสื้อวอร์มที่แพ็คเสร็จเรียบร้อย", min_value=0, max_value=db["ready_to_pack"], step=1, key="pack_amount")
    if st.button("บันทึกเข้าสต็อกพร้อมขาย"):
        if pack_amount > 0:
            db["ready_to_pack"] -= pack_amount
            db["finished_goods"] += pack_amount
            st.success(f"นำเสื้อวอร์มเข้าสต็อกพร้อมขายเพิ่ม {pack_amount} ตัว เรียบร้อยแล้ว! 🎉")
            st.rerun()
