"""
UMKM Scraper Engine - Core Scraping & Contact Extraction Module
Strategy: Google Maps Search → Collect cards → Click each business detail → Extract phone/website/address
"""

import re
import os
import time
import json
import logging
import urllib.parse
from typing import List, Dict, Any, Optional, Tuple

import requests
from bs4 import BeautifulSoup
import pandas as pd
import phonenumbers

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("UMKMScraper")


class PhoneUtils:
    """Helper class to clean, parse, and format Indonesian phone numbers and WA links."""

    @staticmethod
    def clean_phone(phone_str: str) -> str:
        if not phone_str:
            return ""
        cleaned = re.sub(r"[^\d+]", "", phone_str)
        return cleaned

    @staticmethod
    def format_indonesia_phone(phone_str: str) -> Tuple[str, str, str]:
        """
        Formats a raw phone string.
        Returns:
            (phone_raw, phone_formatted, wa_link)
        """
        if not phone_str:
            return "", "", ""

        cleaned = PhoneUtils.clean_phone(phone_str)
        if not cleaned:
            return phone_str, "", ""

        if cleaned.startswith("08"):
            wa_num = "62" + cleaned[1:]
        elif cleaned.startswith("+628"):
            wa_num = cleaned[1:]
        elif cleaned.startswith("628"):
            wa_num = cleaned
        elif cleaned.startswith("0"):
            wa_num = ""
        else:
            wa_num = cleaned if cleaned.startswith("62") else ""

        formatted_phone = phone_str
        try:
            parsed = phonenumbers.parse(phone_str if phone_str.startswith("+") else ("+" + wa_num if wa_num else phone_str), "ID")
            if phonenumbers.is_valid_number(parsed):
                formatted_phone = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        except Exception:
            pass

        wa_link = f"https://wa.me/{wa_num}" if wa_num and len(wa_num) >= 10 else ""
        return phone_str, formatted_phone, wa_link

    @staticmethod
    def extract_phones_from_text(text: str) -> List[Tuple[str, str, str]]:
        """Extracts potential Indonesian mobile / phone numbers from raw text or HTML."""
        if not text:
            return []

        wa_link_pattern = r"(?:https?:\/\/)?(?:wa\.me|api\.whatsapp\.com\/send\?phone=)(\d+)"
        phone_pattern = r"(?:\+62|62|0)[\s\-]?8[1-9][\d\s\-]{7,12}"

        results = []
        seen = set()

        for match in re.finditer(wa_link_pattern, text):
            num = match.group(1)
            if num not in seen and len(num) >= 10:
                seen.add(num)
                raw, fmt, wa = PhoneUtils.format_indonesia_phone(num)
                results.append((raw, fmt, wa))

        for match in re.finditer(phone_pattern, text):
            num = re.sub(r"[^\d+]", "", match.group(0))
            if num not in seen and len(num) >= 10:
                seen.add(num)
                raw, fmt, wa = PhoneUtils.format_indonesia_phone(num)
                results.append((raw, fmt, wa))

        return results


class ContactExtractor:
    """Extracts additional WhatsApp links, social profiles, and emails from target website."""

    @staticmethod
    def scrape_website_details(url: str, timeout: int = 5) -> Dict[str, Any]:
        result = {
            "extra_wa": [],
            "wa_link": "",
            "emails": [],
            "socials": [],
            "status": "Skipped"
        }

        if not url or not url.startswith("http"):
            return result

        if any(domain in url.lower() for domain in ["facebook.com", "instagram.com", "tokopedia.com", "shopee.co.id", "tiktok.com", "google.com", "business.site"]):
            result["status"] = "Social/Map Site"
            return result

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7"
        }

        try:
            resp = requests.get(url, headers=headers, timeout=timeout, verify=False)
            if resp.status_code == 200:
                html = resp.text
                soup = BeautifulSoup(html, "html.parser")

                phones = PhoneUtils.extract_phones_from_text(html)
                for raw, fmt, wa in phones:
                    if wa and wa not in result["extra_wa"]:
                        result["extra_wa"].append(wa)

                if result["extra_wa"]:
                    result["wa_link"] = result["extra_wa"][0]

                email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
                emails = list(set(re.findall(email_pattern, html)))
                result["emails"] = [e for e in emails if not e.endswith((".png", ".jpg", ".svg"))][:3]

                social_domains = ["instagram.com", "facebook.com", "tiktok.com", "shopee.co.id", "tokopedia.com"]
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    if any(sd in href for sd in social_domains):
                        if href not in result["socials"]:
                            result["socials"].append(href)

                result["status"] = "Success"
            else:
                result["status"] = f"HTTP {resp.status_code}"
        except Exception as e:
            result["status"] = f"Error: {str(e)[:30]}"

        return result


