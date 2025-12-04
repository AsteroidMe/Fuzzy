import streamlit as st
import pandas as pd
import numpy as np

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="SPK Web Hosting - SAW vs TOPSIS",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Analisis Perbandingan SAW dan TOPSIS untuk Rekomendasi Web Hosting")
st.markdown("""
Sistem Pendukung Keputusan (SPK) ini membandingkan dua metode untuk memilih layanan hosting terbaik:
1.  **Simple Additive Weighting (SAW)**
2.  **Technique for Order of Preference by Similarity to Ideal Solution (TOPSIS)**
""")

# --- 1. DEFINISI KRITERIA & BOBOT ---
# Sesuai dengan Tabel Kriteria yang dibahas
CRITERIA_CONFIG = {
    "C1": {"name": "Harga Bulanan (C1)", "weight": 0.30, "attr": "cost"},
    "C2": {"name": "Kapasitas (C2)", "weight": 0.20, "attr": "benefit"},
    "C3": {"name": "Bandwidth (C3)", "weight": 0.20, "attr": "benefit"},
    "C4": {"name": "Backup (C4)", "weight": 0.10, "attr": "benefit"},
    "C5": {"name": "Keamanan (C5)", "weight": 0.20, "attr": "benefit"}
}

# --- 2. DATA AWAL (DEFAULT - DATA RIIL) ---
# Data mentah sesuai tabel spesifikasi awal
default_data = {
    "Alternatif": ["A1 (Hostinger)", "A2 (Bluehost)", "A3 (Dreamhost)", "A4 (Siteground)", "A5 (InMotion)"],
    "Harga Bulanan (C1)": [32420, 66340, 43060, 49710, 49710],    # Dalam Rupiah
    "Kapasitas (C2)": [25, 10, 50, 10, 100],                       # Dalam GB
    "Bandwidth (C3)": ["Unlimited", "Unmetered", "Unmetered", "Unmetered", "Unmetered"],
    "Backup (C4)": ["Mingguan", "Mingguan", "Harian", "Harian", "Harian"],
    "Keamanan (C5)": ["SSL", "SSL", "SSL", "SSL", "SSL"]
}

# --- 3. FUNGSI LOGIKA (KUANTIFIKASI DATA) ---
def run_quantification(df):
    """
    Mengubah data mentah (Rupiah, GB, Teks) menjadi Skala 1-5
    sesuai 'Tabel Sub Kriteria'
    """
    df_score = df.copy()
    
    # 1. Konversi Harga (C1)
    # Aturan: Murah = Skor Tinggi (Karena di SAW kita jadikan Benefit)
    # Range: 0-20k(5), 20-40k(4), 40-60k(3), 60-80k(2), >80k(1)
    def score_c1(val):
        if val <= 20000: return 5
        elif val <= 40000: return 4
        elif val <= 60000: return 3
        elif val <= 80000: return 2
        else: return 1

    # 2. Konversi Kapasitas (C2)
    # Range: 80-100(5), 60-80(4), 40-60(3), 20-40(2), 0-20(1)
    def score_c2(val):
        if val >= 80: return 5
        elif val >= 60: return 4
        elif val >= 40: return 3
        elif val >= 20: return 2
        else: return 1

    # 3. Konversi Bandwidth (C3)
    # Unlimited/Unmetered dianggap skor 5 (Maksimal)
    def score_c3(val):
        return 5 # Sesuai data, semua dapat skor 5

    # 4. Konversi Backup (C4)
    # Harian(5), Mingguan(3)
    def score_c4(val):
        if "Harian" in str(val) or "Daily" in str(val): return 5
        elif "Mingguan" in str(val) or "Weekly" in str(val): return 3
        else: return 1

    # 5. Konversi Keamanan (C5)
    # SSL standar diberi skor 2 (sesuai tabel sub kriteria sebelumnya)
    def score_c5(val):
        return 2

    # Terapkan fungsi
    df_score["Harga Bulanan (C1)"] = df["Harga Bulanan (C1)"].apply(score_c1)
    df_score["Kapasitas (C2)"] = df["Kapasitas (C2)"].apply(score_c2)
    df_score["Bandwidth (C3)"] = df["Bandwidth (C3)"].apply(score_c3)
    df_score["Backup (C4)"] = df["Backup (C4)"].apply(score_c4)
    df_score["Keamanan (C5)"] = df["Keamanan (C5)"].apply(score_c5)

    return df_score

# --- 4. INTERFACE INPUT DATA ---

with st.expander("📝 Input Data Hosting (Data Mentah)", expanded=True):
    st.info("Silakan ubah data di bawah ini untuk melakukan simulasi nilai.")
    df_input = pd.DataFrame(default_data)
    edited_df = st.data_editor(df_input, num_rows="dynamic", use_container_width=True)

col1, col2 = st.columns([1, 5])
with col1:
    btn_hitung = st.button("🚀 Hitung Ranking", type="primary")

# --- 5. PROSES KALKULASI ---

