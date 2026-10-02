"""Simulated pilot data for Lahore. Coordinates are approximate. All availability is SIMULATED."""
import random
import time

# id, name, nameUr, lat, lon, departments, sehatCard
HOSPITALS = [
    ("mayo", "Mayo Hospital", "میو ہسپتال", 31.5767, 74.3127,
     ["Emergency", "Medicine", "Surgery", "Cardiology", "Orthopaedics", "ICU", "Burns", "Paediatrics"], True),
    ("services", "Services Hospital", "سروسز ہسپتال", 31.5408, 74.3370,
     ["Emergency", "Medicine", "Surgery", "Gynae/Obstetrics", "Orthopaedics", "ICU", "Paediatrics"], True),
    ("jinnah", "Jinnah Hospital", "جناح ہسپتال", 31.4846, 74.2972,
     ["Emergency", "Medicine", "Surgery", "Cardiology", "Gynae/Obstetrics", "Orthopaedics", "ICU", "Burns"], True),
    ("gangaram", "Sir Ganga Ram Hospital", "سر گنگا رام ہسپتال", 31.5560, 74.3240,
     ["Emergency", "Medicine", "Surgery", "Gynae/Obstetrics", "Paediatrics", "ICU"], True),
    ("lgh", "Lahore General Hospital", "لاہور جنرل ہسپتال", 31.4560, 74.3535,
     ["Emergency", "Medicine", "Surgery", "Orthopaedics", "ICU", "Cardiology"], True),
    ("childrens", "Children's Hospital Lahore", "چلڈرن ہسپتال", 31.4940, 74.3330,
     ["Emergency", "Paediatrics", "Surgery", "ICU"], True),
    ("pic", "Punjab Institute of Cardiology", "پنجاب انسٹیٹیوٹ آف کارڈیالوجی", 31.5370, 74.3420,
     ["Emergency", "Cardiology", "ICU"], True),
    ("zayed", "Shaikh Zayed Hospital", "شیخ زاید ہسپتال", 31.5126, 74.3031,
     ["Emergency", "Medicine", "Surgery", "Cardiology", "Gynae/Obstetrics", "ICU", "Paediatrics"], False),
    ("ladyaitchison", "Lady Aitchison Hospital", "لیڈی ایچیسن ہسپتال", 31.5725, 74.3150,
     ["Emergency", "Gynae/Obstetrics", "Paediatrics"], True),
    ("ladywillingdon", "Lady Willingdon Hospital", "لیڈی ولنگڈن ہسپتال", 31.5880, 74.3110,
     ["Emergency", "Gynae/Obstetrics", "Paediatrics"], True),
]

DEPT_SIZE = {"Emergency": 40, "Medicine": 60, "Surgery": 50, "Cardiology": 40, "Paediatrics": 40,
             "Gynae/Obstetrics": 45, "Orthopaedics": 35, "ICU": 16, "Burns": 14}

MALE = ["Dr Ahmed Raza", "Dr Usman Tariq", "Dr Bilal Hussain", "Dr Faisal Iqbal", "Dr Hamza Sheikh",
        "Dr Imran Butt", "Dr Kamran Javed", "Dr Saad Mahmood", "Dr Zain Qureshi", "Dr Ali Haider",
        "Dr Omer Farooq", "Dr Waqas Anwar", "Dr Junaid Akhtar", "Dr Adnan Malik", "Dr Haris Nadeem"]
FEMALE = ["Dr Sana Khan", "Dr Ayesha Siddiqui", "Dr Fatima Noor", "Dr Hira Aslam", "Dr Mehwish Ali",
          "Dr Saba Rehman", "Dr Amna Yousaf", "Dr Rabia Naveed", "Dr Zara Imtiaz", "Dr Maryam Saleem",
          "Dr Nida Hassan", "Dr Iqra Shafiq", "Dr Kiran Abbas", "Dr Sadia Latif", "Dr Hina Arshad"]

EQUIPMENT = ["CT", "MRI", "XRay", "Dialysis", "Ventilator", "Oxygen"]

