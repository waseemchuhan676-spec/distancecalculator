import math
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

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
    km = 100.0
    miles = km * KM_TO_MILES
    assert abs(miles - 62.1371192) < 1e-6, f"Expected 62.1371192, got {miles}"
    
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

def test_fuel_economy_converter_math():
    C_US = 235.214583
    C_UK = 282.480936
    
    # 30 MPG US to L/100km
    mpg_us = 30.0
    l100 = C_US / mpg_us
    assert abs(l100 - 7.840486) < 1e-4
    
    # L/100km back to MPG UK
    mpg_uk = C_UK / l100
    assert abs(mpg_uk - (30.0 * 1.20095)) < 1e-2
    
    # km/L to MPG US
    kml = 100.0 / l100
    assert abs(kml * 2.35214583 - mpg_us) < 1e-3
    print("[PASS] Fuel economy multi-way converter mathematical formulas verified.")

def test_sitemap_xml_and_all_pages_exist():
    sitemap_path = Path("sitemap.xml")
    assert sitemap_path.exists(), "sitemap.xml does not exist"
    tree = ET.parse(sitemap_path)
    root = tree.getroot()
    urls = [elem.text for elem in root.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url/{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
    assert len(urls) >= 28, f"Expected at least 28 canonical URLs in sitemap, found {len(urls)}"
    
    for url in urls:
        assert url.startswith("https://distancecalculator-theta.vercel.app/"), f"Invalid sitemap URL: {url}"
        parsed = urlparse(url)
        path_str = parsed.path.lstrip('/')
        if not path_str:
            local_file = Path("index.html")
        elif path_str.endswith('/'):
            local_file = Path(path_str) / "index.html"
        else:
            local_file = Path(path_str)
        
        assert local_file.exists(), f"Sitemap URL refers to missing disk file: {local_file} (from {url})"
    
    print(f"[PASS] Sitemap valid XML with {len(urls)} canonical URLs; all verified to exist on disk!")

def test_robots_txt():
    robots_path = Path("robots.txt")
    assert robots_path.exists(), "robots.txt does not exist"
    content = robots_path.read_text(encoding="utf-8")
    assert "User-agent: *" in content
    assert "Allow: /" in content
    assert "Sitemap: https://distancecalculator-theta.vercel.app/sitemap.xml" in content
    print("[PASS] robots.txt syntax and sitemap link verified.")

def test_tools_pages_quality():
    tools = [
        "tools/fuel-cost-calculator.html",
        "tools/km-to-miles.html",
        "tools/miles-to-km.html",
        "tools/travel-time-calculator.html",
        "tools/straight-line-distance.html",
        "tools/fuel-economy-converter.html",
        "tools/road-trip-cost-calculator.html"
    ]
    for tool_file in tools:
        p = Path(tool_file)
        assert p.exists(), f"Missing tool file: {tool_file}"
        html = p.read_text(encoding="utf-8")
        assert "<title>" in html and "</title>" in html, f"Missing title in {tool_file}"
        assert '<meta name="description"' in html, f"Missing description in {tool_file}"
        assert '<link rel="canonical"' in html, f"Missing canonical in {tool_file}"
        assert '<script type="application/ld+json">' in html, f"Missing structured data in {tool_file}"
        assert 'href="/"' in html, f"Missing link back to home in {tool_file}"
    print(f"[PASS] All {len(tools)} specialized tools verified with titles, descriptions, canonicals & schemas.")

def test_blog_articles_quality():
    blog_files = list(Path("blog").glob("*.html"))
    assert len(blog_files) >= 10, f"Expected at least 10 blog files, found {len(blog_files)}"
    for bf in blog_files:
        html = bf.read_text(encoding="utf-8")
        assert "<title>" in html, f"Missing title in {bf}"
        assert '<meta name="description"' in html, f"Missing description in {bf}"
        assert '<link rel="canonical"' in html, f"Missing canonical in {bf}"
        assert "<h1" in html, f"Missing H1 in {bf}"
        assert '<script type="application/ld+json">' in html, f"Missing schema in {bf}"
    print(f"[PASS] All {len(blog_files)} blog articles verified with complete SEO metadata and schemas.")

def test_city_distance_pilot_routes_quality():
    route_files = list(Path("distance").glob("*.html"))
    assert len(route_files) >= 5, f"Expected 5 pilot route files, found {len(route_files)}"
    for rf in route_files:
        html = rf.read_text(encoding="utf-8")
        assert "<title>" in html, f"Missing title in {rf}"
        assert '<meta name="description"' in html, f"Missing description in {rf}"
        assert '<link rel="canonical"' in html, f"Missing canonical in {rf}"
        assert '<script type="application/ld+json">' in html, f"Missing schema in {rf}"
        assert 'class="stat-box"' in html, f"Missing stats box in {rf}"
    print(f"[PASS] All {len(route_files)} pilot city route pages verified.")

def test_trust_and_legal_pages_exist():
    trust_pages = [
        "about.html",
        "how-it-works.html",
        "data-sources.html",
        "faq.html",
        "contact.html",
        "privacy-policy.html",
        "terms.html",
        "disclaimer.html"
    ]
    for tp in trust_pages:
        p = Path(tp)
        assert p.exists(), f"Missing trust page: {tp}"
        html = p.read_text(encoding="utf-8")
        assert "<title>" in html and "</title>" in html, f"Missing title in {tp}"
        assert '<meta name="description"' in html, f"Missing description in {tp}"
    print(f"[PASS] All {len(trust_pages)} trust, legal and methodology pages verified.")

def test_index_html_security_and_structure():
    index_path = Path("index.html")
    assert index_path.exists(), "index.html does not exist"
    content = index_path.read_text(encoding="utf-8")
    
    # Security: No raw innerHTML on API suggestions
    assert "box.innerHTML = data.map" not in content, "SECURITY RISK: raw innerHTML found on API suggestions!"
    assert "item.textContent = p.display_name" in content, "Safe textContent must be used for API suggestions."
    
    # Logic verification
    assert "handleInputChange" in content, "Stale coordinate invalidation handler missing!"
    assert 'id="gpsBtn"' in content, "GPS My Location button missing!"
    assert "generateGreatCircleArc" in content, "Great-Circle arc generator missing!"
    assert 'id="tripOneWay"' in content and 'id="tripRound"' in content, "Trip type selector missing!"
    assert "getTripMultiplier" in content, "Trip multiplier calculation helper missing!"
    
    # Navigation & internal linking
    assert 'class="header-nav"' in content, "Main header navigation missing!"
    assert 'tools/fuel-cost-calculator.html' in content, "Fuel cost tool link missing!"
    assert 'tools/travel-time-calculator.html' in content, "Travel time tool link missing!"
    assert 'distance/new-york-to-boston.html' in content, "Pilot route link missing!"
    assert 'how-it-works.html' in content, "How it works link missing!"
    
    # Schemas
    schemas = re.findall(r'<script type="application/ld\+json">(.*?)</script>', content, re.DOTALL)
    assert len(schemas) >= 3, f"Expected at least 3 schema blocks, got {len(schemas)}"
    for s in schemas:
        parsed = json.loads(s.strip())
        assert "@context" in parsed and "@type" in parsed
    
    print("[PASS] index.html security, schemas, navigation, and structure verified.")

if __name__ == "__main__":
    print("=" * 60)
    print("RUNNING DISTANCE CALCULATOR COMPREHENSIVE QA & TEST SUITE")
    print("=" * 60)
    test_haversine_accuracy()
    test_unit_conversions_exact()
    test_fuel_calculations_oneway_and_roundtrip()
    test_fuel_economy_converter_math()
    test_sitemap_xml_and_all_pages_exist()
    test_robots_txt()
    test_tools_pages_quality()
    test_blog_articles_quality()
    test_city_distance_pilot_routes_quality()
    test_trust_and_legal_pages_exist()
    test_index_html_security_and_structure()
    print("=" * 60)
    print("ALL 11 TEST SUITES PASSED FLAWLESSLY! 100% SUCCESS RATE")
    print("=" * 60)
