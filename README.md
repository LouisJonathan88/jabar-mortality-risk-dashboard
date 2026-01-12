# K-Means Mortality Clustering Recommendation System

Sistem rekomendasi pencegahan penyebab kematian berbasis **clustering K-Means** menggunakan data **Open Data Jawa Barat**.  
Aplikasi ini mengelompokkan kabupaten/kota berdasarkan kemiripan pola penyebab kematian dan memberikan **rekomendasi pencegahan** sesuai tingkat risiko.

## 📊 Dataset
Dataset yang digunakan berasal dari **Open Data Jawa Barat**.

- Sumber: https://opendata.jabarprov.go.id/id/dataset/jumlah-kematian-berdasarkan-jenis-dan-penyebab-kematian-di-jawa-barat

## 🚀 Cara Menjalankan Aplikasi
1. Clone repository:
   ```bash
   git clone https://github.com/LouisJonathan88/kmeans-mortality-clustering-recommendation.git

   cd kmeans-mortality-clustering-recommendation
    ```
2. Install dependencies:
   ```bash
    pip install -r requirements.txt
    ```
3. Jalankan aplikasi:
    ```bash
     streamlit run app.py
     ```

# Jabar Mortality Risk Dashboard

Dashboard interaktif untuk **visualisasi risiko kematian kabupaten/kota di Provinsi Jawa Barat** berbasis **peta spasial (choropleth)** dan **rekomendasi penanganan berbasis AI (Gemini)**.

Aplikasi ini membantu pengguna memahami **pola risiko kematian**, **penyebab kematian dominan**, serta memberikan **rekomendasi strategis pencegahan** berdasarkan data historis kesehatan.

---

## Tujuan Sistem
- Memvisualisasikan **tingkat risiko kematian** kabupaten/kota di Jawa Barat
- Menampilkan **penyebab kematian tertinggi** pada setiap wilayah
- Memberikan **rekomendasi penanganan otomatis berbasis AI**

---

## Fitur 
- **Peta Risiko Kematian**
- **Clustering Risiko Wilayah** 
- **Detail Wilayah & Total Kematian**
- **Daftar Penyebab Kematian Teratas**
- **Rekomendasi Penanganan Berbasis AI (Google Gemini)**
- **Filter Tahun & Jenis Kematian**
---

## Dataset
Dataset bersumber dari **Open Data Jawa Barat**:

- **Jumlah Kematian Berdasarkan Jenis dan Penyebab Kematian di Jawa Barat**  
  https://opendata.jabarprov.go.id/id/dataset/jumlah-kematian-berdasarkan-jenis-dan-penyebab-kematian-di-jawa-barat

Data telah melalui proses **pembersihan, agregasi, dan pengelompokan risiko** sebelum digunakan dalam aplikasi.

---

## Teknologi yang Digunakan
- **Python**
- **Streamlit**
- **Pandas**
- **Folium**
- **Google Gemini API**
- **GeoJSON (Wilayah Jawa Barat)**

---

## Cara Menjalankan Aplikasi

1. Clone repository:
   ```bash
   git clone https://github.com/LouisJonathan88/kmeans-mortality-clustering-recommendation.git

   cd kmeans-mortality-clustering-recommendation
    ```
2. Install dependencies:
   ```bash
    pip install -r requirements.txt
    ```
3. Konfigurasi API Key (membuat file .env)
    ```bash
    api_gemini=YOUR_API_KEY_HERE
    ```
3. Jalankan aplikasi:
    ```bash
     streamlit run app.py
     ```

