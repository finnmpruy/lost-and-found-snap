import io
import time
import streamlit as st
import pandas as pd
from PIL import Image
import extra_streamlit_components as stx
from streamlit_cropper import st_cropper
from datetime import datetime, timedelta
from database import (
    init_db,
    authenticate_user,
    get_user_by_id,
    register_user,
    insert_laporan,
    get_all_laporan,
    update_status_barang,
)
from module.multimedia_engine import (
    crop_center_square,
    process_uploaded_image,
    generate_placeholder_card,
    generate_sha256_hash,
    save_image_bytes,
    generate_digital_poster,
)

st.set_page_config(
    page_title="Lost & Found Snap | Telkom University",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

init_db()

# ==========================================
# GLOBAL MODERN UI/UX STYLING (TEL-U THEME)
# ==========================================
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        color: #0F172A;
    }

    #MainMenu, footer, header {visibility: hidden;}
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 3rem !important;
        max-width: 1280px;
    }

    .stApp {
        background: linear-gradient(180deg, #F8FAFC 0%, #EFF3F8 100%) !important;
        color: #0F172A !important;
    }

    h1, h2, h3, h4, h5, h6,
    .stMarkdown p,
    label[data-testid="stWidgetLabel"] p,
    div[data-testid="stRadio"] label p,
    div[data-testid="stCheckbox"] label p,
    button[data-baseweb="tab"] p {
        color: #0F172A !important;
    }
    div[data-testid="stCaptionContainer"] p {
        color: #475569 !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 16px !important;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04) !important;
    }

    input, textarea, div[data-baseweb="select"] > div {
        background-color: #F8FAFC !important;
        color: #0F172A !important;
        border-color: #CBD5E1 !important;
    }

    /* Top Navbar */
    .telu-navbar {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        padding: 16px 28px;
        border-radius: 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.18);
    }
    .brand-box { display: flex; align-items: center; gap: 12px; }
    .brand-logo {
        background: linear-gradient(135deg, #DC2626 0%, #991B1B 100%);
        color: #FFFFFF !important;
        width: 38px;
        height: 38px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 18px;
    }
    .brand-title { font-size: 20px; font-weight: 800; color: #FFFFFF !important; letter-spacing: -0.4px; }
    .brand-snap { color: #F87171 !important; }
    .brand-sub { font-size: 11px; color: #94A3B8 !important; font-weight: 500; }
    .user-pill {
        background: rgba(255, 255, 255, 0.1);
        padding: 8px 16px;
        border-radius: 999px;
        font-size: 13px;
        color: #F8FAFC !important;
        border: 1px solid rgba(255, 255, 255, 0.16);
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .role-tag {
        background: #DC2626;
        color: #FFFFFF !important;
        font-size: 10px;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 999px;
        text-transform: uppercase;
    }

    /* Login Hero Card */
    .auth-hero {
        background: linear-gradient(135deg, #0F172A 0%, #1E1B4B 55%, #7F1D1D 100%);
        border-radius: 20px;
        padding: 38px;
        color: #FFFFFF !important;
        box-shadow: 0 20px 35px -10px rgba(15, 23, 42, 0.25);
    }
    .auth-hero h1, .auth-hero p, .auth-hero div { color: #FFFFFF !important; }
    .auth-badge {
        background: rgba(239, 68, 68, 0.22);
        border: 1px solid rgba(248, 113, 113, 0.45);
        color: #FECACA !important;
        padding: 6px 14px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 16px;
    }
    .auth-feature-item {
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.14);
        border-radius: 12px;
        padding: 12px 16px;
        margin-bottom: 10px;
        font-size: 13px;
        color: #F1F5F9 !important;
    }

    /* KPI Stat Cards */
    .kpi-card {
        background: #FFFFFF;
        border-radius: 16px;
        padding: 20px 22px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);
    }
    .kpi-label { font-size: 13px; font-weight: 600; color: #64748B !important; margin-bottom: 6px; }
    .kpi-value { font-size: 30px; font-weight: 800; color: #0F172A !important; line-height: 1.1; }
    .kpi-sub { font-size: 12px; margin-top: 8px; font-weight: 500; }

    /* Gallery Badges */
    .badge-hilang {
        background: #FEE2E2; color: #B91C1C !important; border: 1px solid #FECACA;
        padding: 3px 10px; border-radius: 999px; font-size: 11px; font-weight: 700;
    }
    .badge-ditemukan {
        background: #DCFCE7; color: #15803D !important; border: 1px solid #BBF7D0;
        padding: 3px 10px; border-radius: 999px; font-size: 11px; font-weight: 700;
    }
    .badge-selesai {
        background: #F1F5F9; color: #475569 !important; border: 1px solid #CBD5E1;
        padding: 3px 10px; border-radius: 999px; font-size: 11px; font-weight: 700; margin-left: 4px;
    }
    .hash-pill {
        font-family: 'Courier New', monospace; background: #F8FAFC; border: 1px solid #E2E8F0;
        color: #475569 !important; padding: 2px 8px; border-radius: 6px; font-size: 11px;
        display: inline-block; margin-top: 6px;
    }

    /* Buttons */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #DC2626 0%, #B91C1C 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
    }
    div.stButton > button[kind="primary"] p { color: #FFFFFF !important; }
    div.stButton > button[kind="secondary"] {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
    }
    div.stButton > button[kind="secondary"] p { color: #0F172A !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==========================================
# SESSION & COOKIE PERSISTENCE (URL BERSIH)
# ==========================================
cookie_manager = stx.CookieManager(key="telu_auth_cookie")

if "user" not in st.session_state:
    st.session_state["user"] = None
if "active_menu" not in st.session_state:
    st.session_state["active_menu"] = "Dashboard"
if "logged_out" not in st.session_state:
    st.session_state["logged_out"] = False

if st.session_state["user"] is None and not st.session_state["logged_out"]:
    saved_uid = cookie_manager.get(cookie="telu_uid")
    if saved_uid:
        try:
            restored_user = get_user_by_id(int(saved_uid))
            if restored_user:
                st.session_state["user"] = restored_user
        except Exception:
            pass


def is_laporan_hilang(jenis: str) -> bool:
    return str(jenis).strip().lower() in ("hilang", "kehilangan")


# ==========================================
# MODAL DETAIL BARANG (INTERAKTIF POP-UP)
# ==========================================
@st.dialog("Detail Laporan & Verifikasi Integritas", width="large")
def show_detail_modal(row: dict):
    c_img, c_det = st.columns([1, 1.2])
    with c_img:
        st.image(row["image_path"], use_container_width=True)
        st.caption(f"Format: **{row['format_akhir']}** • Ukuran: **{row['ukuran_kompresi_kb']} KB**")
    with c_det:
        badge = "🔴 BARANG HILANG" if is_laporan_hilang(row["jenis_laporan"]) else "🟢 BARANG DITEMUKAN"
        st.markdown(f"**{badge}** • Status: `{row['status_barang']}`")
        st.markdown(f"### {row['nama_barang']}")
        st.write(f"📍 **Lokasi Terakhir:** {row['lokasi_terakhir']}")
        st.write(f"🏷️ **Kategori:** {row['kategori_barang']}")
        st.write(f"📝 **Ciri-ciri Khusus:**\n{row['deskripsi_ciri']}")
        st.divider()
        st.write(f"👤 **Pelapor:** {row['nama_pelapor']} (`{row['nim']}` • {row['kelas']})")
        st.write(f"🕒 **Waktu Lapor:** {row['created_at']}")
        st.code(f"SHA-256: {row['hash_sha256']}", language="text")

        poster_bytes = generate_digital_poster(row)
        st.download_button(
            "📥 Unduh Poster Digital (PNG)",
            data=poster_bytes,
            file_name=f"Poster_{row['nama_barang'].replace(' ', '_')}.png",
            mime="image/png",
            type="primary",
            use_container_width=True,
        )


# ==========================================
# HALAMAN LOGIN & REGISTER
# ==========================================
def render_auth_page():
    col_hero, col_spacer, col_auth = st.columns([1.25, 0.08, 1])

    with col_hero:
        st.markdown(
            """
            <div class="auth-hero">
                <div>
                    <div class="auth-badge">SISTEM MULTIMEDIA • TELKOM UNIVERSITY</div>
                    <h1 style="font-size: 36px; font-weight: 800; line-height: 1.2; margin-bottom: 14px;">
                        Lost & Found <span style="color: #F87171;">Snap</span>
                    </h1>
                    <p style="color: #CBD5E1; font-size: 15px; line-height: 1.6; margin-bottom: 28px;">
                        Platform terpusat pelaporan barang hilang dan ditemukan di lingkungan kampus Telkom University. 
                        Dilengkapi pemrosesan citra otomatis, sensor privasi KTM, dan verifikasi integritas SHA-256.
                    </p>
                    <div class="auth-feature-item">
                        🖼️ <b>Auto-Crop 1:1 & Kompresi Cerdas</b> — Mengubah foto mentah menjadi WebP/JPEG ringan (< 150 KB).
                    </div>
                    <div class="auth-feature-item">
                        🛡️ <b>Privacy Blur & Watermark</b> — Sensor manual data sensitif NIM/NIK dan proteksi watermark kampus.
                    </div>
                    <div class="auth-feature-item">
                        🎨 <b>Auto-Placeholder & Digital Poster</b> — Laporan tanpa foto tetap visual dan siap sebar ke medsos.
                    </div>
                </div>
                <div style="margin-top: 30px; font-size: 12px; color: #94A3B8;">
                    Kelompok 7 • Fakultas Informatika — Telkom University
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_auth:
        with st.container(border=True):
            st.markdown("### Selamat Datang 👋")
            st.caption("Silakan masuk menggunakan akun NIM mahasiswa atau petugas kampus.")

            tab_login, tab_reg = st.tabs(["🔑 Masuk Akun", "📝 Daftar Mahasiswa"])

            with tab_login:
                with st.form("login_form", border=False):
                    nim_input = st.text_input("NIM / Username", placeholder="Masukkan NIM (cth: 103062500006)")
                    pass_input = st.text_input("Kata Sandi", type="password", placeholder="••••••••")
                    submitted = st.form_submit_button("Masuk ke Portal", type="primary", use_container_width=True)

                    if submitted:
                        logged_user = authenticate_user(nim_input, pass_input)
                        if logged_user:
                            st.session_state["user"] = logged_user
                            st.session_state["active_menu"] = "Dashboard"
                            st.session_state["logged_out"] = False
                            cookie_manager.set("telu_uid", str(logged_user["id"]), expires_at=datetime.now() + timedelta(days=1))
                            time.sleep(0.25)
                            st.rerun()
                        else:
                            st.error("NIM atau kata sandi salah.")

                st.markdown(
                    "<div style='margin: 14px 0 8px 0; text-align: center; font-size: 12px; color: #64748B;'>— Atau Coba Tanpa Daftar —</div>",
                    unsafe_allow_html=True,
                )
                if st.button("👤 Masuk sebagai Tamu (Guest)", use_container_width=True):
                    guest_user = authenticate_user("GUEST-TELU", "guest123")
                    if guest_user:
                        st.session_state["user"] = guest_user
                        st.session_state["active_menu"] = "Dashboard"
                        st.session_state["logged_out"] = False
                        cookie_manager.set("telu_uid", str(guest_user["id"]), expires_at=datetime.now() + timedelta(days=1))
                        time.sleep(0.25)
                        st.rerun()
                    else:
                        st.error("Akun tamu belum tersedia.")

            with tab_reg:
                with st.form("register_form", border=False):
                    reg_nama = st.text_input("Nama Lengkap", placeholder="Nama sesuai KTM")
                    reg_nim = st.text_input("NIM", placeholder="103062500xxx")
                    reg_kelas = st.text_input("Kelas", placeholder="IF-47-03")
                    reg_pass = st.text_input("Kata Sandi Baru", type="password", placeholder="Minimal 6 karakter")
                    reg_sub = st.form_submit_button("Buat Akun Mahasiswa", type="primary", use_container_width=True)

                    if reg_sub:
                        if not (reg_nama and reg_nim and reg_kelas and reg_pass):
                            st.warning("Harap lengkapi seluruh data pendaftaran.")
                        else:
                            ok, msg = register_user(reg_nama, reg_nim, reg_kelas, reg_pass)
                            if ok:
                                st.success(msg)
                            else:
                                st.error(msg)


# ==========================================
# HALAMAN UTAMA (DASHBOARD & FITUR)
# ==========================================
def render_main_app():
    user = st.session_state["user"]
    is_admin = user["role"] == "admin"

    # Top Navbar Modern
    st.markdown(
        f"""
        <div class="telu-navbar">
            <div class="brand-box">
                <div class="brand-logo">LF</div>
                <div>
                    <div class="brand-title">Lost & Found <span class="brand-snap">Snap</span></div>
                    <div class="brand-sub">Telkom University Campus Lost & Found System</div>
                </div>
            </div>
            <div class="user-pill">
                <span>👤 <b>{user['nama']}</b> ({user['nim']})</span>
                <span class="role-tag">{user['role']}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Navigation Bar (Admin tidak memiliki menu Buat Laporan)
    if is_admin:
        nav_items = ["Dashboard", "Galeri Kampus", "Poster Digital", "Moderasi Admin"]
    else:
        nav_items = ["Dashboard", "Galeri Kampus", "Buat Laporan", "Poster Digital"]

    if st.session_state["active_menu"] not in nav_items:
        st.session_state["active_menu"] = "Dashboard"

    icons = {
        "Dashboard": "📊",
        "Galeri Kampus": "🗂️",
        "Buat Laporan": "➕",
        "Poster Digital": "🖼️",
        "Moderasi Admin": "🛡️",
    }

    nav_cols = st.columns([1.15] * len(nav_items) + [0.85])
    for idx, item in enumerate(nav_items):
        is_active = st.session_state["active_menu"] == item
        if nav_cols[idx].button(
            f"{icons[item]} {item}",
            key=f"nav_btn_{item}",
            type="primary" if is_active else "secondary",
            use_container_width=True,
        ):
            st.session_state["active_menu"] = item
            st.rerun()

    if nav_cols[-1].button("🚪 Keluar", key="nav_btn_logout", use_container_width=True):
        st.session_state["user"] = None
        st.session_state["logged_out"] = True
        cookie_manager.delete("telu_uid")
        time.sleep(0.25)
        st.rerun()

    st.write("")
    menu = st.session_state["active_menu"]

    # ------------------------------------------
    # MENU 1: INTERACTIVE DASHBOARD
    # ------------------------------------------
    if menu == "Dashboard":
        all_reports = get_all_laporan()
        my_reports = get_all_laporan(user_id=user["id"])

        total_kampus = len(all_reports)
        total_hilang = sum(1 for x in all_reports if is_laporan_hilang(x["jenis_laporan"]) and x["status_barang"] == "Aktif")
        total_ditemukan = sum(1 for x in all_reports if not is_laporan_hilang(x["jenis_laporan"]) and x["status_barang"] == "Aktif")
        total_kembali = sum(1 for x in all_reports if x["status_barang"] == "Selesai")

        g1, g2 = st.columns([2.5, 1])
        with g1:
            st.markdown(f"### Halo, {user['nama']}! 👋")
            if is_admin:
                st.caption(f"Panel Pengawasan & Moderasi Petugas Keamanan • Unit **{user['kelas']}**")
            else:
                st.caption(f"Ringkasan aktivitas Lost & Found Telkom University • Kelas **{user['kelas']}**")
        with g2:
            if is_admin:
                if st.button("🛡️ Buka Panel Moderasi", type="primary", use_container_width=True):
                    st.session_state["active_menu"] = "Moderasi Admin"
                    st.rerun()
            else:
                if st.button("➕ Buat Laporan Baru Sekarang", type="primary", use_container_width=True):
                    st.session_state["active_menu"] = "Buat Laporan"
                    st.rerun()

        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">📦 Total Laporan Kampus</div>
                    <div class="kpi-value">{total_kampus}</div>
                    <div class="kpi-sub" style="color: #2563EB;">Tersimpan permanen di database</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with k2:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">🔴 Barang Masih Hilang</div>
                    <div class="kpi-value">{total_hilang}</div>
                    <div class="kpi-sub" style="color: #DC2626;">Perlu bantuan pencarian</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with k3:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">🟢 Barang Ditemukan</div>
                    <div class="kpi-value">{total_ditemukan}</div>
                    <div class="kpi-sub" style="color: #16A34A;">Menunggu diklaim pemilik</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with k4:
            sub_k4 = "Mode Petugas Keamanan" if is_admin else f"Laporan pribadi Anda: <b>{len(my_reports)}</b>"
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">✅ Berhasil Dikembalikan</div>
                    <div class="kpi-value">{total_kembali}</div>
                    <div class="kpi-sub" style="color: #475569;">{sub_k4}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.write("")

        if is_admin:
            active_reports = [x for x in all_reports if x["status_barang"] == "Aktif"]
            chart_col, mod_preview_col = st.columns([1.15, 1.35])
            with chart_col:
                with st.container(border=True):
                    st.markdown("#### 📍 Sebaran Lokasi Laporan Kampus")
                    if all_reports:
                        df = pd.DataFrame(all_reports)
                        loc_counts = df["lokasi_terakhir"].value_counts().head(6)
                        st.bar_chart(loc_counts, color="#DC2626", height=260)
                    else:
                        st.info("Grafik sebaran lokasi akan otomatis muncul setelah ada laporan masuk.")

            with mod_preview_col:
                with st.container(border=True):
                    st.markdown(f"#### ⚠️ Antrean Laporan Aktif ({len(active_reports)})")
                    if not active_reports:
                        st.success("Semua laporan barang sudah selesai dimoderasi dan dikembalikan.")
                    else:
                        for item in active_reports[:4]:
                            r_img, r_txt, r_btn = st.columns([0.65, 2.3, 1.1])
                            with r_img:
                                st.image(item["image_path"], use_container_width=True)
                            with r_txt:
                                st.markdown(f"**{item['nama_barang']}** (`{item['jenis_laporan']}`)")
                                st.caption(f"Pelapor: {item['nama_pelapor']} • 📍 {item['lokasi_terakhir']}")
                            with r_btn:
                                if st.button("✔ Selesai", key=f"adm_dash_done_{item['id']}", use_container_width=True):
                                    update_status_barang(item["id"], "Selesai")
                                    st.toast(f"'{item['nama_barang']}' ditandai selesai!")
                                    st.rerun()
        else:
            col_my, col_recent = st.columns([1.2, 1])
            with col_my:
                with st.container(border=True):
                    st.markdown(f"#### 👤 Laporan Pribadi Anda ({len(my_reports)})")
                    if not my_reports:
                        st.info("Anda belum membuat laporan apa pun. Klik **Buat Laporan Baru** untuk memulai.")
                    else:
                        for item in my_reports[:5]:
                            r_img, r_txt, r_btn = st.columns([0.65, 2.3, 1.1])
                            with r_img:
                                st.image(item["image_path"], use_container_width=True)
                            with r_txt:
                                st.markdown(f"**{item['nama_barang']}** (`{item['jenis_laporan']}`)")
                                st.caption(f"📍 {item['lokasi_terakhir']} • #{item['hash_sha256'][:10]}")
                            with r_btn:
                                if item["status_barang"] == "Aktif":
                                    if st.button("✔ Selesai", key=f"usr_dash_done_{item['id']}", use_container_width=True):
                                        update_status_barang(item["id"], "Selesai")
                                        st.rerun()
                                else:
                                    st.success("Kembali")

            with col_recent:
                with st.container(border=True):
                    st.markdown("#### 🕒 Laporan Terbaru di Kampus")
                    if not all_reports:
                        st.info("Belum ada laporan barang hilang atau ditemukan saat ini.")
                    else:
                        for recent in all_reports[:4]:
                            rc1, rc2 = st.columns([0.6, 2.4])
                            with rc1:
                                st.image(recent["image_path"], use_container_width=True)
                            with rc2:
                                badge_txt = "🔴 Hilang" if is_laporan_hilang(recent["jenis_laporan"]) else "🟢 Ditemukan"
                                st.markdown(f"**{recent['nama_barang']}** • {badge_txt}")
                                st.caption(f"📍 {recent['lokasi_terakhir']} • {recent['created_at'][:10]}")

    # ------------------------------------------
    # MENU 2: GALERI KAMPUS
    # ------------------------------------------
    elif menu == "Galeri Kampus":
        st.markdown("### 🗂️ Barang hilang & ditemukan di kampus")
        st.caption("Semua laporan terkumpul di satu tempat, tidak hilang setelah 24 jam seperti Story.")

        all_for_loc = get_all_laporan()
        unique_locs = sorted(list({item["lokasi_terakhir"] for item in all_for_loc if item["lokasi_terakhir"]}))

        with st.container(border=True):
            f1, f2, f3 = st.columns([2.4, 1.3, 1.5])
            with f1:
                search_q = st.text_input("Cari", placeholder="🔍 Cari nama barang, ciri-ciri, atau #hash...", label_visibility="collapsed")
            with f2:
                lokasi_opt = st.selectbox(
                    "Lokasi",
                    ["Semua lokasi"] + unique_locs,
                    label_visibility="collapsed",
                )
            with f3:
                jenis_opt = st.radio("Status", ["Semua", "Hilang", "Ditemukan"], horizontal=True, label_visibility="collapsed")

        items = get_all_laporan(
            search_query=search_q,
            lokasi=lokasi_opt,
            jenis=jenis_opt,
            hide_expired_selesai=True,
        )

        if not items:
            st.info("Tidak ada laporan yang cocok dengan filter pencarian.")
        else:
            grid_cols = st.columns(4)
            for i, row in enumerate(items):
                with grid_cols[i % 4]:
                    with st.container(border=True):
                        badge_cls = "badge-hilang" if is_laporan_hilang(row["jenis_laporan"]) else "badge-ditemukan"
                        badge_html = f'<span class="{badge_cls}">{row["jenis_laporan"]}</span>'
                        if row["status_barang"] == "Selesai":
                            badge_html += '<span class="badge-selesai">Sudah Kembali</span>'

                        st.markdown(badge_html, unsafe_allow_html=True)
                        st.write("")
                        st.image(row["image_path"], use_container_width=True)
                        st.markdown(f"**{row['nama_barang']}**")
                        st.caption(f"📍 {row['lokasi_terakhir']} • {row['created_at'][:10]}")
                        st.markdown(f"<div class='hash-pill'>#{row['hash_sha256'][:12]}</div>", unsafe_allow_html=True)
                        st.write("")
                        if st.button("Lihat Detail & Poster", key=f"det_{row['id']}", use_container_width=True):
                            show_detail_modal(row)

    # ------------------------------------------
    # MENU 3: BUAT LAPORAN (KHUSUS MAHASISWA/USER)
    # ------------------------------------------
    elif menu == "Buat Laporan" and not is_admin:
        st.markdown("### ➕ Buat laporan baru")
        st.caption("Foto boleh dilewati. Tanpa foto, sistem membuat kartu gambar otomatis dari ciri-ciri barang.")

        col_form, col_media = st.columns([1.05, 1])
        is_guest = user["nim"] == "GUEST-TELU"

        with col_form:
            with st.container(border=True):
                st.markdown("#### 📋 Data laporan")
                jenis_laporan = st.radio("Jenis Laporan", ["Kehilangan", "Menemukan"], format_func=lambda x: f"Saya {x.lower()}", horizontal=True)

                c_nama, c_nim = st.columns(2)
                with c_nama:
                    nama_pelapor = st.text_input(
                        "Nama pelapor",
                        value="" if is_guest else user["nama"],
                        placeholder="Masukkan nama lengkap Anda",
                    )
                with c_nim:
                    nim_pelapor = st.text_input(
                        "NIM",
                        value="" if is_guest else user["nim"],
                        placeholder="Contoh: 103062500006",
                    )

                c_kelas, c_kat = st.columns(2)
                with c_kelas:
                    kelas_pelapor = st.text_input(
                        "Kelas",
                        value="" if is_guest else user["kelas"],
                        placeholder="Contoh: IF-47-03",
                    )
                with c_kat:
                    kategori = st.selectbox(
                        "Kategori barang",
                        ["Dompet", "KTM / Kartu Identitas", "Elektronik / Aksesoris", "Tas / Ransel", "Kunci", "Lainnya"],
                    )

                nama_barang = st.text_input("Nama barang", placeholder="mis. Dompet kulit cokelat")
                lokasi_terakhir = st.text_input("Tempat terakhir hilang / ditemukan", placeholder="mis. Gedung TULT lantai 3")
                deskripsi_ciri = st.text_area("Ciri-ciri barang", placeholder="Warna, merek, isi, tanda khusus")

                submit_btn = st.button("🚀 Kirim laporan sekarang", type="primary", use_container_width=True)

        with col_media:
            with st.container(border=True):
                st.markdown("#### 📸 Pengolahan Citra & Keamanan (Opsional)")
                uploaded_file = st.file_uploader("Pilih foto (JPG, atau WebP)", type=["jpg", "jpeg", "webp"])

                b_col, c_col = st.columns(2)
                with b_col:
                    brightness = st.slider("Kecerahan", 0.5, 1.5, 1.0, 0.05)
                with c_col:
                    contrast = st.slider("Kontras", 0.5, 1.5, 1.0, 0.05)

                enable_manual_blur = st.checkbox("Sensor Manual (Tarik kotak langsung di atas foto untuk blur)", value=False)
                user_blur_boxes = []

                raw_bytes = uploaded_file.getvalue() if uploaded_file else b""

                if uploaded_file and enable_manual_blur:
                    st.caption("🖱️ Tarik & geser sudut kotak merah di bawah ini untuk menutupi area sensitif:")
                    base_select_img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
                    base_select_img.thumbnail((360, 360), Image.Resampling.LANCZOS)
                    sel_w, sel_h = base_select_img.size

                    box = st_cropper(
                        base_select_img,
                        realtime_update=True,
                        box_color="#DC2626",
                        aspect_ratio=None,
                        return_type="box",
                        key=f"blur_box_{uploaded_file.name}",
                    )
                    if box:
                        bx1 = box["left"] / float(sel_w)
                        by1 = box["top"] / float(sel_h)
                        bx2 = (box["left"] + box["width"]) / float(sel_w)
                        by2 = (box["top"] + box["height"]) / float(sel_h)
                        user_blur_boxes.append((bx1, by1, bx2, by2))

                w_col, f_col = st.columns([1.5, 1])
                with w_col:
                    enable_wm = st.checkbox("Tempel watermark LOST & FOUND TEL-U", value=True)
                with f_col:
                    target_fmt = st.selectbox("Format Output", ["WebP", "JPEG"])

                preview_hash = generate_sha256_hash(f"{nim_pelapor}-{nama_barang}", raw_bytes)

                if uploaded_file:
                    processed = process_uploaded_image(
                        uploaded_bytes=raw_bytes,
                        brightness=brightness,
                        contrast=contrast,
                        blur_boxes=user_blur_boxes,
                        enable_watermark=enable_wm,
                        target_format=target_fmt,
                    )
                    st.image(
                        processed["preview_image"],
                        caption=f"Hasil Akhir ({processed['final_dim']} px • Rasio Asli)",
                        use_container_width=True,
                    )

                    m1, m2, m3 = st.columns(3)
                    m1.metric("Ukuran asli", f"{processed['original_size_kb']} KB")
                    m2.metric("Setelah kompresi", f"{processed['compressed_size_kb']} KB")
                    m3.metric("Format", processed["format"])
                    st.caption(f"SHA-256: `{preview_hash}`")
                else:
                    placeholder_preview = generate_placeholder_card(
                        kategori=kategori,
                        nama_barang=nama_barang or "Nama Barang",
                        deskripsi=deskripsi_ciri or "Ciri-ciri barang akan ditampilkan otomatis pada kartu.",
                        lokasi=lokasi_terakhir or "Lingkungan Telkom University",
                    )
                    st.image(placeholder_preview, caption="Preview Kartu Placeholder Otomatis (1:1)", width=270)

        if submit_btn:
            if not (nama_pelapor and nim_pelapor and nama_barang and lokasi_terakhir and deskripsi_ciri):
                st.error("Mohon lengkapi seluruh kolom data laporan.")
            else:
                if uploaded_file:
                    final_bytes = processed["compressed_bytes"]
                    ext = processed["format"]
                    orig_kb = processed["original_size_kb"]
                    comp_kb = processed["compressed_size_kb"]
                    has_photo = 1
                else:
                    final_bytes = generate_placeholder_card(kategori, nama_barang, deskripsi_ciri, lokasi_terakhir)
                    ext = "WebP"
                    orig_kb = 0.0
                    comp_kb = round(len(final_bytes) / 1024, 1)
                    has_photo = 0

                saved_path = save_image_bytes(final_bytes, preview_hash, ext)

                insert_laporan(
                    {
                        "user_id": user["id"],
                        "jenis_laporan": jenis_laporan,
                        "nama_pelapor": nama_pelapor,
                        "nim": nim_pelapor,
                        "kelas": kelas_pelapor,
                        "kategori_barang": kategori,
                        "nama_barang": nama_barang,
                        "lokasi_terakhir": lokasi_terakhir,
                        "deskripsi_ciri": deskripsi_ciri,
                        "has_photo": has_photo,
                        "image_path": saved_path,
                        "ukuran_asli_kb": orig_kb,
                        "ukuran_kompresi_kb": comp_kb,
                        "format_akhir": ext,
                        "is_watermarked": 1 if (uploaded_file and enable_wm) else 0,
                        "hash_sha256": preview_hash,
                    }
                )
                st.toast("Laporan berhasil dipublikasikan ke Galeri Kampus!", icon="✅")
                st.session_state["active_menu"] = "Galeri Kampus"
                st.rerun()

    # ------------------------------------------
    # MENU 4: POSTER DIGITAL
    # ------------------------------------------
    elif menu == "Poster Digital":
        st.markdown("### 🖼️ Poster digital siap sebar")
        st.caption("Satu lembar gambar ringkas beresolusi tinggi untuk dibagikan ke WhatsApp atau Instagram Story.")

        all_items = get_all_laporan()
        if not all_items:
            st.warning("Belum ada laporan di database. Buat laporan terlebih dahulu.")
        else:
            c_left, c_right = st.columns([1, 1.2])
            with c_left:
                with st.container(border=True):
                    options_map = {f"{item['nama_barang']} ({item['jenis_laporan']} • #{item['hash_sha256'][:8]})": item for item in all_items}
                    selected_label = st.selectbox("Pilih laporan barang", list(options_map.keys()))
                    selected_item = options_map[selected_label]

                    poster_bytes = generate_digital_poster(selected_item)
                    st.download_button(
                        label="📥 Unduh Poster PNG",
                        data=poster_bytes,
                        file_name=f"Poster_{selected_item['nama_barang'].replace(' ', '_')}.png",
                        mime="image/png",
                        type="primary",
                        use_container_width=True,
                    )
                    st.caption("Poster otomatis memuat foto/kartu, lokasi terakhir, ciri-ciri barang, dan kode verifikasi SHA-256.")

            with c_right:
                with st.container(border=True):
                    st.image(poster_bytes, caption="Preview Poster Digital (800 x 1080 px)", width=390)

    # ------------------------------------------
    # MENU 5: MODERASI ADMIN (KHUSUS ADMIN)
    # ------------------------------------------
    elif menu == "Moderasi Admin" and is_admin:
        st.markdown("### 🛡️ Panel Moderasi Petugas Keamanan Kampus")
        st.caption("Analitik sebaran lokasi dan kontrol status pengembalian barang seluruh mahasiswa Telkom University.")

        all_reports = get_all_laporan()
        if not all_reports:
            st.info("Belum ada data laporan masuk.")
        else:
            with st.container(border=True):
                st.markdown("#### 📍 Analitik Sebaran Lokasi Laporan Kampus")
                df = pd.DataFrame(all_reports)
                loc_counts = df["lokasi_terakhir"].value_counts().head(8)
                st.bar_chart(loc_counts, color="#DC2626", height=240)

            st.write("")
            for item in all_reports:
                with st.container(border=True):
                    c1, c2, c3 = st.columns([0.65, 3.2, 1.15])
                    with c1:
                        st.image(item["image_path"], use_container_width=True)
                    with c2:
                        st.markdown(f"**{item['nama_barang']}** — Pelapor: **{item['nama_pelapor']}** (`{item['nim']}` • {item['kelas']})")
                        st.caption(f"{item['jenis_laporan']} • 📍 {item['lokasi_terakhir']} • Hash: `#{item['hash_sha256'][:12]}`")
                    with c3:
                        new_st = st.selectbox(
                            "Status",
                            ["Aktif", "Selesai"],
                            index=0 if item["status_barang"] == "Aktif" else 1,
                            key=f"adm_{item['id']}",
                            label_visibility="collapsed",
                        )
                        if new_st != item["status_barang"]:
                            update_status_barang(item["id"], new_st)
                            st.toast(f"Status '{item['nama_barang']}' diperbarui ke {new_st}!")
                            st.rerun()


if st.session_state["user"] is None:
    render_auth_page()
else:
    render_main_app()