# key, name, salt (active ingredient), strength, priceRs (per pack, simulated)
MEDICINES = [
    ("panadol-500", "Panadol 500mg", "Paracetamol", "500mg", 45),
    ("calpol-500", "Calpol 500mg", "Paracetamol", "500mg", 40),
    ("paracetamol-500", "Paracetamol 500mg (generic)", "Paracetamol", "500mg", 20),
    ("augmentin-625", "Augmentin 625mg", "Amoxicillin + Clavulanic acid", "625mg", 520),
    ("amclav-625", "Amclav 625mg", "Amoxicillin + Clavulanic acid", "625mg", 390),
    ("coamoxiclav-625", "Co-amoxiclav 625mg (generic)", "Amoxicillin + Clavulanic acid", "625mg", 280),
    ("brufen-400", "Brufen 400mg", "Ibuprofen", "400mg", 70),
    ("ibuprofen-400", "Ibuprofen 400mg (generic)", "Ibuprofen", "400mg", 35),
    ("flagyl-400", "Flagyl 400mg", "Metronidazole", "400mg", 60),
    ("metronidazole-400", "Metronidazole 400mg (generic)", "Metronidazole", "400mg", 30),
    ("risek-20", "Risek 20mg", "Omeprazole", "20mg", 260),
    ("omeprazole-20", "Omeprazole 20mg (generic)", "Omeprazole", "20mg", 120),
    ("nexum-40", "Nexum 40mg", "Esomeprazole", "40mg", 390),
    ("esomeprazole-40", "Esomeprazole 40mg (generic)", "Esomeprazole", "40mg", 190),
    ("glucophage-500", "Glucophage 500mg", "Metformin", "500mg", 150),
    ("metformin-500", "Metformin 500mg (generic)", "Metformin", "500mg", 70),
    ("disprin-300", "Disprin 300mg", "Aspirin", "300mg", 30),
    ("loprin-75", "Loprin 75mg", "Aspirin", "75mg", 55),
    ("aspirin-75", "Aspirin 75mg (generic)", "Aspirin", "75mg", 25),
    ("lipitor-20", "Lipitor 20mg", "Atorvastatin", "20mg", 620),
    ("atorvastatin-20", "Atorvastatin 20mg (generic)", "Atorvastatin", "20mg", 240),
    ("norvasc-5", "Norvasc 5mg", "Amlodipine", "5mg", 480),
    ("amlodipine-5", "Amlodipine 5mg (generic)", "Amlodipine", "5mg", 150),
    ("concor-5", "Concor 5mg", "Bisoprolol", "5mg", 360),
    ("bisoprolol-5", "Bisoprolol 5mg (generic)", "Bisoprolol", "5mg", 170),
    ("plavix-75", "Plavix 75mg", "Clopidogrel", "75mg", 720),
    ("clopidogrel-75", "Clopidogrel 75mg (generic)", "Clopidogrel", "75mg", 260),
    ("angised-05", "Angised 0.5mg", "Glyceryl trinitrate", "0.5mg", 90),
    ("ventolin-inh", "Ventolin Inhaler 100mcg", "Salbutamol", "100mcg/dose", 420),
    ("salbutamol-inh", "Salbutamol Inhaler 100mcg (generic)", "Salbutamol", "100mcg/dose", 260),
    ("ponstan-250", "Ponstan 250mg", "Mefenamic acid", "250mg", 110),
    ("ciproxin-500", "Ciproxin 500mg", "Ciprofloxacin", "500mg", 380),
    ("ciprofloxacin-500", "Ciprofloxacin 500mg (generic)", "Ciprofloxacin", "500mg", 160),
    ("zyrtec-10", "Zyrtec 10mg", "Cetirizine", "10mg", 190),
    ("cetirizine-10", "Cetirizine 10mg (generic)", "Cetirizine", "10mg", 60),
    ("ors", "ORS sachet", "Oral rehydration salts", "1 sachet", 25),
    ("mixtard-3070", "Mixtard 30/70 insulin", "Human insulin 30/70", "100IU/ml", 1250),
    ("humulin-7030", "Humulin 70/30 insulin", "Human insulin 30/70", "100IU/ml", 1180),
    ("lasix-40", "Lasix 40mg", "Furosemide", "40mg", 85),
    ("furosemide-40", "Furosemide 40mg (generic)", "Furosemide", "40mg", 40),
    ("rocephin-1g", "Rocephin 1g injection", "Ceftriaxone", "1g", 480),
    ("ceftriaxone-1g", "Ceftriaxone 1g injection (generic)", "Ceftriaxone", "1g", 210),
]