class UMKMScraper:
    """
    Main Scraping Engine.
    Strategy: 
      Pass 1 - Search Google Maps, scroll & collect business card elements
      Pass 2 - Click into each business detail panel to extract phone, website, address
    """

    def __init__(self, mode: str = "selenium", headless: bool = True):
        self.mode = mode
        self.headless = headless
        self.driver = None

    def _init_driver(self):
        """Initializes Chrome or Edge WebDriver via Selenium with desktop resolution."""
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options as ChromeOptions
        from selenium.webdriver.edge.options import Options as EdgeOptions

        # Try Chrome first
        try:
            chrome_options = ChromeOptions()
            if self.headless:
                chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--lang=id-ID")
            chrome_options.add_experimental_option("prefs", {"intl.accept_languages": "id,id-ID,en"})
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")

            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("Selenium Chrome driver initialized successfully.")
            return True
        except Exception as e:
            logger.warning(f"Chrome driver failed: {e}. Trying Edge...")

        # Try Edge as fallback
        try:
            edge_options = EdgeOptions()
            if self.headless:
                edge_options.add_argument("--headless=new")
            edge_options.add_argument("--window-size=1920,1080")
            edge_options.add_argument("--start-maximized")
            edge_options.add_argument("--disable-gpu")
            edge_options.add_argument("--no-sandbox")
            edge_options.add_argument("--lang=id-ID")
            edge_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edge/122.0.0.0")

            self.driver = webdriver.Edge(options=edge_options)
            logger.info("Selenium Edge driver initialized successfully.")
            return True
        except Exception as e:
            logger.error(f"Edge driver also failed: {e}")
            return False

    def _extract_detail_panel(self) -> Dict[str, str]:
        """
        Extracts business details from the currently open Google Maps detail panel.
        Returns dict with: name, phone, website, address, rating, reviews, category
        """
        from selenium.webdriver.common.by import By

        detail = {
            "name": "",
            "phone": "",
            "website": "",
            "address": "",
            "rating": "-",
            "reviews": "-",
            "category": "",
            "latitude": None,
            "longitude": None,
        }

        try:
            # Wait for detail panel to load
            time.sleep(2)

            # --- NAME ---
            try:
                # Try specific Google Maps business name selectors first
                name_found = False
                for selector in ["h1.DUwDvf", "h1.fontHeadlineLarge", "div.lMbq3e h1", "span.fontHeadlineLarge"]:
                    try:
                        name_el = self.driver.find_element(By.CSS_SELECTOR, selector)
                        candidate = name_el.text.strip()
                        # Filter out generic page titles
                        if candidate and candidate not in ["Hasil", "Results", "Google Maps", "Login", ""]:
                            detail["name"] = candidate
                            name_found = True
                            break
                    except Exception:
                        continue
                # Last resort: try any h1 but validate it
                if not name_found:
                    try:
                        h1_els = self.driver.find_elements(By.TAG_NAME, "h1")
                        for h1 in h1_els:
                            txt = h1.text.strip()
                            if txt and len(txt) > 2 and txt not in ["Hasil", "Results", "Google Maps", "Login"]:
                                detail["name"] = txt
                                break
                    except Exception:
                        pass
            except Exception:
                pass

            # --- PHONE ---
            # Google Maps stores phone in button[data-item-id^="phone:"]
            # The data-item-id looks like: phone:tel:+62-813-1501-1866
            try:
                phone_buttons = self.driver.find_elements(By.CSS_SELECTOR, 'button[data-item-id^="phone:"]')
                for btn in phone_buttons:
                    item_id = btn.get_attribute("data-item-id") or ""
                    # Extract phone from data-item-id="phone:tel:+62-813-1501-1866"
                    phone_match = re.search(r"phone:tel:([\+\d\-\s]+)", item_id)
                    if phone_match:
                        detail["phone"] = phone_match.group(1).strip()
                        break
                    # Fallback: try aria-label
                    aria = btn.get_attribute("aria-label") or ""
                    phone_in_aria = re.search(r"([\+\d][\d\-\s]{8,})", aria)
                    if phone_in_aria:
                        detail["phone"] = phone_in_aria.group(1).strip()
                        break
                    # Fallback: try button text
                    btn_text = btn.text.strip()
                    if btn_text and re.search(r"\d{4,}", btn_text):
                        detail["phone"] = btn_text
                        break
            except Exception:
                pass

            # If still no phone, try looking for any element containing phone-like text
            if not detail["phone"]:
                try:
                    # Look for elements with aria-label containing "Telepon" or "Phone"
                    phone_els = self.driver.find_elements(By.CSS_SELECTOR, '[data-tooltip*="telepon" i], [data-tooltip*="phone" i], [aria-label*="Telepon"], [aria-label*="Phone"]')
                    for el in phone_els:
                        aria = el.get_attribute("aria-label") or ""
                        text = el.text.strip()
                        for candidate in [aria, text]:
                            phone_match = re.search(r"((?:\+62|0)[\d\-\s]{8,})", candidate)
                            if phone_match:
                                detail["phone"] = phone_match.group(1).strip()
                                break
                        if detail["phone"]:
                            break
                except Exception:
                    pass

            # Last resort: scan the entire detail panel text for phone numbers
            if not detail["phone"]:
                try:
                    panel_text = self.driver.find_element(By.CSS_SELECTOR, "div[role='main']").text
                    phones = PhoneUtils.extract_phones_from_text(panel_text)
                    if phones:
                        detail["phone"] = phones[0][0]  # raw phone
                except Exception:
                    pass

            # --- WEBSITE ---
            try:
                website_els = self.driver.find_elements(By.CSS_SELECTOR, 'a[data-item-id="authority"]')
                if website_els:
                    detail["website"] = website_els[0].get_attribute("href") or ""
                else:
                    # Fallback: look for link with aria-label about website
                    site_links = self.driver.find_elements(By.CSS_SELECTOR, 'a[aria-label*="situs" i], a[aria-label*="website" i]')
                    for sl in site_links:
                        href = sl.get_attribute("href") or ""
                        if href and "google.com" not in href:
                            detail["website"] = href
                            break
            except Exception:
                pass

            # --- ADDRESS ---
            try:
                addr_btns = self.driver.find_elements(By.CSS_SELECTOR, 'button[data-item-id="address"]')
                if addr_btns:
                    aria = addr_btns[0].get_attribute("aria-label") or ""
                    if aria:
                        detail["address"] = aria.replace("Alamat: ", "").replace("Address: ", "").strip()
                    else:
                        detail["address"] = addr_btns[0].text.strip()
            except Exception:
                pass

            # --- RATING & REVIEWS ---
            try:
                rating_el = self.driver.find_elements(By.CSS_SELECTOR, "div.F7nice span[aria-hidden='true'], span.ceNzKf")
                if rating_el:
                    rating_text = rating_el[0].text.strip()
                    if rating_text:
                        detail["rating"] = rating_text
                # Reviews count
                review_els = self.driver.find_elements(By.CSS_SELECTOR, "span[aria-label*='ulasan'], span[aria-label*='review']")
                if review_els:
                    review_match = re.search(r"([\d\.\,]+(?:\s*(?:rb|k))?)", review_els[0].get_attribute("aria-label") or review_els[0].text)
                    if review_match:
                        detail["reviews"] = review_match.group(1)
            except Exception:
                pass

            # --- CATEGORY ---
            try:
                cat_els = self.driver.find_elements(By.CSS_SELECTOR, "button.DkEaL, span.DkEaL")
                if cat_els:
                    detail["category"] = cat_els[0].text.strip()
            except Exception:
                pass

            # --- LATITUDE & LONGITUDE ---
            try:
                current_url = self.driver.current_url
                coord_match = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", current_url)
                if not coord_match:
                    coord_match = re.search(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", current_url)
                if coord_match:
                    detail["latitude"] = float(coord_match.group(1))
                    detail["longitude"] = float(coord_match.group(2))
            except Exception:
                pass

        except Exception as e:
            logger.error(f"Error extracting detail panel: {e}")

        return detail

    def scrape_google_maps(
        self,
        keyword: str,
        location: str,
        max_results: int = 20,
        enrich_website: bool = True,
        progress_callback=None
    ) -> List[Dict[str, Any]]:
        """
        Two-pass Google Maps scraper:
          Pass 1: Search → scroll → collect card names & Maps place URLs
          Pass 2: Visit each place URL → extract phone/website/address from detail panel
        """
        query = f"{keyword} {location}".strip()
        search_url = f"https://www.google.com/maps/search/{urllib.parse.quote(query)}?hl=id"

        logger.info(f"Starting Google Maps scrape for: '{query}' (Target: {max_results})")
        if progress_callback:
            progress_callback(5, f"Memulai browser untuk pencarian Google Maps: {query}...")

        if not self.driver:
            driver_ok = self._init_driver()
            if not driver_ok:
                logger.warning("Browser driver failed. Falling back to HTTP scraper.")
                return self.scrape_http_fallback(keyword, location, max_results, enrich_website, progress_callback)

        results = []
        try:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.common.action_chains import ActionChains

            # ====== PASS 1: Collect card links from search results ======
            self.driver.get(search_url)
            time.sleep(5)

            # Handle consent overlay
            try:
                consent_btns = self.driver.find_elements(By.CSS_SELECTOR, "form[action*='consent'] button, button[aria-label*='Setuju'], button[aria-label*='Accept']")
                if consent_btns:
                    consent_btns[0].click()
                    time.sleep(3)
            except Exception:
                pass

            if progress_callback:
                progress_callback(10, "Mencari daftar usaha di Google Maps...")

            # Scroll to collect enough cards
            scroll_attempts = 0
            max_scrolls = max(8, max_results // 2)

            scroll_container = None
            try:
                containers = self.driver.find_elements(By.CSS_SELECTOR, "div[role='feed'], div.m6QEdf")
                if containers:
                    scroll_container = containers[0]
            except Exception:
                pass

            while scroll_attempts < max_scrolls:
                cards = self.driver.find_elements(By.CSS_SELECTOR, "div.Nv2pk, div[role='article']")
                if not cards:
                    cards = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/maps/place']")

                if progress_callback:
                    progress_callback(
                        10 + min(20, int((len(cards) / max(max_results, 1)) * 20)),
                        f"Scroll: ditemukan {len(cards)} tempat..."
                    )

                if len(cards) >= max_results:
                    break

                if scroll_container:
                    self.driver.execute_script("arguments[0].scrollTop += 1000;", scroll_container)
                else:
                    self.driver.execute_script("window.scrollBy(0, 1000);")
                time.sleep(2)
                scroll_attempts += 1

            # Re-collect final cards
            cards = self.driver.find_elements(By.CSS_SELECTOR, "div.Nv2pk, div[role='article']")
            if not cards:
                cards = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/maps/place']")
            cards = cards[:max_results]
            total_cards = len(cards)

            logger.info(f"Pass 1 complete: found {total_cards} business cards.")

            if progress_callback:
                progress_callback(30, f"Ditemukan {total_cards} bisnis. Mulai buka profil satu-satu...")

            # ====== PASS 2: Click each card → extract detail ======
            for idx in range(total_cards):
                try:
                    # Re-find cards each iteration (DOM may have changed after navigating back)
                    cards = self.driver.find_elements(By.CSS_SELECTOR, "div.Nv2pk, div[role='article']")
                    if not cards:
                        cards = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/maps/place']")

                    if idx >= len(cards):
                        logger.warning(f"Card index {idx} out of range ({len(cards)} cards). Stopping.")
                        break

                    card = cards[idx]

                    # Get card preview name (for logging)
                    preview_name = ""
                    try:
                        name_els = card.find_elements(By.CSS_SELECTOR, "div.qBF1Pd, div.fontHeadlineSmall, a[aria-label]")
                        for ne in name_els:
                            txt = ne.text.strip() or ne.get_attribute("aria-label") or ""
                            if txt and txt not in ["Aplikasi Google", "Login", "Google Maps"]:
                                preview_name = txt
                                break
                        if not preview_name:
                            lines = [l.strip() for l in card.text.split("\n") if l.strip()]
                            preview_name = lines[0] if lines else f"Bisnis #{idx+1}"
                    except Exception:
                        preview_name = f"Bisnis #{idx+1}"

                    if preview_name in ["Aplikasi Google", "Login", "Google Maps"]:
                        continue

                    if progress_callback:
                        pct = 30 + int((idx / max(total_cards, 1)) * 65)
                        progress_callback(pct, f"[{idx+1}/{total_cards}] Buka profil: {preview_name[:30]}...")

                    logger.info(f"Pass 2 [{idx+1}/{total_cards}]: Opening detail for '{preview_name}'...")

                    # Click the card to open detail panel
                    try:
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card)
                        time.sleep(0.5)
                        card.click()
                    except Exception:
                        try:
                            self.driver.execute_script("arguments[0].click();", card)
                        except Exception as click_err:
                            logger.error(f"Cannot click card #{idx+1}: {click_err}")
                            continue

                    # Wait for detail panel to load
                    time.sleep(3)

                    # Extract all details from the detail panel
                    detail = self._extract_detail_panel()

                    name = detail["name"] or preview_name
                    phone_raw = detail["phone"]
                    website = detail["website"]
                    address = detail["address"] or f"{location} (Google Maps)"
                    rating = detail["rating"]
                    reviews = detail["reviews"]
                    category = detail["category"] or keyword

                    # Format phone → WA link
                    phone_fmt, wa_link = "", ""
                    if phone_raw:
                        _, phone_fmt, wa_link = PhoneUtils.format_indonesia_phone(phone_raw)
                        if not phone_fmt:
                            phone_fmt = phone_raw

                    # Get current Maps URL as the place URL
                    maps_url = self.driver.current_url

                    # Deep website enrichment
                    extra_wa = []
                    social_links = []
                    emails = []
                    if enrich_website and website:
                        enrich_res = ContactExtractor.scrape_website_details(website)
                        if enrich_res["wa_link"] and not wa_link:
                            wa_link = enrich_res["wa_link"]
                        extra_wa = enrich_res["extra_wa"]
                        social_links = enrich_res["socials"]
                        emails = enrich_res["emails"]

                    biz_data = {
                        "no": len(results) + 1,
                        "nama_usaha": name,
                        "kategori": category,
                        "lokasi_alamat": address,
                        "no_telp": phone_fmt or phone_raw,
                        "wa_link": wa_link,
                        "website": website,
                        "extra_wa": ", ".join(extra_wa) if extra_wa else "",
                        "email": ", ".join(emails) if emails else "",
                        "sosial_media": ", ".join(social_links) if social_links else "",
                        "rating": rating,
                        "jumlah_ulasan": reviews,
                        "latitude": detail.get("latitude"),
                        "longitude": detail.get("longitude"),
                        "google_maps_url": maps_url
                    }

                    results.append(biz_data)
                    logger.info(f"✅ Bisnis #{len(results)}: {name} | Phone: {phone_fmt or phone_raw} | WA: {wa_link}")

                    # Navigate BACK to the search results list
                    self.driver.get(search_url)
                    time.sleep(4)

                    # Re-scroll to roughly where we were
                    if scroll_container:
                        try:
                            containers = self.driver.find_elements(By.CSS_SELECTOR, "div[role='feed'], div.m6QEdf")
                            if containers:
                                scroll_container = containers[0]
                                scroll_px = idx * 120  # approximate card height
                                self.driver.execute_script(f"arguments[0].scrollTop = {scroll_px};", scroll_container)
                                time.sleep(2)
                        except Exception:
                            pass

                except Exception as card_err:
                    logger.error(f"Error processing card #{idx+1}: {card_err}")
                    # Try to go back to search results
                    try:
                        self.driver.get(search_url)
                        time.sleep(4)
                    except Exception:
                        pass

            if progress_callback:
                progress_callback(100, f"Selesai! Berhasil mengumpulkan {len(results)} data UMKM.")

        except Exception as e:
            logger.error(f"Google Maps scrape exception: {e}")
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                    self.driver = None
                except Exception:
                    pass

        # Fallback if zero results
        if not results:
            logger.info("Zero results from Selenium. Triggering HTTP fallback scraper...")
            results = self.scrape_http_fallback(keyword, location, max_results, enrich_website, progress_callback)

        return results

    def scrape_http_fallback(
        self,
        keyword: str,
        location: str,
        max_results: int = 20,
        enrich_website: bool = True,
        progress_callback=None
    ) -> List[Dict[str, Any]]:
        """Fast HTTP-based fallback scraper using Bing search."""
        query = f"{keyword} {location} contact whatsapp website"
        logger.info(f"Running HTTP Fallback Scraper for query: '{query}'")
        if progress_callback:
            progress_callback(20, f"Menjalankan Fast HTTP Scraper untuk: {query}...")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7"
        }

        url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}"
        results = []

        try:
            resp = requests.get(url, headers=headers, timeout=12, verify=False)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                entries = soup.find_all("li", class_="b_algo")

                count = 0
                for idx, entry in enumerate(entries, 1):
                    if count >= max_results:
                        break

                    h2_elem = entry.find("h2")
                    snippet_elem = entry.find("p") or entry.find("div", class_="b_caption")

                    if not h2_elem or not h2_elem.find("a"):
                        continue

                    a_tag = h2_elem.find("a")
                    name = a_tag.text.strip()
                    website = a_tag.get("href", "")
                    snippet = snippet_elem.text.strip() if snippet_elem else ""

                    name = re.sub(r"\s*-\s*.*$", "", name)

                    phones = PhoneUtils.extract_phones_from_text(name + " " + snippet)
                    fmt_phone, wa_link = "", ""
                    if phones:
                        raw_phone, fmt_phone, wa_link = phones[0]

                    emails, socials = [], []
                    if enrich_website and website and website.startswith("http"):
                        enrich_res = ContactExtractor.scrape_website_details(website)
                        if enrich_res["wa_link"] and not wa_link:
                            wa_link = enrich_res["wa_link"]
                        emails = enrich_res["emails"]
                        socials = enrich_res["socials"]

                    count += 1
                    biz_data = {
                        "no": count,
                        "nama_usaha": name,
                        "kategori": keyword,
                        "lokasi_alamat": f"{location} (Hasil Web)",
                        "no_telp": fmt_phone,
                        "wa_link": wa_link,
                        "website": website,
                        "extra_wa": "",
                        "email": ", ".join(emails) if emails else "",
                        "sosial_media": ", ".join(socials) if socials else "",
                        "rating": "-",
                        "jumlah_ulasan": "-",
                        "google_maps_url": f"https://www.google.com/search?q={urllib.parse.quote(name + ' ' + location)}"
                    }
                    results.append(biz_data)

            if progress_callback:
                progress_callback(100, f"HTTP Scrape Selesai! {len(results)} data.")
        except Exception as e:
            logger.error(f"HTTP Fallback exception: {e}")

        return results


import math

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates the great circle distance in kilometers between two geographic points."""
    try:
        if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
            return 999999.0
        lat1, lon1, lat2, lon2 = float(lat1), float(lon1), float(lat2), float(lon2)
        R = 6371.0  # Earth radius in KM
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2.0) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2.0) ** 2)
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return round(R * c, 2)
    except Exception:
        return 999999.0


def export_to_dataframe(data: List[Dict[str, Any]]) -> pd.DataFrame:
    """Converts scraped list of dicts to a cleaned pandas DataFrame."""
    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)
    column_order = [
        "no", "nama_usaha", "kategori", "lokasi_alamat",
        "no_telp", "wa_link", "website", "email",
        "sosial_media", "rating", "jumlah_ulasan", "latitude", "longitude", "jarak_km", "google_maps_url"
    ]
    existing_cols = [c for c in column_order if c in df.columns]
    return df[existing_cols]

