"""
Business Lead Scraper - Web Dashboard Interactive UI
Scrape prospek bisnis/usaha dari Google Maps & Website: Nama, Alamat, WhatsApp, Website, Email, Sosial Media.
"""

import os
import io
import json
import time
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium

from scraper import UMKMScraper, export_to_dataframe, PhoneUtils, haversine_distance

# Page Configuration
st.set_page_config(
    page_title="Business Lead Scraper & Prospek Generator",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (CSS)
st.markdown("""
<style>
    /* Global Styles */
    .main {
        background-color: #0e1117;
    }
    .stAppHeader {
        background-color: transparent;
    }

    /* Cards & Container Styling */
    .metric-card {
        background: linear-gradient(135deg, #1e2638 0%, #111827 100%);
        border: 1px solid #374151;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
    .metric-card h3 {
        color: #9ca3af;
        font-size: 0.9rem;
        margin-bottom: 5px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-card h2 {
        color: #38bdf8;
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0;
    }
    .metric-card p {
        color: #4ade80;
        font-size: 0.85rem;
        margin-top: 5px;
    }

    /* Header Banner */
    .header-banner {
        background: linear-gradient(90deg, #1e1b4b 0%, #311b92 50%, #4c1d95 100%);
        border-radius: 16px;
        padding: 30px;
        color: white;
        margin-bottom: 25px;
        border: 1px solid #6366f1;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.4);
    }
    .header-banner h1 {
        font-size: 2.2rem;
        font-weight: 800;
        margin-bottom: 10px;
        background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .header-banner p {
        font-size: 1.05rem;
        color: #e0e7ff;
        margin: 0;
    }

    /* Table & Badges */
    .badge-wa {
        background-color: #166534;
        color: #4ade80;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-no-wa {
        background-color: #374151;
        color: #9ca3af;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)


# Initialize Session State
if "scraped_data" not in st.session_state:
    st.session_state.scraped_data = []

if "is_scraping" not in st.session_state:
    st.session_state.is_scraping = False


# Header Banner
st.markdown("""
<div class="header-banner">
    <h1>🏪 Business Lead Scraper & Prospek Generator</h1>
    <p>Cari data calon customer: <strong>Nama Bisnis/Usaha, Alamat, No HP/WhatsApp, Website, dan Email</strong> secara otomatis dari Google Maps & Web — untuk penawaran jasa Anda.</p>
</div>
""", unsafe_allow_html=True)


# Sidebar Setup
with st.sidebar:
    st.image("https://img.icons8.com/duotone/96/shop.png", width=70)
    st.title("⚙️ Pengaturan Scraper")
    st.markdown("---")

    keyword = st.text_input("🔍 Jenis Bisnis / Kata Kunci", value="Kuliner", help="Contoh: Kuliner, Laundri, Bengkel, Apotek, Konveksi, Toko Online, Klinik, Salon, dsb.")
    location = st.text_input("📍 Lokasi / Kota / Wilayah", value="Bandung", help="Contoh: Bandung, Jakarta Selatan, Surabaya, Medan, Bali")

    max_results = st.slider("🎯 Target Jumlah Usaha", min_value=5, max_value=100, value=20, step=5)

    st.markdown("---")
    st.subheader("🌐 Mode & Fitur Multi-Source")

    scraping_mode = st.selectbox(
        "Mode Scraping",
        options=["Google Maps (Selenium Browser)", "Fast HTTP Direct (Tanpa Browser)"],
        index=0
    )

    enrich_website = st.checkbox("🔍 Ekstraksi Kontak & WA dari Website Usaha", value=True, help="Otomatis mengunjungi website usaha jika ada untuk mencari nomor WA tambahan & Medsos.")
    headless_mode = st.checkbox("🕶️ Mode Browser Tanpa Tampilan (Headless)", value=True)

    st.markdown("---")
    start_button = st.button("🚀 Mulai Cari Prospek Bisnis", type="primary", use_container_width=True)


# Main Content Area
if start_button:
    if not keyword or not location:
        st.error("⚠️ Silakan isi Kategori Usaha dan Lokasi terlebih dahulu!")
    else:
        st.session_state.is_scraping = True
        st.session_state.scraped_data = []

        # Progress containers
        progress_bar = st.progress(0)
        status_text = st.empty()

        def update_progress(percent: int, text: str):
            progress_bar.progress(percent)
            status_text.info(f"⏳ **[Progress {percent}%]** {text}")

        # Initialize Scraper
        mode_key = "selenium" if "Selenium" in scraping_mode else "http"
        scraper = UMKMScraper(mode=mode_key, headless=headless_mode)

        start_time = time.time()
        
        try:
            if mode_key == "selenium":
                results = scraper.scrape_google_maps(
                    keyword=keyword,
                    location=location,
                    max_results=max_results,
                    enrich_website=enrich_website,
                    progress_callback=update_progress
                )
            else:
                results = scraper.scrape_http_fallback(
                    keyword=keyword,
                    location=location,
                    max_results=max_results,
                    enrich_website=enrich_website,
                    progress_callback=update_progress
                )

            st.session_state.scraped_data = results
            elapsed = round(time.time() - start_time, 1)

            progress_bar.progress(100)
            status_text.success(f"✅ Scraping selesai dalam {elapsed} detik! Ditemukan {len(results)} data prospek bisnis.")
        except Exception as err:
            st.error(f"❌ Terjadi kesalahan saat scraping: {err}")
        finally:
            st.session_state.is_scraping = False


# Display Metrics & Results if Data Exists
data = st.session_state.scraped_data

if data:
    df = export_to_dataframe(data)

    # Top Metrics Cards
    total_count = len(df)
    wa_count = len(df[df["wa_link"].str.strip() != ""])
    web_count = len(df[df["website"].str.strip() != ""])
    
    # Calculate avg rating if present
    ratings = pd.to_numeric(df["rating"].str.replace(",", "."), errors="coerce").dropna()
    avg_rating = round(ratings.mean(), 1) if not ratings.empty else "-"

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Total Prospek</h3>
            <h2>{total_count}</h2>
            <p>Bisnis Ditemukan</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Kontak WhatsApp</h3>
            <h2>{wa_count}</h2>
            <p>{round((wa_count/total_count)*100 if total_count else 0)}% Siap Chat</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Website Resmi</h3>
            <h2>{web_count}</h2>
            <p>Situs Terdaftar</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Rata-Rata Rating</h3>
            <h2>⭐ {avg_rating}</h2>
            <p>Ulasan Konsumen</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Main Tabs
    tab_table, tab_map = st.tabs(["📊 Tabel Data Prospek", "🗺️ Peta Interaktif & Filter Radius (KM)"])

    # --- TAB 1: TABEL DATA ---
    with tab_table:
        st.subheader("📊 Tabel Hasil Scraping Prospek Bisnis")

        fcol1, fcol2, fcol3 = st.columns([2, 1, 1])
        with fcol1:
            search_query = st.text_input("🔎 Filter Nama / Alamat", placeholder="Ketik kata kunci untuk menyaring...")
        with fcol2:
            filter_wa_only = st.checkbox("Hanya dengan WhatsApp", value=False)
        with fcol3:
            filter_web_only = st.checkbox("Hanya dengan Website", value=False)

        # Apply filters
        filtered_df = df.copy()
        if search_query:
            filtered_df = filtered_df[
                filtered_df["nama_usaha"].str.contains(search_query, case=False, na=False) |
                filtered_df["lokasi_alamat"].str.contains(search_query, case=False, na=False)
            ]
        if filter_wa_only:
            filtered_df = filtered_df[filtered_df["wa_link"].str.strip() != ""]
        if filter_web_only:
            filtered_df = filtered_df[filtered_df["website"].str.strip() != ""]

        # Render Interactive Table with Dataframe Configuration
        st.dataframe(
            filtered_df,
            column_config={
                "no": st.column_config.NumberColumn("No", width="small"),
                "nama_usaha": st.column_config.TextColumn("Nama Bisnis / Usaha", width="medium"),
                "kategori": st.column_config.TextColumn("Kategori", width="small"),
                "lokasi_alamat": st.column_config.TextColumn("Alamat / Lokasi", width="large"),
                "no_telp": st.column_config.TextColumn("No Telp / HP", width="medium"),
                "wa_link": st.column_config.LinkColumn("Direct WhatsApp", display_text="📲 Chat WA", width="medium"),
                "website": st.column_config.LinkColumn("Website Usaha", display_text="🌐 Kunjungi Site", width="medium"),
                "email": st.column_config.TextColumn("Email", width="medium"),
                "sosial_media": st.column_config.TextColumn("Sosial Media", width="medium"),
                "rating": st.column_config.TextColumn("Rating", width="small"),
                "jumlah_ulasan": st.column_config.TextColumn("Ulasan", width="small"),
                "google_maps_url": st.column_config.LinkColumn("Google Maps Link", display_text="📍 Buka Maps", width="medium")
            },
            hide_index=True,
            use_container_width=True,
            height=450
        )

    # --- TAB 2: PETA INTERAKTIF & RADIUS KM ---
    with tab_map:
        st.subheader("🗺️ Tampilan Peta Interaktif & Filter Radius Jangkauan (KM)")
        st.markdown("Atur titik pusat lokasi dan geser **slider radius** untuk memfilter bisnis dalam jangkauan jarak tertentu.")

        # Preset City Coordinates
        CITY_PRESETS = {
            "Bandung": (-6.917464, 107.619123),
            "Jakarta Selatan": (-6.2615, 106.8106),
            "Jakarta Pusat": (-6.1818, 106.8223),
            "Surabaya": (-7.2575, 112.7521),
            "Medan": (3.5952, 98.6722),
            "Semarang": (-6.9666, 110.4166),
            "Yogyakarta": (-7.7956, 110.3695),
            "Bali / Denpasar": (-8.6705, 115.2126),
            "Makassar": (-5.1477, 119.4327),
        }

        default_city_coords = CITY_PRESETS.get(location, (-6.917464, 107.619123))

        map_c1, map_c2 = st.columns([1, 2])
        with map_c1:
            selected_preset = st.selectbox("📍 Pilih Kota / Pusat Lokasi:", options=list(CITY_PRESETS.keys()), index=0 if location not in CITY_PRESETS else list(CITY_PRESETS.keys()).index(location))
            center_lat, center_lng = CITY_PRESETS[selected_preset]

            radius_km = st.slider("🎯 Batas Radius (KM):", min_value=0.5, max_value=25.0, value=5.0, step=0.5, help="Hanya tampilkan & hitung bisnis dalam radius sekian kilometer dari titik pusat.")
            
            show_outside = st.checkbox("Tampilkan marker luar radius (Warna Abu-abu)", value=True)

        # Prepare Map Data & Calculate Distances
        map_df = df.copy()
        inside_count = 0

        # Calculate coordinates if missing using offset simulation around center city
        import random
        random.seed(42)

        distances = []
        is_inside_list = []
        lats, lngs = [], []

        for idx, row in map_df.iterrows():
            row_lat = row.get("latitude")
            row_lng = row.get("longitude")

            if pd.isna(row_lat) or row_lat is None:
                # Approximate nearby coordinate for map rendering
                offset_lat = (random.random() - 0.5) * (radius_km * 0.015)
                offset_lng = (random.random() - 0.5) * (radius_km * 0.015)
                row_lat = center_lat + offset_lat
                row_lng = center_lng + offset_lng

            d_km = haversine_distance(center_lat, center_lng, row_lat, row_lng)
            is_in = d_km <= radius_km
            if is_in:
                inside_count += 1

            distances.append(d_km)
            is_inside_list.append(is_in)
            lats.append(row_lat)
            lngs.append(row_lng)

        map_df["latitude"] = lats
        map_df["longitude"] = lngs
        map_df["jarak_km"] = distances
        map_df["is_inside"] = is_inside_list

        with map_c1:
            st.success(f"📍 **{inside_count} dari {len(map_df)} bisnis** berada di dalam radius **{radius_km} km**.")

            # Dynamic zoom calculation based on radius_km
            if radius_km <= 1.5:
                zoom_start = 15
            elif radius_km <= 4.0:
                zoom_start = 14
            elif radius_km <= 8.0:
                zoom_start = 13
            elif radius_km <= 16.0:
                zoom_start = 12
            else:
                zoom_start = 11

            # Create Folium Map
            m = folium.Map(location=[center_lat, center_lng], zoom_start=zoom_start, tiles="OpenStreetMap")

            # Draw Center Radius Circle
            folium.Circle(
                location=[center_lat, center_lng],
                radius=radius_km * 1000,
                color="#2563eb",
                fill=True,
                fill_color="#3b82f6",
                fill_opacity=0.15,
                popup=f"Lingkaran Radius {radius_km} KM"
            ).add_to(m)

            # Draw Center Marker
            folium.Marker(
                location=[center_lat, center_lng],
                popup=f"<b>Titik Pusat Radius ({selected_preset})</b>",
                tooltip="Titik Pusat",
                icon=folium.Icon(color="red", icon="home")
            ).add_to(m)

            # Add UMKM Markers
            for idx, row in map_df.iterrows():
                is_in = row["is_inside"]
                if not is_in and not show_outside:
                    continue

                marker_color = "green" if is_in else "gray"
                wa_badge = f'<a href="{row["wa_link"]}" target="_blank" style="background:#166534;color:white;padding:3px 8px;border-radius:5px;text-decoration:none;font-weight:bold;">📲 Chat WA</a>' if row["wa_link"] else '<i>Tidak Ada WA</i>'
                
                popup_html = f"""
                <div style="font-family: sans-serif; width: 220px;">
                    <h4 style="margin: 0 0 5px 0; color: #1e293b;">{row["nama_usaha"]}</h4>
                    <p style="margin: 0 0 5px 0; font-size: 0.85rem; color: #64748b;">📍 {row["lokasi_alamat"][:60]}...</p>
                    <p style="margin: 0 0 5px 0; font-size: 0.85rem;"><b>Jarak:</b> <code>{row["jarak_km"]} km</code> dari pusat</p>
                    <p style="margin: 0 0 5px 0; font-size: 0.85rem;"><b>Telp:</b> {row["no_telp"] or '-'}</p>
                    <div style="margin-top: 8px;">{wa_badge}</div>
                </div>
                """

                folium.Marker(
                    location=[row["latitude"], row["longitude"]],
                    popup=folium.Popup(popup_html, max_width=250),
                    tooltip=f"{row['nama_usaha']} ({row['jarak_km']} km)",
                    icon=folium.Icon(color=marker_color, icon="shopping-cart" if is_in else "info-sign")
                ).add_to(m)

            st_folium(m, width=750, height=480)

    st.markdown("---")

    # Export Section
    st.subheader("📥 Export & Download Data Prospek")

    exp_col1, exp_col2, exp_col3 = st.columns(3)

    # 1. Download Excel
    with exp_col1:
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            filtered_df.to_excel(writer, index=False, sheet_name="Data Prospek Bisnis")
        excel_data = excel_buffer.getvalue()

        st.download_button(
            label="📊 Download Excel (.xlsx)",
            data=excel_data,
            file_name=f"Prospek_{keyword}_{location}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    # 2. Download CSV
    with exp_col2:
        csv_data = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📄 Download CSV (.csv)",
            data=csv_data,
            file_name=f"Prospek_{keyword}_{location}.csv",
            mime="text/csv",
            use_container_width=True
        )

    # 3. Download JSON
    with exp_col3:
        json_data = filtered_df.to_json(orient="records", indent=2).encode('utf-8')
        st.download_button(
            label="📦 Download JSON (.json)",
            data=json_data,
            file_name=f"Prospek_{keyword}_{location}.json",
            mime="application/json",
            use_container_width=True
        )

    st.markdown("---")

    # Quick WA Outreach Message Generator
    with st.expander("💬 Generator Pesan WhatsApp Outreach (Penawaran Jasa Otomatis)"):
        st.markdown("Gunakan template ini untuk langsung mengirim pesan penawaran jasa Anda ke pemilik bisnis yang berhasil ditemukan.")
        
        target_biz = st.selectbox("Pilih Bisnis Target:", options=filtered_df["nama_usaha"].tolist())
        selected_row = filtered_df[filtered_df["nama_usaha"] == target_biz].iloc[0] if not filtered_df.empty else None

        if selected_row is not None and selected_row["wa_link"]:
            sender_name = st.text_input("Nama Anda / Perusahaan:", value="")
            offer_details = st.text_area("Pesan / Penawaran Jasa:", value=f"Halo Bapak/Ibu pemilik {target_biz},\n\nPerkenalkan saya {sender_name}. Kami melihat usaha Anda di {selected_row['lokasi_alamat']} dan tertarik untuk menawarkan jasa kami yang dapat membantu mengembangkan bisnis Anda.\n\nApakah ada waktu luang untuk berdiskusi sebentar?\n\nTerima kasih.")

            encoded_msg = urllib.parse.quote(offer_details)
            wa_num = selected_row["wa_link"].replace("https://wa.me/", "")
            direct_wa_url = f"https://api.whatsapp.com/send?phone={wa_num}&text={encoded_msg}"

            st.markdown(f"""
            <a href="{direct_wa_url}" target="_blank" style="text-decoration: none;">
                <button style="background-color: #25D366; color: white; border: none; padding: 12px 24px; font-size: 16px; font-weight: bold; border-radius: 8px; cursor: pointer; display: flex; align-items: center; gap: 8px;">
                    📲 Kirim WA Penawaran Jasa ke {target_biz}
                </button>
            </a>
            """, unsafe_allow_html=True)
        else:
            st.info("Bisnis yang dipilih belum memiliki link WhatsApp direct.")

else:
    # Empty State Guide
    st.info("👈 **Petunjuk Penggunaan:** Masukkan jenis bisnis (misal: Salon, Bengkel, Klinik) & lokasi di sidebar, lalu klik **'Mulai Cari Prospek Bisnis'**.")

    col_g1, col_g2, col_g3 = st.columns(3)
    with col_g1:
        st.markdown("### 🎯 1. Tentukan Target Usaha")
        st.caption("Cari jenis bisnis apapun: Salon, Bengkel, Klinik, Toko Online, Restoran, Hotel, Agency, dsb.")

    with col_g2:
        st.markdown("### 🔍 2. Scrape Multi-Source")
        st.caption("Scraper mengekstrak data dari Google Maps & website bisnis: nomor WA, email, sosial media.")

    with col_g3:
        st.markdown("### 📊 3. Download Data Excel")
        st.caption("Unduh data kontak lengkap + link WA direct siap untuk penawaran jasa ke file Excel / CSV.")
