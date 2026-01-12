import json
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium
import os
from dotenv import load_dotenv
from google import genai

st.set_page_config(layout="wide")

# =============================
# Gemini Client Setup
# =============================
load_dotenv()
client = genai.Client(api_key=os.getenv("api_gemini"))

# =============================
# Config Path (sesuaikan bila perlu)
# =============================
DATA_RISK = "data/risk_cluster.csv"
DATA_DETAIL = "data/detail_penyebab.csv"
GEOJSON_PATH = "data/Jabar_By_Kab.geojson"

# =============================
# Helpers
# =============================
def norm_kabkota(name: str) -> str:
    """
    Key untuk MATCHING ke GeoJSON:
    - Kabupaten Bandung -> BANDUNG
    - Kota Bandung -> KOTA BANDUNG
    """
    s = str(name).strip().upper()
    s = " ".join(s.split())
    s = s.replace("KAB. ", "KABUPATEN ")
    # kalau KABUPATEN -> buang prefix
    if s.startswith("KABUPATEN "):
        s = s.replace("KABUPATEN ", "", 1)
    return s

def display_kabkota(name: str) -> str:
    """
    Nama untuk TAMPILAN dropdown/panel:
    - Jika bukan diawali KOTA, anggap Kabupaten -> "KABUPATEN X"
    - Jika sudah KOTA, tetap "KOTA X"
    """
    s = str(name).strip().upper()
    s = " ".join(s.split())
    s = s.replace("KAB. ", "KABUPATEN ")

    if s.startswith("KOTA "):
        return s
    if s.startswith("KABUPATEN "):
        return s

    # GeoJSON biasanya cuma "BANDUNG", "GARUT", dst -> tampilkan sebagai Kabupaten
    return f"KABUPATEN {s}"