PHARMACIES = [
    ("ph-gulberg", "Al-Shifa Pharmacy Gulberg", 31.5204, 74.3487),
    ("ph-johar", "Care Plus Pharmacy Johar Town", 31.4697, 74.2728),
    ("ph-johar2", "Al-Noor Medical Store Johar Town", 31.4630, 74.2820),
    ("ph-dha", "Medicare Chemists DHA", 31.4720, 74.4060),
    ("ph-modeltown", "Model Town Medicos", 31.4834, 74.3256),
    ("ph-iqbaltown", "Iqbal Town Pharmacy", 31.5050, 74.2900),
    ("ph-gardentown", "Garden Town Chemist", 31.5000, 74.3220),
    ("ph-shadman", "Shadman Medical Hall", 31.5390, 74.3300),
    ("ph-anarkali", "Anarkali Dawakhana", 31.5690, 74.3100),
    ("ph-township", "Township Health Pharmacy", 31.4500, 74.3100),
    ("ph-wapda", "Wapda Town Pharmacy", 31.4350, 74.2650),
    ("ph-faisaltown", "Faisal Town Medical Store", 31.4790, 74.3040),
    ("ph-samanabad", "Samanabad Pharmacy", 31.5340, 74.2980),
    ("ph-cantt", "Cantt Care Pharmacy", 31.5100, 74.3900),
    ("ph-shahdara", "Shahdara Medical Store", 31.6280, 74.2950),
    ("ph-ichhra", "Ichhra Pharmacy", 31.5300, 74.3150),
    ("ph-valencia", "Valencia Chemists", 31.4040, 74.2560),
    ("ph-bahria", "Bahria Town Pharmacy", 31.3690, 74.1830),
]

BLOOD_BANKS = [
    ("bb-mayo", "Hospital Blood Bank – Mayo", 31.5760, 74.3135),
    ("bb-services", "Hospital Blood Bank – Services", 31.5400, 74.3360),
    ("bb-jinnah", "Hospital Blood Bank – Jinnah", 31.4850, 74.2985),
    ("bb-gangaram", "Hospital Blood Bank – Ganga Ram", 31.5552, 74.3250),
    ("bb-johar", "Community Blood Bank Johar Town", 31.4680, 74.2760),
    ("bb-gulberg", "Community Blood Bank Gulberg", 31.5180, 74.3450),
]

BLOOD_GROUPS = ["O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-"]
# typical scarcity: negative groups are rare
BLOOD_RANGE = {"O+": (4, 18), "O-": (0, 3), "A+": (3, 14), "A-": (0, 3), "B+": (4, 18),
               "B-": (0, 2), "AB+": (1, 8), "AB-": (0, 2)}

AMBULANCE_POINTS = [
    (31.5600, 74.3300), (31.5200, 74.3500), (31.4700, 74.2750), (31.4800, 74.4000),
    (31.5000, 74.3100), (31.5350, 74.3000), (31.4500, 74.3200), (31.5850, 74.3150),
    (31.4400, 74.2700), (31.5100, 74.3850), (31.6200, 74.2950), (31.4900, 74.3300),
]


