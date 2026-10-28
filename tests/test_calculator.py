import math
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

# Exact mathematical constants as required
KM_TO_MILES = 0.621371192
MILES_TO_KM = 1.609344

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0 # Earth mean radius in km
    rad = math.radians
    dLat = rad(lat2 - lat1)
    dLon = rad(lon2 - lon1)
    a = math.sin(dLat / 2)**2 + math.cos(rad(lat1)) * math.cos(rad(lat2)) * math.sin(dLon / 2)**2
    c = 2 * math.asin(math.sqrt(max(0, min(1, a))))
    return R * c

def test_haversine_accuracy():
    # 1. Lahore (31.5204, 74.3587) to Islamabad (33.6844, 73.0479)
    dist = haversine(31.5204, 74.3587, 33.6844, 73.0479)
    assert 260 < dist < 275, f"Expected ~267 km, got {dist:.2f}"
    
    # 2. London (51.5074, -0.1278) to Paris (48.8566, 2.3522)
    dist_lp = haversine(51.5074, -0.1278, 48.8566, 2.3522)
    assert 330 < dist_lp < 350, f"Expected ~343 km, got {dist_lp:.2f}"
    
    # 3. New York (40.7128, -74.0060) to Los Angeles (34.0522, -118.2437)
    dist_ny_la = haversine(40.7128, -74.0060, 34.0522, -118.2437)
    assert 3900 < dist_ny_la < 4000, f"Expected ~3935 km, got {dist_ny_la:.2f}"
    
    # 4. Zero distance (same location)
    dist_zero = haversine(31.5204, 74.3587, 31.5204, 74.3587)
    assert dist_zero == 0.0, f"Expected 0.0, got {dist_zero}"
    print("[PASS] Haversine accuracy and zero-distance test passed.")

def test_unit_conversions_exact():
    # Test exact conversion constants
    km = 100.0
    miles = km * KM_TO_MILES
    assert abs(miles - 62.1371192) < 1e-6, f"Expected 62.1371192, got {miles}"
    
    # Test inverse conversion
    back_to_km = miles * MILES_TO_KM
    assert abs(back_to_km - 100.0) < 1e-4, f"Expected ~100.0, got {back_to_km}"
    print("[PASS] Exact unit conversions (1 km = 0.621371192 mi, 1 mi = 1.609344 km) passed.")

def test_fuel_calculations_oneway_and_roundtrip():
    distance_km = 300.0
    
    for trip_type, multiplier in [("One-way", 1), ("Round-trip", 2)]:
        trip_distance = distance_km * multiplier
        
        # 1. km/L: Required = distance / eff; Cost = Required * price
        eff_kml = 15.0
        price_kml = 2.0
        fuel_kml = trip_distance / eff_kml
        cost_kml = fuel_kml * price_kml
        assert fuel_kml == (20.0 * multiplier)
        assert cost_kml == (40.0 * multiplier)
        
        # 2. L/100km: Required = (distance / 100) * eff; Cost = Required * price
        eff_l100 = 8.0
        price_l100 = 1.50
        fuel_l100 = (trip_distance / 100.0) * eff_l100
        cost_l100 = fuel_l100 * price_l100
        assert fuel_l100 == (24.0 * multiplier)
        assert cost_l100 == (36.0 * multiplier)
        
        # 3. MPG US: Required = miles / eff; Cost = Required * price
        eff_mpg = 30.0
        price_gal = 3.50
        trip_miles = trip_distance * KM_TO_MILES
        fuel_gal = trip_miles / eff_mpg
        cost_mpg = fuel_gal * price_gal
        expected_gal = (300.0 * multiplier * KM_TO_MILES) / 30.0
        assert abs(fuel_gal - expected_gal) < 1e-5
        assert abs(cost_mpg - (expected_gal * price_gal)) < 1e-5

    print("[PASS] Fuel calculation models (km/L, L/100km, MPG US) for One-way & Round-trip passed.")

def test_sitemap_xml():
    sitemap_path = Path("sitemap.xml")
    assert sitemap_path.exists(), "sitemap.xml does not exist"
    tree = ET.parse(sitemap_path)
    root = tree.getroot()
    urls = [elem.text for elem in root.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url/{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
    assert len(urls) >= 8, f"Expected at least 8 URLs in sitemap, found {len(urls)}"
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
    
    # 5. One-way vs Round-trip trip type support
    assert 'id="tripOneWay"' in content and 'id="tripRound"' in content, "Trip type selector missing!"
    assert "getTripMultiplier" in content, "Trip multiplier calculation helper missing!"
    
    # 6. Schema JSON-LD validation
    schemas = re.findall(r'<script type="application/ld\+json">(.*?)</script>', content, re.DOTALL)
    assert len(schemas) >= 3, f"Expected at least 3 schema blocks, got {len(schemas)}"
    for s in schemas:
        try:
            parsed = json.loads(s.strip())
            assert "@context" in parsed and "@type" in parsed
        except Exception as e:
            raise AssertionError(f"Malformed JSON-LD schema: {e}")
            
    # 7. Check legal links in footer
    assert "/about.html" in content
    assert "/privacy-policy.html" in content
    assert "/terms.html" in content
    
    print("[PASS] index.html security (XSS prevention), schemas, trip-type, and structure verified.")

def test_legal_pages_exist():
    for p in ["about.html", "privacy-policy.html", "terms.html"]:
        path = Path(p)
        assert path.exists(), f"Missing legal page: {p}"
        content = path.read_text(encoding="utf-8")
        assert "<title>" in content and "World Distance Calculator" in content
    print("[PASS] Legal & transparency pages (About, Privacy, Terms) verified.")

if __name__ == "__main__":
    print("Running QA and Unit Test Suite for Distance Calculator (Day 1-5 Audit)...")
    test_haversine_accuracy()
    test_unit_conversions_exact()
    test_fuel_calculations_oneway_and_roundtrip()
    test_sitemap_xml()
    test_robots_txt()
    test_index_html_security_and_structure()
    test_legal_pages_exist()
    print("\nALL AUTOMATED TESTS PASSED SUCCESSFULLY! (7/7 suites passed)")
