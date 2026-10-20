# 🗺️ Otomatisasi Pelaporan Aset Kota (Smart City Asset Management) dengan Python & GeoPandas

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![GeoPandas](https://img.shields.io/badge/GeoPandas-Spatial%20Processing-green)
![Format](https://img.shields.io/badge/Output-GeoJSON-orange)
![Domain](https://img.shields.io/badge/Domain-Smart%20City%20GIS-lightgrey)

Proyek portofolio GIS yang mengotomatisasi pemrosesan **laporan warga tentang kondisi aset publik** (pohon, taman, lampu jalan, jalan raya). Skrip Python mengubah data tabular (CSV) menjadi **data spasial**, menyaring **laporan kritis**, lalu mengekspornya ke **GeoJSON** yang siap ditampilkan di sistem WebGIS.

Terinspirasi konsep aplikasi pelaporan masalah tata kota seperti **"Snap Send Solve"** (Selandia Baru): warga melapor, laporan diproses secara spasial, dan tim pemeliharaan segera ditugaskan.

> ⚠️ **Catatan:** Seluruh data dan koordinat adalah **data dummy fiktif** untuk demonstrasi.

---

## 📑 Daftar Isi
1. [Business Understanding](#1--business-understanding)
2. [The IT Advantage in GIS](#2--the-it-advantage-in-gis)
3. [Seamless Cloud Integration Concept](#3--seamless-cloud-integration-concept)
4. [Alur Kerja Pipeline](#4--alur-kerja-pipeline)
5. [Cara Menjalankan Kode](#5--cara-menjalankan-kode)
6. [Struktur Repositori](#6--struktur-repositori)

---

## 1. 🎯 Business Understanding

### Masalah
Pemerintah kota mengelola ribuan aset publik. Laporan warga datang dari banyak kanal dalam format tidak seragam, sehingga:
- Laporan darurat (misalnya pohon tumbang atau kabel lampu terbuka) **tenggelam** di antara laporan ringan.
- Tim pemeliharaan sulit menentukan **lokasi dan prioritas** penugasan.
- Pelaporan manajemen aset memakan waktu karena direkap manual.

### Peran Integrasi GIS
| Kebutuhan | Kontribusi GIS |
|---|---|
| Merespons keluhan lebih cepat | Setiap laporan memiliki **koordinat**, sehingga langsung dapat dipetakan |
| Prioritas penugasan | Laporan **Urgensi Tinggi** dan **Open** otomatis dipisahkan |
| Efisiensi rute tim lapangan | Titik kritis terlihat berkelompok di peta, sehingga dapat dikunjungi dalam satu rute |
| Transparansi | Warga dan pimpinan dapat melihat status penanganan pada dasbor peta |
| Perencanaan pemeliharaan | Analisis jenis aset yang paling sering bermasalah |

---

## 2. 💻 The IT Advantage in GIS

Memproses data spasial dengan skrip Python/GeoPandas memberi keunggulan dibanding pengolahan manual di perangkat lunak desktop konvensional:

| Aspek | Cara Manual (Desktop) | Skrip Python (GeoPandas) |
|---|---|---|
| **Konsistensi** | Bergantung pada ketelitian operator | Aturan filter ditulis sekali dan **dijalankan identik setiap saat** |
| **Risiko human-error** | Salah ketik koordinat, salah pilih filter, lupa langkah | **Berkurang signifikan**: ada validasi kolom dan koordinat otomatis |
| **Skalabilitas** | Melambat saat data ribuan hingga jutaan baris | Memproses data besar dengan kode yang sama |
| **Kecepatan** | Menit hingga jam per siklus pelaporan | Hitungan detik, dapat dijadwalkan otomatis |
| **Reprodusibilitas** | Sulit melacak ulang langkah yang diklik | Kode dapat **di-versioning** dengan Git dan diaudit |
| **Integrasi** | Ekspor manual per kali | Dapat disambungkan ke pipeline, API, dan cron/CI |

> 💡 Otomatisasi mengurangi kesalahan prosedural, tetapi **kualitas data masukan tetap menentukan hasil**. Karena itu skrip menyertakan validasi kolom dan rentang koordinat.

---

## 3. ☁️ Seamless Cloud Integration Concept

Keluaran skrip, `laporan_kritis_terbaru.geojson`, memakai format **GeoJSON** (standar terbuka, CRS WGS84/EPSG:4326) sehingga dapat langsung dikonsumsi oleh berbagai platform:

```
 Laporan Warga (CSV)
        │
        ▼
 Python + GeoPandas  ──►  laporan_kritis_terbaru.geojson
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        ▼                          ▼                          ▼
   ArcGIS Online                 QGIS                  WebGIS open-source
 (tambah layer GeoJSON)    (Add Vector Layer)         (Leaflet / MapLibre)
```

**Pola integrasi:**
- **ArcGIS Online:** GeoJSON dapat ditambahkan sebagai layer ke peta web. Untuk otomatisasi penuh, dapat dikembangkan memakai ArcGIS API for Python.
- **QGIS:** buka langsung sebagai layer vektor, atau muat dari URL.
- **Platform cloud open-source:** pustaka seperti Leaflet dan MapLibre membaca GeoJSON secara native lewat `fetch()`.
- **Pembaruan berkala:** skrip dapat dijadwalkan (cron atau GitHub Actions), lalu file GeoJSON terbaru diunggah ke penyimpanan cloud atau endpoint yang dibaca dasbor, sehingga peta selalu menampilkan kondisi terkini.

**Contoh struktur fitur pada GeoJSON:**

```json
{
  "type": "Feature",
  "properties": {
    "ID_Laporan": "LP-2025-025",
    "Kategori_Aset": "Pohon",
    "Urgensi": "Tinggi",
    "Status_Penanganan": "Open"
  },
  "geometry": { "type": "Point", "coordinates": [106.8212, -6.2147] }
}
```

> ℹ️ GitHub menampilkan berkas `.geojson` sebagai peta interaktif langsung di halaman repositori.

---

## 4. 🔄 Alur Kerja Pipeline

1. **Load** : membaca CSV laporan warga.
2. **Validate** : memeriksa kolom wajib dan rentang koordinat.
3. **Convert** : DataFrame → GeoDataFrame (`shapely.geometry.Point`, EPSG:4326).
4. **Filter** : `Urgensi == "Tinggi"` dan `Status_Penanganan == "Open"`, diurutkan dari yang terbaru.
5. **Export** : menulis `laporan_kritis_terbaru.geojson`.
6. **Summarize** : mencetak jumlah laporan kritis per kategori aset di terminal.

---

## 5. ▶️ Cara Menjalankan Kode

```bash
# 1. Clone repositori
git clone https://github.com/<username>/<nama-repositori>.git
cd <nama-repositori>

# 2. (Opsional) Buat virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Instal dependensi
pip install -r requirements.txt

# 4. Jalankan skrip
python gis_asset_automation.py
```

**Keluaran:**
- Ringkasan analitik di terminal.
- File `laporan_kritis_terbaru.geojson`, yang bisa langsung dibuka di QGIS, diunggah ke ArcGIS Online, atau dilihat di GitHub.

> 🛠️ Jika instalasi GeoPandas bermasalah di Windows, gunakan `conda install -c conda-forge geopandas`.

---

## 6. 📁 Struktur Repositori

```
├── data_laporan_aset_kota.csv       # Data dummy laporan warga (25 baris)
├── gis_asset_automation.py          # Skrip pemrosesan spasial
├── laporan_kritis_terbaru.geojson   # Hasil (dibuat setelah skrip dijalankan)
├── requirements.txt                 # Dependensi Python
└── README.md                        # Dokumentasi proyek
```

---

## 🚀 Pengembangan Lanjutan
- **Analisis spasial:** pengelompokan titik kritis (clustering) dan peta panas (heatmap).
- **Spatial join** dengan batas kelurahan untuk membagi tugas per wilayah.
- **Pembaruan otomatis** terjadwal dengan GitHub Actions.
- **Dasbor interaktif** dengan Folium atau Streamlit.
- Hitung **SLA** (selisih hari sejak laporan) untuk menandai laporan yang terlambat ditangani.
