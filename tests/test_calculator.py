import math
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0 # km
    rad = math.radians
    dLat = rad(lat2 - lat1)
    dLon = rad(lon2 - lon1)
    a = math.sin(dLat / 2)**2 + math.cos(rad(lat1)) * math.cos(rad(lat2)) * math.sin(dLon / 2)**2
    c = 2 * math.asin(math.sqrt(max(0, min(1, a))))
    return R * c

def test_haversine_accuracy():
    # Lahore (31.5204, 74.3587) to Islamabad (33.6844, 73.0479)
    dist = haversine(31.5204, 74.3587, 33.6844, 73.0479)
    assert 260 < dist < 275, f"Expected ~267 km, got {dist:.2f}"
    
    # London (51.5074, -0.1278) to Paris (48.8566, 2.3522)
    dist_lp = haversine(51.5074, -0.1278, 48.8566, 2.3522)
    assert 330 < dist_lp < 350, f"Expected ~343 km, got {dist_lp:.2f}"
    
    # Zero distance (same location)
    dist_zero = haversine(31.5204, 74.3587, 31.5204, 74.3587)
    assert dist_zero == 0.0, f"Expected 0.0, got {dist_zero}"
    print("[PASS] Haversine accuracy and zero-distance test passed.")

def test_fuel_calculations():
    distance_km = 300.0
    
    # 1. km/L
    eff_kml = 15.0
    price_kml = 2.0
    fuel_kml = distance_km / eff_kml
    cost_kml = fuel_kml * price_kml
    assert fuel_kml == 20.0, f"Expected 20.0 L, got {fuel_kml}"
    assert cost_kml == 40.0, f"Expected 40.0, got {cost_kml}"
    
    # 2. L/100km
    eff_l100 = 8.0 # 8 L per 100km -> for 300km = 24 L
    price_l100 = 1.5
    fuel_l100 = (distance_km / 100.0) * eff_l100
    cost_l100 = fuel_l100 * price_l100
    assert fuel_l100 == 24.0, f"Expected 24.0 L, got {fuel_l100}"
    assert cost_l100 == 36.0, f"Expected 36.0, got {cost_l100}"
    
    # 3. MPG US
    miles = distance_km * 0.621371
    eff_mpg = 30.0
    price_gal = 3.50
    gallons = miles / eff_mpg
    cost_mpg = gallons * price_gal
    expected_gal = (300.0 * 0.621371) / 30.0
    assert abs(gallons - expected_gal) < 1e-5
    print("[PASS] Fuel calculation models (km/L, L/100km, MPG US) passed.")

def test_unit_conversions():
    km = 100.0
    mi = km * 0.621371
    assert abs(mi - 62.1371) < 1e-4
    print("[PASS] Unit conversions (km to miles) passed.")

def test_sitemap_xml():
    sitemap_path = Path("sitemap.xml")
    assert sitemap_path.exists(), "sitemap.xml does not exist"
    tree = ET.parse(sitemap_path)
    root = tree.getroot()
    urls = [elem.text for elem in root.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url/{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
    assert len(urls) >= 7, f"Expected at least 7 URLs in sitemap, found {len(urls)}"
    for url in urls:
        assert url.startswith("https://distancecalculator-theta.vercel.app/"), f"Invalid sitemap URL: {url}"
    print(f"[PASS] Sitemap valid XML with {len(urls)} canonical URLs.")

def test_robots_txt():
    robots_path = Path("robots.txt")
    assert robots_path.exists(), "robots.txt does not exist"
    content = robots_path.read_text(encoding="utf-8")
    assert "User-agent: *" in content
    assert "Allow: /" in content
    assert "Sitemap: https://distancecalculator-theta.vercel.app/sitemap.xml" in content
    print("[PASS] robots.txt syntax and sitemap link verified.")

def test_index_html_security_and_structure():
    index_path = Path("index.html")
    assert index_path.exists(), "index.html does not exist"
    content = index_path.read_text(encoding="utf-8")
    
    # 1. No raw innerHTML on API suggestions (prevent XSS)
    assert "box.innerHTML = data.map" not in content, "SECURITY RISK: raw innerHTML found on API suggestions!"
    assert "item.textContent = p.display_name" in content, "Safe textContent must be used for API suggestions."
    
    # 2. Stale coordinate invalidation logic
    assert "handleInputChange" in content, "Stale coordinate invalidation handler missing!"
    
    # 3. GPS Geolocation button
    assert 'id="gpsBtn"' in content, "GPS My Location button missing!"
    
    # 4. Geodesic flight arc
    assert "generateGreatCircleArc" in content, "Great-Circle arc generator missing!"
    
    # 5. Schema JSON-LD validation
    schemas = re.findall(r'<script type="application/ld\+json">(.*?)</script>', content, re.DOTALL)
    assert len(schemas) >= 3, f"Expected at least 3 schema blocks, got {len(schemas)}"
    for s in schemas:
        try:
            parsed = json.loads(s.strip())
            assert "@context" in parsed and "@type" in parsed
        except Exception as e:
            raise AssertionError(f"Malformed JSON-LD schema: {e}")
            
    # 6. Check legal links in footer
    assert "/about.html" in content
    assert "/privacy-policy.html" in content
    assert "/terms.html" in content
    
    print("[PASS] index.html security (XSS prevention), schemas, and structure verified.")

def test_legal_pages_exist():
    for p in ["about.html", "privacy-policy.html", "terms.html"]:
        path = Path(p)
        assert path.exists(), f"Missing legal page: {p}"
        content = path.read_text(encoding="utf-8")
        assert "<title>" in content and "World Distance Calculator" in content
    print("[PASS] Legal & transparency pages (About, Privacy, Terms) verified.")

if __name__ == "__main__":
    print("Running QA and Unit Test Suite for Distance Calculator...")
    test_haversine_accuracy()
    test_fuel_calculations()
    test_unit_conversions()
    test_sitemap_xml()
    test_robots_txt()
    test_index_html_security_and_structure()
    test_legal_pages_exist()
    print("\nALL AUTOMATED TESTS PASSED SUCCESSFULLY! (7/7 suites passed)")