@st.cache_data
def load_geojson(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

@st.cache_data
def load_data():
    risk = pd.read_csv(DATA_RISK)
    detail = pd.read_csv(DATA_DETAIL)
    return risk, detail

def pick_clicked_name(out: dict):
    for key in ["last_object_clicked_tooltip", "last_object_clicked_popup", "last_active_drawing"]:
        v = out.get(key)
        if isinstance(v, dict) and v.get("properties"):
            return v["properties"].get("nama_kabkota_geo") or v["properties"].get("KABKOT")
    return None

# =============================
# Load
# =============================
geo = load_geojson(GEOJSON_PATH)
risk, detail = load_data()

# =============================
# Header + Filter Tahun + Jenis Kematian
# =============================
st.markdown(
    "<h1 style='text-align:center; margin-top: 10px;'>Peta Penyebaran Penyebab Kematian dan Rekomendasi Penanganan Berbasis AI</h1>",
    unsafe_allow_html=True
)
st.divider()


filter_col1, filter_col2, _ = st.columns([1.5, 1.5, 5])

with filter_col1:
    tahun = st.selectbox(
        "Tahun",
        sorted(risk["tahun"].dropna().unique())
    )

with filter_col2:
    if "jenis_kematian" in risk.columns:
        jenis = st.selectbox(
            "Jenis Kematian",
            sorted(risk["jenis_kematian"].dropna().unique())
        )
    else:
        jenis = None




# =============================
# Filter risk sesuai pilihan
# =============================
risk_y = risk[risk["tahun"] == tahun].copy()
if jenis is not None:
    risk_y = risk_y[risk_y["jenis_kematian"] == jenis].copy()

need_cols = ["nama_kabupaten_kota", "cluster", "risk_label", "total_kematian"]
missing = [c for c in need_cols if c not in risk_y.columns]
if missing:
    st.error(f"Kolom {missing} tidak ditemukan di risk_cluster.csv.")
    st.stop()

# key match & display
risk_y["kabkota_norm"] = risk_y["nama_kabupaten_kota"].apply(norm_kabkota)
risk_y["kabkota_display"] = risk_y["nama_kabupaten_kota"].apply(display_kabkota)

# kalau ada duplikat norm (contoh: Bandung & Kota Bandung) ini normal dan aman,
# tapi untuk map lookup harus unik. Karena GeoJSON "BANDUNG" itu Kabupaten Bandung,
# maka kita buat lookup map dengan aturan:
# - jika norm mengandung "KOTA " -> itu kota
# - selain itu -> kabupaten
# Karena norm untuk kabupaten adalah "BANDUNG" (tanpa KOTA), dan kota "KOTA BANDUNG" unik.
risk_map = (
    risk_y.drop_duplicates(subset=["kabkota_norm"])  # harusnya aman karena norm kota beda
         .set_index("kabkota_norm")[["cluster", "risk_label", "total_kematian"]]
         .to_dict("index")
)

# =============================
# Enrich GeoJSON (tooltip tampil "KABUPATEN ..." untuk yang bukan KOTA)
# =============================
geo_enriched = json.loads(json.dumps(geo))

for ft in geo_enriched.get("features", []):
    props = ft.get("properties", {})
    geo_name = props.get("KABKOT", "")
    geo_norm = norm_kabkota(geo_name)

    info = risk_map.get(geo_norm)
    if info:
        props["cluster"] = int(info["cluster"])
        props["risk_label"] = str(info["risk_label"])
        props["total_kematian"] = float(info["total_kematian"])
    else:
        props["cluster"] = None
        props["risk_label"] = "N/A"
        props["total_kematian"] = 0.0

    # ✅ TAMPILAN: kalau geojson bukan "KOTA ...", tampil sebagai "KABUPATEN ..."
    props["nama_kabkota_geo"] = display_kabkota(geo_name)

# =============================
# Buat peta
# =============================
m = folium.Map(location=[-6.90, 107.60], zoom_start=8, tiles="cartodbpositron")

palette = ["#2ecc71", "#a3e635", "#facc15", "#fb923c", "#ef4444"]

def style_fn(feature):
    c = feature["properties"].get("cluster", None)
    if c is None:
        return {"fillOpacity": 0.15, "weight": 0.8, "color": "#777", "fillColor": "#cccccc"}
    c = int(c)
    idx = min(c, len(palette) - 1)
    return {"fillOpacity": 0.7, "weight": 1.0, "color": "white", "fillColor": palette[idx]}

tooltip = folium.GeoJsonTooltip(
    fields=["nama_kabkota_geo", "risk_label", "total_kematian"],
    aliases=["Wilayah", "Risiko", "Total Kematian"],
    localize=True
)

folium.GeoJson(
    geo_enriched,
    name="Risiko Wilayah",
    style_function=style_fn,
    tooltip=tooltip,
    highlight_function=lambda x: {"weight": 2.5, "color": "#000000"},
).add_to(m)

folium.LayerControl().add_to(m)

out = st_folium(
    m,
    height=420,
    use_container_width=True,
    key="map",
    returned_objects=["last_object_clicked_tooltip", "last_object_clicked_popup", "last_active_drawing"],
)

clicked_name = pick_clicked_name(out)  # ini sudah versi display: "KABUPATEN BANDUNG" / "KOTA BANDUNG"

st.divider()

# =============================
# Layout bawah (Detail | Top Penyebab)
# =============================
col_detail, col_penyebab = st.columns([2, 3])

# ===== Siapkan options dropdown (tampilan bagus)
opt_df = (
    risk_y[["kabkota_norm", "kabkota_display"]]
    .drop_duplicates()
    .sort_values("kabkota_display")
)
options_display = opt_df["kabkota_display"].tolist()
display_to_norm = dict(zip(opt_df["kabkota_display"], opt_df["kabkota_norm"]))
norm_to_display = dict(zip(opt_df["kabkota_norm"], opt_df["kabkota_display"]))

# Tentukan selected_norm dari klik atau dropdown
if clicked_name:
    clicked_norm = norm_kabkota(clicked_name)  # aman karena display_kabkota tetap nyimpen "KABUPATEN X" / "KOTA X"
    if clicked_norm in norm_to_display:
        selected_norm = clicked_norm
    else:
        # fallback kalau klik tidak cocok (jarang)
        chosen_display = st.selectbox("Pilih wilayah", options_display)
        selected_norm = display_to_norm[chosen_display]
else:
    chosen_display = st.selectbox("Pilih wilayah", options_display)
    selected_norm = display_to_norm[chosen_display]

with col_detail:
    st.subheader("Detail")

    info = risk_y[risk_y["kabkota_norm"] == selected_norm]
    if info.empty:
        st.info("Tidak ada data untuk wilayah yang dipilih.")
    else:
        st.write(f"**Wilayah:** {norm_to_display.get(selected_norm, selected_norm)}")
        if jenis is not None:
            st.write(f"**Jenis kematian:** {jenis}")
        st.write(f"**Risiko:** {info.iloc[0]['risk_label']}")
        st.write(f"**Total kematian:** {int(info.iloc[0]['total_kematian'])}")

with col_penyebab:
    st.subheader("Daftar Penyebab Kematian Teratas")

    tmp = detail.copy()
    tmp["kabkota_norm"] = tmp["nama_kabupaten_kota"].apply(norm_kabkota)

    d = tmp[(tmp["tahun"] == tahun) & (tmp["kabkota_norm"] == selected_norm)]
    if jenis is not None and "jenis_kematian" in tmp.columns:
        d = d[d["jenis_kematian"] == jenis]

    d = d.groupby("penyebab_kematian", as_index=False)["jumlah_kematian"].sum()
    d = d[d["jumlah_kematian"].fillna(0) > 0]

    if d.empty:
        st.info("Tidak ada data penyebab kematian untuk wilayah yang dipilih.")
    else:
        d = d.sort_values("jumlah_kematian", ascending=False).head(10)
        d = d.rename(columns={"penyebab_kematian": "Penyebab", "jumlah_kematian": "Jumlah"})
        d["Jumlah"] = d["Jumlah"].astype(int)
        st.dataframe(d, use_container_width=True, hide_index=True)


# =============================
# Inisialisasi Session State
# =============================
# Simpan filter saat ini untuk mendeteksi perubahan
current_filter = f"{tahun}_{jenis}_{selected_norm}"

if "last_filter" not in st.session_state:
    st.session_state.last_filter = current_filter

# Jika filter berubah (tahun/jenis/wilayah), reset status tombol
if st.session_state.last_filter != current_filter:
    st.session_state.rekomendasi_tampil = False
    st.session_state.hasil_gemini = ""
    st.session_state.last_filter = current_filter

if "rekomendasi_tampil" not in st.session_state:
    st.session_state.rekomendasi_tampil = False

# =============================
# Gemini Rekomendasi
# =============================
st.subheader("Rekomendasi Penanganan AI (Gemini)")

if not d.empty:
    # 1. Tampilkan tombol HANYA JIKA rekomendasi belum tampil
    if not st.session_state.rekomendasi_tampil:
        if st.button("Rekomendasi Penanganan"):
            with st.spinner("Gemini sedang membuat rekomendasi..."):
                try:
                    daftar_penyebab = ", ".join([f"{row['Penyebab']} ({row['Jumlah']} kasus)" for _, row in d.iterrows()])
                    wilayah_terpilih = norm_to_display.get(selected_norm, selected_norm)
                    label_risiko = info.iloc[0]['risk_label']

                    prompt_teks = f"""
                    Anda adalah seorang ahli kesehatan publik. 
                    Data Wilayah: {wilayah_terpilih} dengan risiko {label_risiko}.
                    Penyebab kematian tertinggi: {daftar_penyebab}.
                    Tugas: Berikan rekomendasi penanganan.
                    Aturan: Langsung mulai dari judul ## Langkah Penanganan Strategis dan ## Saran Pencegahan.
                    """

                    response = client.models.generate_content(
                        model="gemini-3-flash-preview",
                        contents=prompt_teks
                    )
                    
                    # Simpan hasil dan ubah status agar tombol hilang
                    st.session_state.hasil_gemini = response.text
                    st.session_state.rekomendasi_tampil = True
                    st.rerun() # Refresh untuk menghilangkan tombol
                    
                except Exception as e:
                    st.error(f"Terjadi kesalahan: {e}")

    # 2. Tampilkan hasil jika status sudah True
    if st.session_state.rekomendasi_tampil:
        st.markdown(st.session_state.hasil_gemini)
        
        st.divider()
        st.warning("⚠️ **Disclaimer:** Informasi ini dihasilkan oleh AI (Gemini) dan bukan merupakan pengganti saran medis profesional, diagnosis, atau kebijakan resmi pemerintah.")

else:
    st.info("Pilih wilayah yang memiliki data penyebab kematian untuk mendapatkan rekomendasi.")