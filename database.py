import sqlite3
import hashlib
import os
from datetime import datetime

DB_NAME = "lost_found_telu.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def init_db():
    conn = get_connection()
    c = conn.cursor()

    # Tabel Users (Mendukung 2 Role: 'user' dan 'admin')
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL,
            nim TEXT UNIQUE NOT NULL,
            kelas TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            created_at TEXT NOT NULL
        )
    """)

    # Tabel Laporan Barang Hilang & Ditemukan
    c.execute("""
        CREATE TABLE IF NOT EXISTS laporan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            jenis_laporan TEXT NOT NULL,
            status_barang TEXT NOT NULL DEFAULT 'Aktif',
            nama_pelapor TEXT NOT NULL,
            nim TEXT NOT NULL,
            kelas TEXT NOT NULL,
            kategori_barang TEXT NOT NULL,
            nama_barang TEXT NOT NULL,
            lokasi_terakhir TEXT NOT NULL,
            deskripsi_ciri TEXT NOT NULL,
            has_photo INTEGER NOT NULL DEFAULT 0,
            image_path TEXT NOT NULL,
            ukuran_asli_kb REAL DEFAULT 0,
            ukuran_kompresi_kb REAL DEFAULT 0,
            format_akhir TEXT DEFAULT 'WebP',
            is_watermarked INTEGER DEFAULT 1,
            hash_sha256 TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    # Pastikan akun Admin & akun Tamu (Guest) selalu tersedia di database
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    default_users = [
        ("Petugas Keamanan Tel-U", "admin", "STAFF-TELU", hash_password("admin123"), "admin", now),
        ("Mahasiswa Tamu", "GUEST-TELU", "UMUM", hash_password("guest123"), "user", now),
    ]
    c.executemany(
        "INSERT OR IGNORE INTO users (nama, nim, kelas, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        default_users,
    )

    # Database lama belum menyimpan waktu perubahan status laporan.
    columns = {row["name"] for row in c.execute("PRAGMA table_info(laporan)")}
    if "updated_at" not in columns:
        c.execute("ALTER TABLE laporan ADD COLUMN updated_at TEXT")

    c.execute("UPDATE laporan SET jenis_laporan = 'Ditemukan' WHERE status_barang = 'Selesai'")

    conn.commit()
    conn.close()


def authenticate_user(nim: str, password: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT id, nama, nim, kelas, role FROM users WHERE nim = ? AND password_hash = ?",
        (nim.strip(), hash_password(password)),
    )
    user = c.fetchone()
    conn.close()
    return dict(user) if user else None


def get_user_by_id(user_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT id, nama, nim, kelas, role FROM users WHERE id = ?",
        (user_id,),
    )
    user = c.fetchone()
    conn.close()
    return dict(user) if user else None


def register_user(nama: str, nim: str, kelas: str, password: str):
    conn = get_connection()
    c = conn.cursor()
    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute(
            "INSERT INTO users (nama, nim, kelas, password_hash, role, created_at) VALUES (?, ?, ?, ?, 'user', ?)",
            (nama.strip(), nim.strip(), kelas.strip(), hash_password(password), now),
        )
        conn.commit()
        return True, "Registrasi berhasil! Silakan login menggunakan NIM Anda."
    except sqlite3.IntegrityError:
        return False, "NIM sudah terdaftar. Silakan langsung login."
    finally:
        conn.close()


def insert_laporan(data: dict):
    conn = get_connection()
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute(
        """
        INSERT INTO laporan (
            user_id, jenis_laporan, status_barang, nama_pelapor, nim, kelas,
            kategori_barang, nama_barang, lokasi_terakhir, deskripsi_ciri,
            has_photo, image_path, ukuran_asli_kb, ukuran_kompresi_kb,
            format_akhir, is_watermarked, hash_sha256, created_at
        ) VALUES (?, ?, 'Aktif', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data["user_id"],
            data["jenis_laporan"],
            data["nama_pelapor"],
            data["nim"],
            data["kelas"],
            data["kategori_barang"],
            data["nama_barang"],
            data["lokasi_terakhir"],
            data["deskripsi_ciri"],
            data["has_photo"],
            data["image_path"],
            data["ukuran_asli_kb"],
            data["ukuran_kompresi_kb"],
            data["format_akhir"],
            data["is_watermarked"],
            data["hash_sha256"],
            now,
        ),
    )
    conn.commit()
    conn.close()


def get_all_laporan(
    search_query: str = "",
    lokasi: str = "Semua lokasi",
    jenis: str = "Semua",
    user_id: int = None,
    hide_expired_selesai: bool = False,
):
    conn = get_connection()
    c = conn.cursor()

    query = "SELECT * FROM laporan WHERE 1=1"
    params = []

    if user_id is not None:
        query += " AND user_id = ?"
        params.append(user_id)

    if search_query and search_query.strip():
        kw = f"%{search_query.strip().lower()}%"
        query += """
            AND (
                LOWER(nama_barang) LIKE ?
                OR LOWER(deskripsi_ciri) LIKE ?
                OR LOWER(hash_sha256) LIKE ?
            )
        """
        params.extend([kw, kw, kw])

    if lokasi and lokasi != "Semua lokasi":
        query += " AND lokasi_terakhir = ?"
        params.append(lokasi)

    if jenis == "Hilang":
        query += " AND TRIM(LOWER(jenis_laporan)) IN ('hilang', 'kehilangan') AND status_barang != 'Selesai'"
    elif jenis == "Ditemukan":
        query += " AND (TRIM(LOWER(jenis_laporan)) = 'ditemukan' OR status_barang = 'Selesai')"

    if hide_expired_selesai:
        query += """
            AND NOT (
                status_barang = 'Selesai'
                AND datetime(COALESCE(updated_at, created_at)) <= datetime('now', '-3 days')
            )
        """

    query += " ORDER BY id DESC"

    c.execute(query, params)
    rows = [dict(row) for row in c.fetchall()]
    conn.close()
    return rows


def update_status_barang(laporan_id: int, status_baru: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "UPDATE laporan SET status_barang = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (status_baru, laporan_id),
    )
    conn.commit()
    conn.close()


def delete_laporan(laporan_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT image_path FROM laporan WHERE id = ?", (laporan_id,))
    row = c.fetchone()
    if row and row["image_path"] and os.path.exists(row["image_path"]):
        try:
            os.remove(row["image_path"])
        except OSError:
            pass
    c.execute("DELETE FROM laporan WHERE id = ?", (laporan_id,))
    conn.commit()
    conn.close()