def build_items(now=None):
    rnd = random.Random(42)
    now = int(now or time.time())
    items = []

    def ts(max_age_min=90):
        return now - rnd.randint(1, max_age_min) * 60

    # unique fictional names: first names x surnames
    surnames = sorted({n.split()[-1] for n in MALE + FEMALE})
    used_female = [f"Dr {f.split()[1]} {s}" for f in FEMALE for s in surnames if s != f.split()[-1]]
    used_male = [f"Dr {m.split()[1]} {s}" for m in MALE for s in surnames if s != m.split()[-1]]
    rnd.shuffle(used_female)
    rnd.shuffle(used_male)
    used_female = [n for n in used_female if n != "Dr Sana Khan"]
    fi = mi = 0

    for hid, name, name_ur, lat, lon, depts, sehat in HOSPITALS:
        fid = f"hosp-{hid}"
        has_female = False
        for d in depts:
            total = DEPT_SIZE[d]
            # government hospitals run hot; a few departments full
            occ_ratio = rnd.choice([0.7, 0.8, 0.9, 0.95, 1.0, 1.0, 0.85, 0.6])
            occupied = min(total, int(total * occ_ratio))
            items.append({"pk": f"FACILITY#{fid}", "sk": f"RES#bed#{d}", "kind": "bed", "key": d,
                          "total": total, "occupied": occupied, "updatedAt": ts(), "updatedBy": "ward staff"})
            n_docs = 2 if d in ("Emergency", "Medicine", "Gynae/Obstetrics") else 1
            for j in range(n_docs):
                female = d in ("Gynae/Obstetrics",) or rnd.random() < 0.4 or hid.startswith("lady")
                if hid == "mayo" and d == "Medicine" and j == 0:
                    dname, female = "Dr Sana Khan", True  # fixed name used in the demo staff message
                elif female:
                    dname = used_female[fi % len(used_female)]; fi += 1
                else:
                    dname = used_male[mi % len(used_male)]; mi += 1
                on = rnd.random() < 0.75
                has_female = has_female or (female and on)
                dkey = dname.lower().replace("dr ", "").replace(" ", "-") + "-" + d[:4].lower()
                items.append({"pk": f"FACILITY#{fid}", "sk": f"RES#doctor#{dkey}", "kind": "doctor",
                              "key": dkey, "name": dname, "dept": d, "gender": "F" if female else "M",
                              "onDuty": on, "shiftEnds": rnd.choice(["14:00", "20:00", "08:00", "22:00"]),
                              "updatedAt": ts(), "updatedBy": "duty roster"})
        eq_list = EQUIPMENT if len(depts) > 4 else ["XRay", "Oxygen", "Ventilator"] + (["CT"] if hid == "pic" else [])
        for e in eq_list:
            status = rnd.choices(["working", "down", "busy"], [0.65, 0.2, 0.15])[0]
            if e == "Oxygen":
                status = "working"
            items.append({"pk": f"FACILITY#{fid}", "sk": f"RES#equipment#{e}", "kind": "equipment", "key": e,
                          "status": status, "queue": rnd.randint(0, 12) if status != "down" else 0,
                          "updatedAt": ts(180 if rnd.random() < 0.15 else 90), "updatedBy": "radiology desk"})
        # free dispensary in some hospitals (generic medicines, price 0)
        if hid in ("mayo", "services", "jinnah", "gangaram"):
            for key, mname, salt, strength, price in MEDICINES:
                if "(generic)" in mname or key == "ors":
                    if rnd.random() < 0.7:
                        q = rnd.randint(0, 60)
                        items.append({"pk": f"FACILITY#{fid}", "sk": f"RES#medicine#{key}", "kind": "medicine",
                                      "key": key, "name": mname, "salt": salt, "strength": strength,
                                      "inStock": q > 0, "qty": q, "priceRs": 0, "updatedAt": ts(),
                                      "updatedBy": "hospital dispensary"})
        items.append({"pk": f"FACILITY#{fid}", "sk": "META", "type": "hospital", "id": fid, "name": name,
                      "nameUr": name_ur, "lat": lat, "lon": lon, "phone": "042-0000000",
                      "sehatCard": sehat, "femaleDoctor": has_female or hid.startswith("lady"), "open24h": True})

    for pid, name, lat, lon in PHARMACIES:
        fid = pid
        items.append({"pk": f"FACILITY#{fid}", "sk": "META", "type": "pharmacy", "id": fid, "name": name,
                      "lat": lat, "lon": lon, "phone": "042-0000000", "sehatCard": False,
                      "femaleDoctor": False, "open24h": rnd.random() < 0.4})
        for key, mname, salt, strength, price in MEDICINES:
            if rnd.random() < 0.8:
                q = rnd.choice([0, 0, 2, 5, 8, 12, 20, 30, 45])
                items.append({"pk": f"FACILITY#{fid}", "sk": f"RES#medicine#{key}", "kind": "medicine", "key": key,
                              "name": mname, "salt": salt, "strength": strength, "inStock": q > 0, "qty": q,
                              "priceRs": int(price * rnd.uniform(0.95, 1.08)), "updatedAt": ts(),
                              "updatedBy": "pharmacist"})

    for bid, name, lat, lon in BLOOD_BANKS:
        fid = bid
        items.append({"pk": f"FACILITY#{fid}", "sk": "META", "type": "bloodbank", "id": fid, "name": name,
                      "lat": lat, "lon": lon, "phone": "042-0000000", "sehatCard": False,
                      "femaleDoctor": False, "open24h": True})
        for g in BLOOD_GROUPS:
            lo, hi = BLOOD_RANGE[g]
            items.append({"pk": f"FACILITY#{fid}", "sk": f"RES#blood#{g}", "kind": "blood", "key": g,
                          "units": rnd.randint(lo, hi), "updatedAt": ts(), "updatedBy": "blood bank clerk"})

    for i, (lat, lon) in enumerate(AMBULANCE_POINTS):
        items.append({"pk": f"AMBULANCE#amb-{i + 1:02d}", "sk": "META", "id": f"amb-{i + 1:02d}",
                      "type": "ALS" if i % 3 == 0 else "basic", "status": "busy" if i in (5, 9) else "available",
                      "lat": lat, "lon": lon, "updatedAt": now})

    items.append({"pk": "STATS", "sk": "GLOBAL", "searches": 0, "ambulanceRequests": 0, "medicineSearches": 0,
                  "bloodRequests": 0, "estMinutesSaved": 0, "notifications": 0, "staffUpdates": 0})
    return items
