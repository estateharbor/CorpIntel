"""Deterministic, realistic SAMPLE dataset generator for the MMR.

IMPORTANT: This produces **clearly-labeled sample data** used so the product is
fully demonstrable before a real `DATA_GOV_API_KEY` is injected. Every company
generated here carries `data_source = "sample"`. When the real data.gov.in
ingestion runs, records carry `data_source = "data.gov.in"`.

The generator is seeded (deterministic) so repeated runs upsert idempotently by
CIN. Volume + variety are tuned to power search, analytics, charts and exports.
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from typing import Dict, List

from services.city_tagger import tag_city, extract_area, extract_pin

# --- Locality tables (area -> pin) -----------------------------------------
MUMBAI_AREAS = {
    "Andheri": ["400053", "400069", "400093"], "Bandra": ["400050", "400051"],
    "Borivali": ["400066", "400092"], "Dadar": ["400014", "400028"],
    "Lower Parel": ["400013"], "Worli": ["400018", "400030"],
    "Powai": ["400076"], "Goregaon": ["400062", "400063"],
    "Malad": ["400064", "400097"], "Kandivali": ["400067", "400101"],
    "Chembur": ["400071", "400074"], "Ghatkopar": ["400077", "400086"],
    "Mulund": ["400080", "400081"], "Vile Parle": ["400056", "400057"],
    "Santacruz": ["400054", "400055"], "Vikhroli": ["400079"],
    "Sion": ["400022"], "Colaba": ["400005"], "Fort": ["400001"],
}
NAVI_MUMBAI_AREAS = {
    "Vashi": ["400703"], "Belapur": ["400614"], "Kharghar": ["410210"],
    "Airoli": ["400708"], "Nerul": ["400706"], "Panvel": ["410206"],
    "Kamothe": ["410209"], "Ghansoli": ["400701"], "Kopar Khairane": ["400709"],
    "Sanpada": ["400705"], "Turbhe": ["400705"], "Seawoods": ["400706"],
}
THANE_AREAS = {
    "Thane West": ["400601", "400604", "400607"], "Kalyan": ["421301"],
    "Dombivli": ["421201", "421202", "421203"], "Ulhasnagar": ["421001", "421003"],
    "Ambernath": ["421501", "421505"], "Badlapur": ["421503"],
    "Bhiwandi": ["421302", "421308"], "Mira Road": ["401107"],
    "Vasai": ["401201", "401202"], "Virar": ["401303", "401305"],
    "Nalasopara": ["401203", "401209"], "Naigaon": ["401208"], "Shahapur": ["421601"],
}
CITY_TABLE = {
    "Mumbai": MUMBAI_AREAS,
    "Navi Mumbai": NAVI_MUMBAI_AREAS,
    "Thane": THANE_AREAS,
}

# --- Sector definitions: (sector, sub_sector, activity, b2b_or_b2c, nic) ----
SECTORS = [
    ("Information Technology", "Software Development", "Computer programming, consultancy and related activities", "B2B", "62011"),
    ("Information Technology", "SaaS Products", "Development of software and applications, software publishing", "B2B", "58200"),
    ("Financial Services", "FinTech", "Other financial service activities, financial technology", "B2C", "64990"),
    ("Financial Services", "NBFC & Lending", "Financial leasing and credit granting", "B2C", "64910"),
    ("Pharmaceuticals", "Drug Manufacturing", "Manufacture of pharmaceuticals, medicinal chemical products", "B2B", "21001"),
    ("Healthcare", "Diagnostics & Clinics", "Human health activities, medical and dental practice", "B2C", "86100"),
    ("Manufacturing", "Engineering Goods", "Manufacture of machinery and equipment", "B2B", "28000"),
    ("Manufacturing", "Chemicals", "Manufacture of basic chemicals and chemical products", "B2B", "20119"),
    ("Textiles & Apparel", "Garments", "Manufacture of wearing apparel and textiles", "B2C", "14101"),
    ("Logistics & Supply Chain", "Freight & Warehousing", "Warehousing, storage and transport support activities", "B2B", "52109"),
    ("Real Estate", "Construction & Development", "Construction of buildings and real estate development", "B2C", "41001"),
    ("Trading", "Wholesale Trade", "Wholesale trade except of motor vehicles", "B2B", "46900"),
    ("Retail & E-commerce", "Online Retail", "Retail sale via internet and stores", "B2C", "47910"),
    ("Food & Beverages", "Food Processing", "Manufacture of food products and beverages", "B2C", "10791"),
    ("Media & Entertainment", "Digital Media", "Motion picture, video, television and content production", "B2C", "59110"),
    ("Education", "EdTech & Training", "Educational support and technical training activities", "B2C", "85500"),
    ("Consulting", "Management Consulting", "Management consultancy and business advisory activities", "B2B", "70200"),
    ("Hospitality & Tourism", "Hotels & Travel", "Accommodation, food service and travel agency activities", "B2C", "55101"),
    ("Energy", "Renewables", "Electric power generation including solar and renewable energy", "B2B", "35106"),
    ("Automotive", "Auto Components", "Manufacture of parts and accessories for motor vehicles", "B2B", "29301"),
]

NAME_PREFIX = [
    "Shree", "Sai", "Krishna", "Mahalaxmi", "Aditya", "Veer", "Anand",
    "Sagar", "Om", "Tirupati", "Rajdeep", "Yash", "Sterling", "Pinnacle",
    "Zenith", "Nexus", "Orbit", "Vertex", "Quantum", "Aarav", "Meghna",
    "Sunrise", "Galaxy", "Pioneer", "Eternal", "Bluechip", "Greenfield",
    "Westcoast", "Konkan", "Sahyadri", "Arihant", "Bharat", "Indus",
    "Matrix", "Apex", "Crest", "Stellar", "Vibrant", "Prime", "Noble",
]
NAME_CORE = [
    "Technologies", "Infotech", "Softwares", "Logistics", "Trading",
    "Exports", "Pharma", "Chemicals", "Textiles", "Engineering",
    "Constructions", "Realty", "Fintech", "Capital", "Foods",
    "Healthcare", "Diagnostics", "Solutions", "Systems", "Enterprises",
    "Industries", "Ventures", "Retail", "Apparels", "Motors", "Steel",
    "Packaging", "Media", "Consultants", "Securities", "Energy", "Hospitality",
]
SUFFIX = [
    ("Private Limited", "Private", "PTC", "U"),
    ("Private Limited", "Private", "PTC", "U"),
    ("Private Limited", "Private", "PTC", "U"),
    ("Limited", "Public", "PLC", "L"),
    ("(OPC) Private Limited", "One Person Company", "OPC", "U"),
]
STATUS_CHOICES = (["Active"] * 8) + ["Struck Off", "Under Liquidation"]
ROADS = ["MIDC Road", "Link Road", "Station Road", "SV Road", "LBS Marg",
         "Industrial Estate", "Business Park", "Tech Park", "Market Yard",
         "Sector 17", "Sector 30", "Plot No. 42", "Trade Centre"]
BUILDINGS = ["Unit", "Office", "Shop", "Gala", "Floor", "Wing", "Tower"]
FIRST_NAMES = ["Rajesh", "Amit", "Priya", "Sneha", "Vikram", "Anjali", "Suresh",
               "Neha", "Rohit", "Kavita", "Manoj", "Pooja", "Sanjay", "Deepa",
               "Arun", "Sunita", "Nikhil", "Reshma", "Gaurav", "Aishwarya"]
LAST_NAMES = ["Sharma", "Patel", "Shah", "Mehta", "Joshi", "Desai", "Kulkarni",
              "Iyer", "Nair", "Reddy", "Gupta", "Agarwal", "Pawar", "Naik",
              "Bhosale", "Jadhav", "Singh", "Kapoor", "Rao", "Chauhan"]
DESIGNATIONS = ["Director", "Managing Director", "Whole-time Director",
                "Additional Director", "Nominee Director"]


def _cin(rng: random.Random, listing: str, nic: str, year: int, ctype: str, seq: int) -> str:
    return f"{listing}{nic}MH{year}{ctype}{seq:06d}"


def generate_sample_dataset(count: int = 600, seed: int = 20260101) -> Dict[str, List[dict]]:
    """Generate companies, directors and enrichment records.

    Returns dict with keys: companies, directors, enrichment.
    """
    rng = random.Random(seed)
    now = datetime.now(timezone.utc)
    companies: List[dict] = []
    directors: List[dict] = []
    enrichment: List[dict] = []

    # City distribution weights (Mumbai heaviest)
    city_pool = (["Mumbai"] * 5) + (["Navi Mumbai"] * 3) + (["Thane"] * 3)

    used_cins = set()
    used_dins = set()

    for i in range(count):
        city = rng.choice(city_pool)
        area = rng.choice(list(CITY_TABLE[city].keys()))
        pin = rng.choice(CITY_TABLE[city][area])
        sector, sub_sector, activity, b2b, nic = rng.choice(SECTORS)
        suffix_label, company_class, ctype, listing = rng.choice(SUFFIX)
        prefix = rng.choice(NAME_PREFIX)
        core = rng.choice(NAME_CORE)
        # occasional 2-word prefix for variety
        name_base = f"{prefix} {core}"
        if rng.random() < 0.25:
            name_base = f"{prefix} {rng.choice(NAME_PREFIX)} {core}"
        name = f"{name_base} {suffix_label}"

        # Incorporation date: bias to recent years; include some in last 7 days
        r = rng.random()
        if r < 0.04:
            doi = now - timedelta(days=rng.randint(0, 6))  # "new this week"
        elif r < 0.5:
            doi = now - timedelta(days=rng.randint(7, 365 * 3))
        else:
            doi = now - timedelta(days=rng.randint(365 * 3, 365 * 16))
        year = doi.year

        seq = rng.randint(100000, 999999)
        cin = _cin(rng, listing, nic, year, ctype, seq)
        while cin in used_cins:
            seq = rng.randint(100000, 999999)
            cin = _cin(rng, listing, nic, year, ctype, seq)
        used_cins.add(cin)

        bldg = f"{rng.choice(BUILDINGS)} {rng.randint(1, 99)}"
        road = rng.choice(ROADS)
        address = f"{bldg}, {road}, {area}, {city} - {pin}, Maharashtra, India"

        authorized = rng.choice([100000, 500000, 1000000, 2500000, 5000000,
                                 10000000, 25000000, 50000000, 100000000])
        paid_up = int(authorized * rng.choice([0.1, 0.25, 0.5, 0.75, 1.0]))

        status = rng.choice(STATUS_CHOICES)
        enriched = rng.random() < 0.55

        # Verify city via tagger to keep data consistent with production logic
        tagged_city = tag_city(address)

        company = {
            "cin": cin,
            "name": name,
            "status": status,
            "company_class": company_class,
            "category": "Company limited by Shares",
            "date_of_incorporation": doi.replace(hour=0, minute=0, second=0, microsecond=0),
            "principal_activity": activity,
            "sector": sector,
            "sub_sector": sub_sector,
            "b2b_or_b2c": b2b,
            "authorized_capital": float(authorized),
            "paid_up_capital": float(paid_up),
            "roc": "RoC-Mumbai",
            "address": address,
            "city": tagged_city,
            "pin_code": pin,
            "area": extract_area(address) or area,
            "registered_state": "Maharashtra",
            "last_updated": now,
            "enriched": enriched,
            "classified": True,
            "data_source": "sample",
            "data_quality_score": 0,  # computed after enrichment below
        }

        # Directors (1-4)
        ndir = rng.randint(1, 4)
        comp_dirs = []
        for _ in range(ndir):
            din = rng.randint(10000000, 99999999)
            while din in used_dins:
                din = rng.randint(10000000, 99999999)
            used_dins.add(din)
            dname = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
            appt = doi + timedelta(days=rng.randint(0, 365))
            director = {
                "din": str(din),
                "name": dname,
                "cin": cin,
                "designation": rng.choice(DESIGNATIONS),
                "date_of_appointment": appt.replace(hour=0, minute=0, second=0, microsecond=0),
                "is_active": status == "Active" and rng.random() < 0.9,
            }
            directors.append(director)
            comp_dirs.append(director)

        # Enrichment for enriched companies
        has_gstin = has_phone = has_email = has_filings = False
        if enriched:
            slug = name_base.lower().replace(" ", "")
            gstin = f"27{rng.choice('ABCDEFGHJ')}{rng.choice('ABCDEFGH')}{rng.randint(1000,9999)}{rng.choice('PCFHL')}{rng.randint(1,9)}Z{rng.randint(1,9)}"
            phone = f"+91 {rng.choice(['98','99','97','70','81','88'])}{rng.randint(10000000, 99999999)}"
            email = f"info@{slug[:18]}.co.in"
            website = f"https://www.{slug[:18]}.co.in"
            charges = []
            if rng.random() < 0.4:
                charges.append({
                    "charge_id": str(rng.randint(100000000, 999999999)),
                    "amount": float(rng.choice([500000, 2500000, 10000000, 50000000])),
                    "holder": rng.choice(["HDFC Bank", "ICICI Bank", "State Bank of India",
                                          "Axis Bank", "Kotak Mahindra Bank", "Bajaj Finance"]),
                    "created": (doi + timedelta(days=rng.randint(30, 800))).date().isoformat(),
                    "satisfied": rng.random() < 0.3,
                })
            filings = []
            for fy in range(rng.randint(1, 3)):
                filings.append({
                    "form_type": rng.choice(["AOC-4", "MGT-7", "ADT-1"]),
                    "filing_date": (now - timedelta(days=365 * fy + rng.randint(0, 60))).date().isoformat(),
                    "status": "Filed",
                    "financial_year": f"{now.year - fy - 1}-{str(now.year - fy)[2:]}",
                })
            has_gstin, has_phone, has_email = True, True, True
            has_filings = len(filings) > 0
            enrichment.append({
                "cin": cin,
                "gstin": gstin,
                "email": email,
                "phone": phone,
                "website": website,
                "linkedin_url": f"https://www.linkedin.com/company/{slug[:24]}",
                "charges": charges,
                "filings": filings,
                "source": "sample",
                "enriched_at": now,
            })

        # data_quality_score (per spec scoring)
        score = 0
        if has_phone:
            score += 10
        if has_email:
            score += 10
        if has_gstin:
            score += 15
        if len(comp_dirs) > 0:
            score += 15
        if has_filings:
            score += 15
        if company["sector"]:
            score += 20
        if company["pin_code"]:
            score += 15
        company["data_quality_score"] = score
        companies.append(company)

    return {"companies": companies, "directors": directors, "enrichment": enrichment}
