"""
UMKM Scraper CLI - Command Line Tool
Run UMKM scraping directly from terminal with custom arguments and automatic file export.
"""

import argparse
import sys
import os
import logging
from scraper import UMKMScraper, export_to_dataframe

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def main():
    parser = argparse.ArgumentParser(description="UMKM Lead Scraper & Contact Generator Indonesia")
    parser.add_argument("-k", "--keyword", type=str, default="Kuliner", help="Kategori / Kata kunci usaha (Contoh: Kuliner, Laundri, Konveksi)")
    parser.add_argument("-l", "--location", type=str, default="Bandung", help="Lokasi / Kota / Wilayah (Contoh: Bandung, Jakarta Selatan)")
    parser.add_argument("-m", "--max", type=int, default=20, help="Jumlah target usaha yang ingin di-scrape (default: 20)")
    parser.add_argument("--mode", type=str, choices=["selenium", "http"], default="selenium", help="Mode scraping: 'selenium' (Google Maps) atau 'http' (Fast HTTP)")
    parser.add_argument("-o", "--output", type=str, default="umkm_result.xlsx", help="Nama file hasil output (Contoh: hasil.xlsx atau hasil.csv)")
    parser.add_argument("--headful", action="store_true", help="Tampilkan jendela browser saat scraping berlangsung (default: headless)")
    parser.add_argument("--no-enrich", action="store_true", help="Matikan ekstraksi kontak mendalam dari website usaha")

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print(" 🏪 UMKM SCRAPER & LEAD GENERATOR INDONESIA ")
    print("=" * 60)
    print(f" 🔍 Kata Kunci  : {args.keyword}")
    print(f" 📍 Lokasi      : {args.location}")
    print(f" 🎯 Target Count: {args.max}")
    print(f" 🌐 Mode        : {args.mode.upper()}")
    print(f" 📁 File Output : {args.output}")
    print("=" * 60 + "\n")

    headless = not args.headful
    enrich_website = not args.no_enrich

    def cli_progress(percent, msg):
        print(f"[{percent:3d}%] {msg}")

    scraper = UMKMScraper(mode=args.mode, headless=headless)
    
    if args.mode == "selenium":
        data = scraper.scrape_google_maps(
            keyword=args.keyword,
            location=args.location,
            max_results=args.max,
            enrich_website=enrich_website,
            progress_callback=cli_progress
        )
    else:
        data = scraper.scrape_http_fallback(
            keyword=args.keyword,
            location=args.location,
            max_results=args.max,
            enrich_website=enrich_website,
            progress_callback=cli_progress
        )

    if not data:
        print("\n❌ Tidak ada data UMKM yang ditemukan.")
        sys.exit(0)

    df = export_to_dataframe(data)
    output_filename = args.output

    if output_filename.endswith(".xlsx"):
        df.to_excel(output_filename, index=False)
    elif output_filename.endswith(".json"):
        df.to_json(output_filename, orient="records", indent=2)
    else:
        if not output_filename.endswith(".csv"):
            output_filename += ".csv"
        df.to_csv(output_filename, index=False)

    print(f"\n✅ Berhasil! Total {len(df)} data UMKM disimpan ke: {os.path.abspath(output_filename)}")
    print("\nRingkasan Data Scrape:")
    print(df[["no", "nama_usaha", "no_telp", "wa_link", "website"]].head(10).to_string(index=False))


if __name__ == "__main__":
    main()