if btn_hitung:
    st.divider()
    
    # A. PRE-PROCESSING
    alternatives = edited_df["Alternatif"].values
    data_only = edited_df.drop(columns=["Alternatif"])
    
    # Lakukan Kuantifikasi (Ubah ke angka 1-5)
    matrix_x = run_quantification(data_only)
    matrix_x.index = alternatives 
    
    # Ambil list bobot
    weights = np.array([conf["weight"] for key, conf in CRITERIA_CONFIG.items()])

    st.subheader("1. Matriks Keputusan (X) - Hasil Konversi Skala 1-5")
    st.dataframe(matrix_x)

    # --- TAB UNTUK MASING-MASING METODE ---
    tab_saw, tab_topsis, tab_result = st.tabs(["📊 Metode SAW", "📉 Metode TOPSIS", "🏆 Ranking Akhir"])

    # === METODE SAW ===
    with tab_saw:
        st.header("Perhitungan SAW")
        st.markdown("Prinsip: Normalisasi Linear & Penjumlahan Terbobot")
        
        # 1. Normalisasi SAW
        # Karena C1 (Harga) sudah dikonversi jadi skor 1-5 (dimana 5=Murah/Bagus),
        # Maka SEMUA kriteria dianggap BENEFIT secara matematis di tahap ini.
        # Rumus: r = x / max(x)
        
        max_vals = matrix_x.max()
        norm_saw = matrix_x.div(max_vals)
        
        st.write("**a. Tabel Normalisasi (R):**")
        st.dataframe(norm_saw.style.format("{:.4f}"))
        
        # 2. Perankingan SAW
        # V = Sum(R * W)
        saw_final = norm_saw.dot(weights) 
        
        st.write("**b. Nilai Preferensi (V):**")
        df_saw_res = pd.DataFrame(saw_final, columns=["Nilai SAW"])
        st.dataframe(df_saw_res.style.format("{:.4f}").background_gradient(cmap="Blues"))

    # === METODE TOPSIS ===
    with tab_topsis:
        st.header("Perhitungan TOPSIS")
        st.markdown("Prinsip: Jarak terhadap Solusi Ideal Positif & Negatif")
        
        # 1. Normalisasi Matriks (Pembagi Akar Kuadrat)
        # Rumus: r = x / sqrt(sum(x^2))
        divisor = np.sqrt((matrix_x**2).sum())
        norm_topsis = matrix_x.div(divisor)
        
        st.write("**a. Matriks Ternormalisasi (R):**")
        st.dataframe(norm_topsis.style.format("{:.4f}"))

        # 2. Matriks Terbobot (Y)
        # Rumus: y = r * weight
        weighted_topsis = norm_topsis * weights
        
        st.write("**b. Matriks Ternormalisasi Terbobot (Y):**")
        st.dataframe(weighted_topsis.style.format("{:.4f}"))

        # 3. Solusi Ideal Positif (A+) & Negatif (A-)
        # Karena semua sudah skala benefit (1-5), maka A+ = Max, A- = Min
        ideal_pos = weighted_topsis.max()
        ideal_neg = weighted_topsis.min()

        st.write("**c. Solusi Ideal:**")
        col_ide1, col_ide2 = st.columns(2)
        with col_ide1:
            st.write("Positif (A+):", ideal_pos.values)
        with col_ide2:
            st.write("Negatif (A-):", ideal_neg.values)

        # 4. Jarak Euclidean (D+ dan D-)
        dist_pos = np.sqrt(((weighted_topsis - ideal_pos)**2).sum(axis=1))
        dist_neg = np.sqrt(((weighted_topsis - ideal_neg)**2).sum(axis=1))

        # 5. Nilai Preferensi (V)
        # Rumus: V = D- / (D- + D+)
        topsis_score = dist_neg / (dist_neg + dist_pos)

        st.write("**d. Hasil Perhitungan Jarak & Preferensi:**")
        df_topsis_res = pd.DataFrame({
            "D+ (Jarak Ideal)": dist_pos,
            "D- (Jarak Negatif)": dist_neg,
            "Nilai TOPSIS (V)": topsis_score
        })
        st.dataframe(df_topsis_res.style.format("{:.4f}").background_gradient(subset=["Nilai TOPSIS (V)"], cmap="Greens"))

    # === TAB HASIL AKHIR ===
    with tab_result:
        st.header("Perbandingan Hasil Ranking")
        
        # Gabungkan semua hasil
        final_df = pd.DataFrame(index=alternatives)
        
        # SAW Data
        final_df["SAW Score"] = df_saw_res["Nilai SAW"]
        final_df["SAW Rank"] = final_df["SAW Score"].rank(ascending=False).astype(int)
        
        # TOPSIS Data
        final_df["TOPSIS Score"] = df_topsis_res["Nilai TOPSIS (V)"]
        final_df["TOPSIS Rank"] = final_df["TOPSIS Score"].rank(ascending=False).astype(int)
        
        # Tampilkan tabel gabungan
        st.dataframe(final_df.style.format({
            "SAW Score": "{:.4f}",
            "TOPSIS Score": "{:.4f}"
        }).highlight_max(subset=["SAW Score", "TOPSIS Score"], color='lightgreen', axis=0))
        
        # Analisis Pemenang
        best_saw = final_df.sort_values("SAW Rank").index[0]
        best_topsis = final_df.sort_values("TOPSIS Rank").index[0]
        
        st.success(f"""
        **Kesimpulan Rekomendasi:**
        * 🥇 Pemenang menurut **SAW**: **{best_saw}**
        * 🥇 Pemenang menurut **TOPSIS**: **{best_topsis}**
        """)

        # Cek Konsistensi
        if best_saw == best_topsis:
            st.info("✅ **Konsisten!** Kedua metode merekomendasikan layanan hosting yang sama.")
        else:
            st.warning("⚠️ **Berbeda!** Terjadi perbedaan rekomendasi antara kedua metode.")

else:
    st.warning("Data siap. Klik tombol 'Hitung Ranking' di atas untuk memulai simulasi.")