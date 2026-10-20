"""
Otomatisasi Pemrosesan Data Pelaporan Aset Kota (Smart City Asset Management)
=============================================================================
Alur kerja:
  1. Muat laporan warga (CSV tabular).
  2. Validasi kolom dan koordinat.
  3. Ubah DataFrame -> GeoDataFrame (data spasial) dari Latitude/Longitude.
  4. Filter otomatis: laporan Urgensi "Tinggi" dan Status "Open".
  5. Ekspor ke GeoJSON untuk WebGIS / Cloud GIS.
  6. Cetak ringkasan analitik ke terminal.

Terinspirasi konsep pelaporan masalah tata kota seperti "Snap Send Solve".
"""

# ---------------------------------------------------------------
# 1. IMPORT LIBRARY
# ---------------------------------------------------------------
import sys
from pathlib import Path

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

# ---------------------------------------------------------------
# 2. KONFIGURASI
# ---------------------------------------------------------------
FILE_INPUT = Path("data_laporan_aset_kota.csv")
FILE_OUTPUT = Path("laporan_kritis_terbaru.geojson")

# WGS84 (EPSG:4326): sistem koordinat lat/long standar GPS dan GeoJSON
CRS_WGS84 = "EPSG:4326"

URGENSI_TARGET = "Tinggi"
STATUS_TARGET = "Open"

KOLOM_WAJIB = [
    "ID_Laporan", "Tanggal_Laporan", "Kategori_Aset", "Deskripsi_Masalah",
    "Urgensi", "Latitude", "Longitude", "Status_Penanganan",
]


# ---------------------------------------------------------------
# 3. MEMUAT & MEMBERSIHKAN DATA
# ---------------------------------------------------------------
def muat_data(path: Path) -> pd.DataFrame:
    """Muat CSV laporan warga dan pastikan strukturnya benar."""
    if not path.exists():
        sys.exit(f"[ERROR] File tidak ditemukan: {path}")

    df = pd.read_csv(path)

    # Validasi kolom: gagal cepat jika struktur data tidak sesuai
    kolom_hilang = [k for k in KOLOM_WAJIB if k not in df.columns]
    if kolom_hilang:
        sys.exit(f"[ERROR] Kolom wajib tidak ada: {kolom_hilang}")

    # Rapikan teks (hapus spasi berlebih) agar filter tidak meleset
    for kolom in ["Kategori_Aset", "Urgensi", "Status_Penanganan"]:
        df[kolom] = df[kolom].astype(str).str.strip()

    # Ubah teks tanggal menjadi tipe datetime
    df["Tanggal_Laporan"] = pd.to_datetime(df["Tanggal_Laporan"], errors="coerce")

    # Pastikan koordinat bertipe numerik
    df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")
    df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")
    return df


def validasi_koordinat(df: pd.DataFrame) -> pd.DataFrame:
    """Buang baris dengan koordinat kosong atau di luar rentang valid."""
    valid = (
        df["Latitude"].between(-90, 90) & df["Longitude"].between(-180, 180)
    )  # NaN otomatis bernilai False
    jumlah_buang = int((~valid).sum())
    if jumlah_buang:
        print(f"[PERINGATAN] {jumlah_buang} baris dibuang karena koordinat tidak valid.")
    return df[valid].copy()


# ---------------------------------------------------------------
# 4. KONVERSI TABULAR -> SPASIAL
# ---------------------------------------------------------------
def buat_geodataframe(df: pd.DataFrame) -> gpd.GeoDataFrame:
    """Setiap baris menjadi titik (Point) di peta."""
    # PERHATIAN: Point menerima urutan (x, y) = (LONGITUDE, LATITUDE)
    geometri = [Point(lon, lat) for lon, lat in zip(df["Longitude"], df["Latitude"])]
    return gpd.GeoDataFrame(df, geometry=geometri, crs=CRS_WGS84)


# ---------------------------------------------------------------
# 5. FILTERING OTOMATIS
# ---------------------------------------------------------------
def filter_laporan_kritis(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Ambil hanya laporan Urgensi Tinggi dan Status Open, terbaru di atas."""
    mask = (gdf["Urgensi"] == URGENSI_TARGET) & (gdf["Status_Penanganan"] == STATUS_TARGET)
    return gdf[mask].sort_values("Tanggal_Laporan", ascending=False).copy()


# ---------------------------------------------------------------
# 6. EKSPOR KE GEOJSON
# ---------------------------------------------------------------
def ekspor_geojson(gdf: gpd.GeoDataFrame, path: Path) -> None:
    """Simpan ke GeoJSON (standar RFC 7946) untuk WebGIS/Cloud GIS."""
    hasil = gdf.copy()
    # Datetime diubah ke teks agar aman diserialisasi ke JSON
    hasil["Tanggal_Laporan"] = hasil["Tanggal_Laporan"].dt.strftime("%Y-%m-%d")
    hasil.to_file(path, driver="GeoJSON")


# ---------------------------------------------------------------
# 7. RINGKASAN ANALITIK
# ---------------------------------------------------------------
def cetak_ringkasan(gdf_semua: gpd.GeoDataFrame, gdf_kritis: gpd.GeoDataFrame) -> None:
    total, kritis = len(gdf_semua), len(gdf_kritis)
    persen = (kritis / total * 100) if total else 0

    print("=" * 60)
    print(" RINGKASAN LAPORAN ASET KOTA - SMART CITY")
    print("=" * 60)
    print(f"Total laporan masuk        : {total}")
    print(f"Laporan kritis (Tinggi+Open): {kritis} ({persen:.1f}%)")

    print("\nDistribusi status penanganan (semua laporan):")
    print(gdf_semua["Status_Penanganan"].value_counts().to_string())

    if kritis == 0:
        print("\nTidak ada laporan kritis saat ini.")
        return

    print("\nJumlah laporan kritis per kategori aset:")
    per_kategori = gdf_kritis["Kategori_Aset"].value_counts()
    for kategori, jumlah in per_kategori.items():
        print(f"  {kategori:<12} {'#' * jumlah} {jumlah}")

    print("\nDaftar laporan kritis (terbaru di atas):")
    for _, r in gdf_kritis.iterrows():
        print(
            f"  {r['ID_Laporan']} | {r['Tanggal_Laporan']:%Y-%m-%d} | "
            f"{r['Kategori_Aset']:<11} | {r['Deskripsi_Masalah']} "
            f"({r['Latitude']:.4f}, {r['Longitude']:.4f})"
        )

    minx, miny, maxx, maxy = gdf_kritis.total_bounds
    print(f"\nBounding box area kritis (lon/lat): "
          f"[{minx:.4f}, {miny:.4f}] - [{maxx:.4f}, {maxy:.4f}]")


# ---------------------------------------------------------------
# 8. PROGRAM UTAMA
# ---------------------------------------------------------------
def main() -> None:
    df = muat_data(FILE_INPUT)
    df = validasi_koordinat(df)

    gdf = buat_geodataframe(df)
    print(f"[OK] {len(gdf)} laporan dikonversi ke GeoDataFrame (CRS: {gdf.crs}).\n")

    gdf_kritis = filter_laporan_kritis(gdf)

    if len(gdf_kritis) > 0:
        ekspor_geojson(gdf_kritis, FILE_OUTPUT)
        print(f"[OK] {len(gdf_kritis)} laporan kritis diekspor ke '{FILE_OUTPUT}'.\n")
    else:
        print("[INFO] Tidak ada laporan kritis, file GeoJSON tidak dibuat.\n")

    cetak_ringkasan(gdf, gdf_kritis)


if __name__ == "__main__":
    main()
