// Business Lead Scraper - Google Maps Radius & Realtime Circle Overlay Extension
(function () {
  console.log("🏪 Business Lead Scraper Extension active.");

  if (document.getElementById("gmaps-radius-widget")) return;

  // ========== 1. SVG CIRCLE OVERLAY ==========
  let svgOverlay = document.getElementById("gmaps-radius-svg-overlay");
  if (!svgOverlay) {
    svgOverlay = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svgOverlay.id = "gmaps-radius-svg-overlay";
    svgOverlay.style.cssText = `position:fixed;top:0;left:0;width:100vw;height:100vh;pointer-events:none;z-index:99999;display:block;`;

    const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    circle.id = "gmaps-radius-circle";
    circle.setAttribute("fill", "rgba(56,189,248,0.18)");
    circle.setAttribute("stroke", "#38bdf8");
    circle.setAttribute("stroke-width", "3");
    circle.setAttribute("stroke-dasharray", "8,6");
    circle.style.transition = "r 0.08s ease-out, cx 0.2s, cy 0.2s";

    const centerDot = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    centerDot.id = "gmaps-center-dot";
    centerDot.setAttribute("r", "6");
    centerDot.setAttribute("fill", "#ef4444");
    centerDot.setAttribute("stroke", "#fff");
    centerDot.setAttribute("stroke-width", "2");

    const radiusLabel = document.createElementNS("http://www.w3.org/2000/svg", "text");
    radiusLabel.id = "gmaps-radius-svg-label";
    radiusLabel.setAttribute("text-anchor", "middle");
    radiusLabel.setAttribute("fill", "#fff");
    radiusLabel.setAttribute("font-size", "14px");
    radiusLabel.setAttribute("font-weight", "bold");
    radiusLabel.setAttribute("font-family", "sans-serif");
    radiusLabel.style.textShadow = "0 2px 4px rgba(0,0,0,0.8)";
    radiusLabel.textContent = "🎯 3.0 KM";

    svgOverlay.appendChild(circle);
    svgOverlay.appendChild(centerDot);
    svgOverlay.appendChild(radiusLabel);
    document.body.appendChild(svgOverlay);
  }

  // ========== 2. WIDGET ==========
  const widget = document.createElement("div");
  widget.id = "gmaps-radius-widget";
  widget.innerHTML = `
    <h4>🏪 Business Lead Scraper</h4>
    <div style="margin-bottom:10px;">
      <button id="btn-my-location" style="width:100%;background:linear-gradient(135deg,#f59e0b,#d97706);border:none;color:#fff;padding:9px 12px;border-radius:8px;font-size:12px;font-weight:700;cursor:pointer;">
        📍 Deteksi Lokasi Saya (GPS)
      </button>
      <div id="location-info" style="font-size:10px;color:#94a3b8;margin-top:5px;display:none;"></div>
    </div>
    <div style="margin-bottom:10px;">
      <label style="font-size:12px;color:#94a3b8;">🔍 Cari Bisnis di Sekitar:</label>
      <div style="display:flex;gap:6px;margin-top:4px;">
        <input type="text" id="search-keyword" placeholder="Contoh: Salon, Bengkel, Klinik..." style="flex:1;background:#1e293b;border:1px solid #475569;color:#fff;padding:6px 8px;border-radius:6px;font-size:12px;">
        <button id="btn-search-nearby" style="background:#2563eb;border:none;color:#fff;padding:6px 10px;border-radius:6px;font-size:12px;font-weight:600;cursor:pointer;">Cari</button>
      </div>
    </div>
    <div class="radius-control">
      <label for="radius-range" style="font-size:12px;color:#94a3b8;">Batas Radius: <strong id="radius-val" style="color:#38bdf8;font-size:16px;">3.0</strong> KM</label>
      <input type="range" id="radius-range" min="0.5" max="25" step="0.5" value="3.0">
    </div>
    <div class="btn-group">
      <button id="btn-toggle-circle">🔵 Toggle Bulatan Radius</button>
      <button id="btn-scrape-visible" style="background:linear-gradient(135deg,#475569,#334155);">⚡ Ekstrak Cepat (Tanpa Nomor)</button>
      <button id="btn-bot-scrape" class="btn-export">🤖 AUTO-BOT: Ekstrak Semua + Nomor WA</button>
    </div>
    <div id="radius-status" class="status-info">⚡ Langkah: 1) Cari bisnis dulu → 2) Scroll hasil ke bawah → 3) Klik Auto-Bot</div>
  `;
  document.body.appendChild(widget);

  const radiusRange = document.getElementById("radius-range");
  const radiusVal = document.getElementById("radius-val");
  const statusDiv = document.getElementById("radius-status");
  const btnToggle = document.getElementById("btn-toggle-circle");
  const btnScrape = document.getElementById("btn-scrape-visible");
  const btnBotScrape = document.getElementById("btn-bot-scrape");
  const btnMyLocation = document.getElementById("btn-my-location");
  const btnSearchNearby = document.getElementById("btn-search-nearby");
  const searchKeyword = document.getElementById("search-keyword");
  const locationInfo = document.getElementById("location-info");
  const circleEl = document.getElementById("gmaps-radius-circle");

  let circleVisible = true;
  let myLat = null, myLng = null;

  // ========== 3. REALTIME CIRCLE ==========
  const updateCircle = (km) => {
    svgOverlay.style.display = circleVisible ? "block" : "none";
    const sidebar = document.querySelector("div.w6VYqd, div#pane");
    const sw = (sidebar && sidebar.offsetWidth < 600) ? sidebar.offsetWidth : 400;
    const cx = sw + (window.innerWidth - sw) / 2;
    const cy = window.innerHeight / 2;
    const r = Math.min(Math.max(km * 35, 20), 600);
    if (circleEl) { circleEl.setAttribute("cx", cx); circleEl.setAttribute("cy", cy); circleEl.setAttribute("r", r); }
    const dot = document.getElementById("gmaps-center-dot");
    if (dot) { dot.setAttribute("cx", cx); dot.setAttribute("cy", cy); }
    const lbl = document.getElementById("gmaps-radius-svg-label");
    if (lbl) { lbl.setAttribute("x", cx); lbl.setAttribute("y", cy - 15); lbl.textContent = `🎯 ${km.toFixed(1)} KM`; }
  };

  updateCircle(3.0);
  window.addEventListener("resize", () => updateCircle(parseFloat(radiusRange.value)));
  radiusRange.addEventListener("input", (e) => {
    const km = parseFloat(e.target.value);
    radiusVal.textContent = km.toFixed(1);
    circleVisible = true;
    updateCircle(km);
    statusDiv.textContent = `🔵 Radius ${km.toFixed(1)} KM`;
    statusDiv.style.color = "#38bdf8";
  });
  btnToggle.addEventListener("click", () => {
    circleVisible = !circleVisible;
    svgOverlay.style.display = circleVisible ? "block" : "none";
    btnToggle.textContent = circleVisible ? "🔵 Sembunyikan Bulatan" : "🔵 Tampilkan Bulatan";
  });

  // ========== 4. GEOLOCATION ==========
  btnMyLocation.addEventListener("click", () => {
    if (!navigator.geolocation) { statusDiv.textContent = "❌ Browser tidak mendukung GPS."; return; }
    btnMyLocation.textContent = "⏳ Mendeteksi...";
    btnMyLocation.disabled = true;
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        myLat = pos.coords.latitude; myLng = pos.coords.longitude;
        btnMyLocation.textContent = "✅ Lokasi Terdeteksi!";
        btnMyLocation.style.background = "linear-gradient(135deg,#16a34a,#15803d)";
        btnMyLocation.disabled = false;
        locationInfo.style.display = "block";
        locationInfo.innerHTML = `📍 <b>${myLat.toFixed(5)}, ${myLng.toFixed(5)}</b>`;
        statusDiv.textContent = "📍 Lokasi GPS ditemukan! Ketik jenis bisnis lalu klik Cari.";
        statusDiv.style.color = "#4ade80";
        window.location.href = `https://www.google.com/maps/@${myLat},${myLng},15z`;
      },
      (err) => {
        btnMyLocation.textContent = "📍 Deteksi Lokasi Saya (GPS)";
        btnMyLocation.style.background = "linear-gradient(135deg,#f59e0b,#d97706)";
        btnMyLocation.disabled = false;
        statusDiv.textContent = "❌ Gagal deteksi lokasi. Izinkan akses GPS di browser.";
        statusDiv.style.color = "#f87171";
      },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
    );
  });

  // ========== 5. SEARCH NEARBY ==========
  const doSearch = () => {
    let kw = searchKeyword.value.trim();
    if (!kw) { 
      kw = "Tempat Usaha"; // Default pencarian umum jika kosong
    }
    if (!myLat || !myLng) {
      const m = window.location.href.match(/@(-?\d+\.\d+),(-?\d+\.\d+)/);
      if (m) { myLat = parseFloat(m[1]); myLng = parseFloat(m[2]); }
    }
    statusDiv.textContent = `🔍 Mencari "${kw}"...`;
    statusDiv.style.color = "#38bdf8";
    const url = myLat && myLng
      ? `https://www.google.com/maps/search/${encodeURIComponent(kw)}/@${myLat},${myLng},14z`
      : `https://www.google.com/maps/search/${encodeURIComponent(kw)}`;
    window.location.href = url;
  };
  btnSearchNearby.addEventListener("click", doSearch);
  searchKeyword.addEventListener("keydown", (e) => { if (e.key === "Enter") doSearch(); });

  // ========== 6. ROBUST EXTRACTOR ==========
  btnScrape.addEventListener("click", () => {

    // CHECK: Must be on a search results page
    const currentUrl = window.location.href;
    const isSearchPage = currentUrl.includes("/maps/search/") || currentUrl.includes("/maps/place/");

    if (!isSearchPage) {
      statusDiv.innerHTML = `⚠️ <b>Belum ada pencarian aktif!</b><br><small>Ketik jenis bisnis di kolom "Cari Bisnis di Sekitar" (contoh: <b>Salon</b>) lalu klik <b>Cari</b>, atau ketik langsung di search box Google Maps.</small>`;
      statusDiv.style.color = "#f87171";
      return;
    }

    statusDiv.textContent = "⏳ Memindai data bisnis dari hasil pencarian Google Maps...";
    statusDiv.style.color = "#fbbf24";

    const extracted = [];
    const seenNames = new Set();

    // Blacklist: Google Maps UI elements that are NOT business names
    const BLACKLIST = new Set([
      "Hasil", "Google Maps", "Simpan", "Rute", "Situs web", "Peta",
      "Bagikan", "Kirim ke ponsel", "Petunjuk arah", "Login", "Logout",
      "Telusuri", "Tambahkan label", "Lapisan", "Cari di sekitar sini",
      "Telusuri Google Maps", "Lihat samping", "Map details", "Map tools",
      "Map type", "Satellite", "Terrain", "Default", "Transit", "Traffic",
      "Biking", "Street View", "Wildfires", "Air quality", "Globe view",
      "3D", "Labels", "Tampilkan Street View", "Ukur jarak",
      "Cetak", "Setelan", "Bantuan", "Kirim masukan", "Tips dan trik",
      "Bahasa", "Unduh Google Maps", "Detail peta", "Alat peta", "Jenis peta",
      "Nearby", "Directions", "Save", "Share", "Send to phone",
      "Layers", "More info", "Explore", "Add a missing place",
      "Your data in Maps", "Reviews", "Updates", "Menu", "Tutup",
      "Buka", "Zoom in", "Zoom out", "Show your location",
      "Kembali ke hasil", "Lainnya", "More", "Less", "Show more"
    ]);

    const isValidBiz = (t) => {
      if (!t || t.length < 3 || t.length > 100) return false;
      if (BLACKLIST.has(t)) return false;
      // Reject pure UI strings: single words that match common UI
      if (/^(Map|Peta|Show|Hide|Close|Open|Back|Next|More|Less|Send|Save|Share|Print|Help)\b/i.test(t)) return false;
      // Reject pure numbers, coordinates, or URLs
      if (/^[\d\s\.\,\-\/\@\:]+$/.test(t)) return false;
      if (t.startsWith("http") || t.startsWith("www.")) return false;
      // Reject very short generic strings
      if (t.length < 4) return false;
      return true;
    };

    const addEntry = (name, phone, rating, url) => {
      const clean = name.trim().replace(/\n.*/g, ""); // Only first line
      if (!isValidBiz(clean) || seenNames.has(clean)) return;
      seenNames.add(clean);
      extracted.push({
        nama_usaha: clean,
        no_telp: phone || "-",
        rating: rating || "-",
        google_maps_url: url || currentUrl
      });
    };

    // ---- STRATEGY D: Detail panel (single place view - PRIORITIZED!) ----
    if (currentUrl.includes("/maps/place/")) {
      const h1 = document.querySelector("h1.DUwDvf, h1.fontHeadlineLarge");
      if (h1) {
        const title = h1.innerText.trim();
        let phone = "";
        let rating = "-";

        // Try to get phone from specific button data attribute
        const phoneBtn = document.querySelector('button[data-item-id^="phone:"]');
        if (phoneBtn) {
          const pid = phoneBtn.getAttribute("data-item-id") || "";
          const pm = pid.match(/phone:tel:([\+\d\-\s]+)/);
          if (pm) phone = pm[1].trim();
        }

        // Fallback: aggressive regex scan on the entire main panel text
        const mainPanel = document.querySelector('div[role="main"]') || document.body;
        const allText = mainPanel.innerText || "";
        
        if (!phone) {
          const phoneMatch = allText.match(/((?:\+62|62|0)\d[\d\s\-]{7,})/);
          if (phoneMatch) phone = phoneMatch[1].trim();
        }
        
        const ratingMatch = allText.match(/(\d[\.,]\d)\s*(?:\(|bintang|star|ulasan|reviews)/i);
        if (ratingMatch) rating = ratingMatch[1];

        addEntry(title, phone, rating, currentUrl);
      }
    }

    // ---- STRATEGY A: Place links with aria-label (most reliable) ----
    document.querySelectorAll('a[href*="/maps/place/"]').forEach((link) => {
      const aria = (link.getAttribute("aria-label") || "").trim();
      if (!aria) return; // Skip links without aria-label
      
      const parentCard = link.closest("div.Nv2PK") || link.closest("div.m6QEdf") || link.parentElement?.parentElement;
      let phone = "", rating = "-";
      if (parentCard) {
        const txt = parentCard.innerText || "";
        const pm = txt.match(/((?:\+62|62|0)\d[\d\s\-]{7,})/);
        if (pm) phone = pm[1].trim();
        const rm = txt.match(/(\d[\.,]\d)\s*(?:\(|bintang|star|ulasan)/i);
        if (rm) rating = rm[1];
      }
      addEntry(aria, phone, rating, link.href);
    });

    // ---- STRATEGY B: Feed container children ----
    const feed = document.querySelector('div[role="feed"]');
    if (feed) {
      Array.from(feed.children).forEach((child) => {
        // Find the primary link with aria-label in each card
        const mainLink = child.querySelector('a[aria-label][href*="/maps/place/"]') || child.querySelector('a[aria-label]');
        if (mainLink) {
          const title = (mainLink.getAttribute("aria-label") || "").trim();
          const href = mainLink.href || currentUrl;
          const txt = child.innerText || "";
          let phone = "", rating = "-";
          const pm = txt.match(/((?:\+62|62|0)\d[\d\s\-]{7,})/);
          if (pm) phone = pm[1].trim();
          const rm = txt.match(/(\d[\.,]\d)\s*(?:\(|bintang|star|ulasan)/i);
          if (rm) rating = rm[1];
          addEntry(title, phone, rating, href);
        }
      });
    }

    // ---- STRATEGY C: Known class selectors for business titles ----
    ["div.qBF1Pd", "span.fontHeadlineSmall", "div.NrDZNb", "div.rgHvZc"].forEach((sel) => {
      document.querySelectorAll(sel).forEach((el) => {
        const title = (el.innerText || "").trim().split("\n")[0];
        const link = el.closest("a") || el.parentElement?.closest("a");
        const href = link?.href || currentUrl;
        // Only add if href looks like a place link
        if (href.includes("/maps/place/") || href.includes("/maps/search/")) {
          addEntry(title, "", "-", href);
        }
      });
    });

    console.log(`[Business Lead Scraper] Found ${extracted.length} entries:`, extracted);

    if (extracted.length === 0) {
      statusDiv.innerHTML = `⚠️ <b>Tidak ada bisnis terdeteksi!</b><br><small>Pastikan: 1) Sudah ketik pencarian, 2) Hasil muncul di panel kiri, 3) <b>Scroll ke bawah</b> beberapa kali agar data ter-load.</small>`;
      statusDiv.style.color = "#f87171";
      return;
    }

    statusDiv.textContent = `✅ Berhasil mengekstrak ${extracted.length} bisnis!`;
    statusDiv.style.color = "#4ade80";

    const blob = new Blob([JSON.stringify(extracted, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `prospek_bisnis_cepat_${radiusRange.value}km.json`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  });

  // ========== 7. AUTO-BOT DEEP SCRAPE (CLICKS EVERYTHING) ==========
  btnBotScrape.addEventListener("click", async () => {
    const currentUrl = window.location.href;
    const isSearchPage = currentUrl.includes("/maps/search/") || currentUrl.includes("/maps/place/");

    if (!isSearchPage) {
      statusDiv.innerHTML = `⚠️ <b>Belum ada pencarian aktif!</b><br><small>Lakukan pencarian bisnis terlebih dahulu.</small>`;
      statusDiv.style.color = "#f87171";
      return;
    }

    const links = Array.from(document.querySelectorAll('a[href*="/maps/place/"]'));
    if (links.length === 0) {
      statusDiv.textContent = "⚠️ Tidak ada bisnis di daftar. Pastikan hasil pencarian sudah muncul!";
      statusDiv.style.color = "#f87171";
      return;
    }

    // Prepare variables
    const extracted = [];
    const seenNames = new Set();
    
    // Disable buttons during bot run
    btnBotScrape.disabled = true;
    btnScrape.disabled = true;

    for (let i = 0; i < links.length; i++) {
      statusDiv.innerHTML = `🤖 <b>Bot bekerja:</b> Membuka bisnis ${i + 1} dari ${links.length}...<br><small style="color:#fbbf24;">Jangan klik apapun, biarkan bot bekerja!</small>`;
      statusDiv.style.color = "#4ade80";

      const link = links[i];
      const fallbackTitle = (link.getAttribute("aria-label") || "").trim();

      // Click the item in the list
      link.click();
      
      // Wait for detail panel to slide in and load
      await new Promise(r => setTimeout(r, 2500));

      // EXTRACT DETAIL PANEL
      const h1 = document.querySelector("h1.DUwDvf, h1.fontHeadlineLarge");
      let title = h1 ? h1.innerText.trim() : fallbackTitle;
      
      let phone = "";
      let rating = "-";

      const phoneBtn = document.querySelector('button[data-item-id^="phone:"]');
      if (phoneBtn) {
        const pid = phoneBtn.getAttribute("data-item-id") || "";
        const pm = pid.match(/phone:tel:([\+\d\-\s]+)/);
        if (pm) phone = pm[1].trim();
      }

      const mainPanel = document.querySelector('div[role="main"]') || document.body;
      const allText = mainPanel.innerText || "";
      
      if (!phone) {
        const phoneMatch = allText.match(/((?:\+62|62|0)\d[\d\s\-]{7,})/);
        if (phoneMatch) phone = phoneMatch[1].trim();
      }
      
      const ratingMatch = allText.match(/(\d[\.,]\d)\s*(?:\(|bintang|star|ulasan|reviews)/i);
      if (ratingMatch) rating = ratingMatch[1];

      // Add if valid and not seen
      if (title && title.length > 2 && !seenNames.has(title) && !/^(Map|Peta|Show|Hide)\b/i.test(title)) {
        seenNames.add(title);
        extracted.push({
          nama_usaha: title,
          no_telp: phone || "-",
          rating: rating || "-",
          google_maps_url: window.location.href
        });
      }

      // CLICK BACK BUTTON
      const backBtn = document.querySelector('button[aria-label="Kembali ke hasil"]') || 
                      document.querySelector('button[aria-label="Back"]') ||
                      document.querySelector('button.cewAtd');
                      
      if (backBtn) {
        backBtn.click();
      } else {
        // Fallback: use history back if back button is hidden
        window.history.back();
      }

      // Wait for list to slide back in
      await new Promise(r => setTimeout(r, 1500));
    }

    // Re-enable buttons
    btnBotScrape.disabled = false;
    btnScrape.disabled = false;

    statusDiv.textContent = `✅ Bot Selesai! Berhasil mengekstrak ${extracted.length} bisnis dengan nomor telpon.`;
    statusDiv.style.color = "#4ade80";

    // Download JSON
    const blob = new Blob([JSON.stringify(extracted, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `prospek_bot_lengkap_${radiusRange.value}km.json`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  });
})();
