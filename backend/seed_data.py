"""Reference data for Lahore: REAL facilities only, no invented availability.

- Hospitals: real government and private hospitals; coordinates checked against OpenStreetMap / Wikipedia.
  Department lists are each hospital's main publicly known departments.
- Pharmacies: real pharmacies from OpenStreetMap (osm_pharmacies.py).
- Blood banks: real blood banks / donation centres in Lahore (some locations are area-level, marked approximate).
- Beds, doctors on duty, machine status, medicine stock and blood units are NOT seeded.
  They only exist once a staff member reports them through the staff portal.
"""
from osm_pharmacies import PHARMACIES

# id, name, nameUr, lat, lon, departments, ownership
HOSPITALS = [
    ("mayo", "Mayo Hospital", "میو ہسپتال", 31.5711, 74.3154,
     ["Emergency", "Medicine", "Surgery", "Cardiology", "Orthopaedics", "ICU", "Burns", "Paediatrics"], "government"),
    ("services", "Services Hospital", "سروسز ہسپتال", 31.5413, 74.3331,
     ["Emergency", "Medicine", "Surgery", "Gynae/Obstetrics", "Orthopaedics", "ICU", "Paediatrics"], "government"),
    ("jinnah", "Jinnah Hospital", "جناح ہسپتال", 31.4845, 74.2970,
     ["Emergency", "Medicine", "Surgery", "Cardiology", "Gynae/Obstetrics", "Orthopaedics", "ICU", "Burns"], "government"),
    ("gangaram", "Sir Ganga Ram Hospital", "سر گنگا رام ہسپتال", 31.5544, 74.3207,
     ["Emergency", "Medicine", "Surgery", "Gynae/Obstetrics", "Paediatrics", "ICU"], "government"),
    ("lgh", "Lahore General Hospital", "لاہور جنرل ہسپتال", 31.4554, 74.3501,
     ["Emergency", "Medicine", "Surgery", "Orthopaedics", "ICU", "Cardiology"], "government"),
    ("childrens", "Children's Hospital Lahore", "چلڈرن ہسپتال", 31.4801, 74.3430,
     ["Emergency", "Paediatrics", "Surgery", "ICU"], "government"),
    ("pic", "Punjab Institute of Cardiology", "پنجاب انسٹیٹیوٹ آف کارڈیالوجی", 31.5378, 74.3355,
     ["Emergency", "Cardiology", "ICU"], "government"),
    ("zayed", "Shaikh Zayed Hospital", "شیخ زاید ہسپتال", 31.5091, 74.3090,
     ["Emergency", "Medicine", "Surgery", "Cardiology", "Gynae/Obstetrics", "ICU", "Paediatrics"], "government"),
    ("ladyaitchison", "Lady Aitchison Hospital", "لیڈی ایچیسن ہسپتال", 31.5738, 74.3155,
     ["Emergency", "Gynae/Obstetrics", "Paediatrics"], "government"),
    ("ladywillingdon", "Lady Willingdon Hospital", "لیڈی ولنگڈن ہسپتال", 31.5880, 74.3110,
     ["Emergency", "Gynae/Obstetrics", "Paediatrics"], "government"),
    # private (fees apply); coordinates from OpenStreetMap
    ("doctors", "Doctors Hospital", "ڈاکٹرز ہسپتال", 31.4795, 74.2801,
     ["Emergency", "Medicine", "Surgery", "Cardiology", "Gynae/Obstetrics", "Paediatrics", "Orthopaedics", "ICU"], "private"),
    ("hameedlatif", "Hameed Latif Hospital", "حمید لطیف ہسپتال", 31.5119, 74.3276,
     ["Emergency", "Medicine", "Surgery", "Gynae/Obstetrics", "Paediatrics", "ICU"], "private"),
    ("ittefaq", "Ittefaq Hospital", "اتفاق ہسپتال", 31.4757, 74.3375,
     ["Emergency", "Medicine", "Surgery", "Cardiology", "Gynae/Obstetrics", "Paediatrics", "Orthopaedics", "ICU"], "private"),
    ("fatimamemorial", "Fatima Memorial Hospital", "فاطمہ میموریل ہسپتال", 31.5356, 74.3280,
     ["Emergency", "Medicine", "Surgery", "Gynae/Obstetrics", "Paediatrics", "Orthopaedics", "ICU"], "private"),
    ("surgimed", "Surgimed Hospital", "سرجیمیڈ ہسپتال", 31.5381, 74.3513,
     ["Emergency", "Medicine", "Surgery", "Orthopaedics", "ICU"], "private"),
    ("omar", "Omar Hospital", "عمر ہسپتال", 31.5371, 74.3381,
     ["Emergency", "Medicine", "Cardiology", "Surgery", "ICU"], "private"),
    ("evercare", "Evercare Hospital", "ایورکیئر ہسپتال", 31.4370, 74.2809,
     ["Emergency", "Medicine", "Surgery", "Cardiology", "Gynae/Obstetrics", "Paediatrics", "Orthopaedics", "ICU"], "private"),
    ("farooq", "Farooq Hospital", "فاروق ہسپتال", 31.4654, 74.2358,
     ["Emergency", "Medicine", "Surgery", "Gynae/Obstetrics", "Paediatrics", "ICU"], "private"),
    ("bahriaintl", "Bahria International Hospital", "بحریہ انٹرنیشنل ہسپتال", 31.3877, 74.1878,
     ["Emergency", "Medicine", "Surgery", "Cardiology", "Gynae/Obstetrics", "Paediatrics", "Orthopaedics", "ICU"], "private"),
]

# id, name, lat, lon, precision ("exact" = building, "area" = neighbourhood-level)
BLOOD_BANKS = [
    ("bb-lgh", "Blood Bank, Lahore General Hospital", 31.4561, 74.3505, "exact"),
    ("bb-aadil", "Lahore Blood Bank & Transfusion Centre (Aadil Hospital, DHA)", 31.4891, 74.3802, "exact"),
    ("bb-sundas", "Sundas Foundation, Shadman", 31.5343, 74.3303, "area"),
    ("bb-husaini", "Husaini Blood Bank, Jail Road, Shadman", 31.5360, 74.3330, "area"),
    ("bb-fatimid", "Fatimid Foundation, Johar Town", 31.4710, 74.2725, "area"),
    ("bb-redcrescent", "Pakistan Red Crescent Society, Mozang Chungi", 31.5488, 74.3150, "area"),
]

BLOOD_GROUPS = ["O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-"]
EQUIPMENT = ["CT", "MRI", "XRay", "Dialysis", "Ventilator", "Oxygen"]

# Medicine reference (real brand -> active ingredient). No prices: those come only from pharmacy reports.
# key, name, salt (active ingredient), strength
MEDICINES = [
    ("panadol-500", "Panadol 500mg", "Paracetamol", "500mg"),
    ("calpol-500", "Calpol 500mg", "Paracetamol", "500mg"),
    ("paracetamol-500", "Paracetamol 500mg (generic)", "Paracetamol", "500mg"),
    ("augmentin-625", "Augmentin 625mg", "Amoxicillin + Clavulanic acid", "625mg"),
    ("amclav-625", "Amclav 625mg", "Amoxicillin + Clavulanic acid", "625mg"),
    ("coamoxiclav-625", "Co-amoxiclav 625mg (generic)", "Amoxicillin + Clavulanic acid", "625mg"),
    ("brufen-400", "Brufen 400mg", "Ibuprofen", "400mg"),
    ("ibuprofen-400", "Ibuprofen 400mg (generic)", "Ibuprofen", "400mg"),
    ("flagyl-400", "Flagyl 400mg", "Metronidazole", "400mg"),
    ("metronidazole-400", "Metronidazole 400mg (generic)", "Metronidazole", "400mg"),
    ("risek-20", "Risek 20mg", "Omeprazole", "20mg"),
    ("omeprazole-20", "Omeprazole 20mg (generic)", "Omeprazole", "20mg"),
    ("nexum-40", "Nexum 40mg", "Esomeprazole", "40mg"),
    ("esomeprazole-40", "Esomeprazole 40mg (generic)", "Esomeprazole", "40mg"),
    ("glucophage-500", "Glucophage 500mg", "Metformin", "500mg"),
    ("metformin-500", "Metformin 500mg (generic)", "Metformin", "500mg"),
    ("disprin-300", "Disprin 300mg", "Aspirin", "300mg"),
    ("loprin-75", "Loprin 75mg", "Aspirin", "75mg"),
    ("aspirin-75", "Aspirin 75mg (generic)", "Aspirin", "75mg"),
    ("lipitor-20", "Lipitor 20mg", "Atorvastatin", "20mg"),
    ("atorvastatin-20", "Atorvastatin 20mg (generic)", "Atorvastatin", "20mg"),
    ("norvasc-5", "Norvasc 5mg", "Amlodipine", "5mg"),
    ("amlodipine-5", "Amlodipine 5mg (generic)", "Amlodipine", "5mg"),
    ("concor-5", "Concor 5mg", "Bisoprolol", "5mg"),
    ("bisoprolol-5", "Bisoprolol 5mg (generic)", "Bisoprolol", "5mg"),
    ("plavix-75", "Plavix 75mg", "Clopidogrel", "75mg"),
    ("clopidogrel-75", "Clopidogrel 75mg (generic)", "Clopidogrel", "75mg"),
    ("angised-05", "Angised 0.5mg", "Glyceryl trinitrate", "0.5mg"),
    ("ventolin-inh", "Ventolin Inhaler 100mcg", "Salbutamol", "100mcg/dose"),
    ("salbutamol-inh", "Salbutamol Inhaler 100mcg (generic)", "Salbutamol", "100mcg/dose"),
    ("ponstan-250", "Ponstan 250mg", "Mefenamic acid", "250mg"),
    ("ciproxin-500", "Ciproxin 500mg", "Ciprofloxacin", "500mg"),
    ("ciprofloxacin-500", "Ciprofloxacin 500mg (generic)", "Ciprofloxacin", "500mg"),
    ("zyrtec-10", "Zyrtec 10mg", "Cetirizine", "10mg"),
    ("cetirizine-10", "Cetirizine 10mg (generic)", "Cetirizine", "10mg"),
    ("ors", "ORS sachet", "Oral rehydration salts", "1 sachet"),
    ("mixtard-3070", "Mixtard 30/70 insulin", "Human insulin 30/70", "100IU/ml"),
    ("humulin-7030", "Humulin 70/30 insulin", "Human insulin 30/70", "100IU/ml"),
    ("lasix-40", "Lasix 40mg", "Furosemide", "40mg"),
    ("furosemide-40", "Furosemide 40mg (generic)", "Furosemide", "40mg"),
    ("rocephin-1g", "Rocephin 1g injection", "Ceftriaxone", "1g"),
    ("ceftriaxone-1g", "Ceftriaxone 1g injection (generic)", "Ceftriaxone", "1g"),
]

# General, patient-friendly information per active ingredient (not medical advice).
# rx: "rx" = prescription needed, "otc" = usually sold without prescription, "ask" = ask your pharmacist
MED_INFO = {
    "Paracetamol": ("Pain relief and fever", "درد اور بخار کے لیے", "otc"),
    "Amoxicillin + Clavulanic acid": ("Antibiotic for bacterial infections (chest, ear, throat, urine, skin)", "بیکٹیریا والے انفیکشن کے لیے اینٹی بائیوٹک", "rx"),
    "Ibuprofen": ("Pain, swelling and fever", "درد، سوجن اور بخار کے لیے", "otc"),
    "Metronidazole": ("Certain bacterial and parasitic infections, e.g. stomach and gut infections", "معدے اور آنتوں کے بعض انفیکشن کے لیے", "rx"),
    "Omeprazole": ("Acidity, heartburn and stomach ulcers", "تیزابیت، سینے کی جلن اور معدے کے السر کے لیے", "ask"),
    "Esomeprazole": ("Acidity, heartburn and stomach ulcers", "تیزابیت، سینے کی جلن اور معدے کے السر کے لیے", "ask"),
    "Metformin": ("Type 2 diabetes (lowers blood sugar)", "شوگر (ٹائپ 2) کنٹرول کرنے کے لیے", "rx"),
    "Aspirin": ("300mg: pain and fever. 75mg: low dose to help prevent heart attack and stroke, only if a doctor advises", "300 ملی گرام: درد اور بخار۔ 75 ملی گرام: ڈاکٹر کے مشورے سے دل کے دورے سے بچاؤ", "ask"),
    "Atorvastatin": ("Lowers cholesterol", "کولیسٹرول کم کرنے کے لیے", "rx"),
    "Amlodipine": ("High blood pressure and angina (heart-related chest pain)", "ہائی بلڈ پریشر اور دل کے درد کے لیے", "rx"),
    "Bisoprolol": ("High blood pressure and some heart conditions", "ہائی بلڈ پریشر اور دل کی بعض بیماریوں کے لیے", "rx"),
    "Clopidogrel": ("Prevents blood clots after a heart attack, stent or stroke", "دل کے دورے، اسٹنٹ یا فالج کے بعد خون جمنے سے بچاؤ", "rx"),
    "Glyceryl trinitrate": ("Fast relief of angina (heart-related chest pain), under the tongue", "دل کے درد میں فوری آرام (زبان کے نیچے)", "rx"),
    "Salbutamol": ("Quick relief of asthma and wheezing", "دمہ اور سانس کی گھٹن میں فوری آرام", "rx"),
    "Mefenamic acid": ("Pain, including period pain", "درد، بشمول ماہواری کا درد", "ask"),
    "Ciprofloxacin": ("Antibiotic for bacterial infections, e.g. urine infections and typhoid", "پیشاب کے انفیکشن اور ٹائیفائیڈ وغیرہ کے لیے اینٹی بائیوٹک", "rx"),
    "Cetirizine": ("Allergies: sneezing, runny nose, itching, hives", "الرجی: چھینکیں، ناک بہنا، خارش", "otc"),
    "Oral rehydration salts": ("Replaces water and salts lost in diarrhoea or vomiting", "دست یا الٹی میں پانی اور نمکیات کی کمی پوری کرنے کے لیے", "otc"),
    "Human insulin 30/70": ("Diabetes: controls blood sugar (injection)", "شوگر کنٹرول کرنے کے لیے انسولین (انجکشن)", "rx"),
    "Furosemide": ("Removes extra fluid (swelling, heart failure) and lowers blood pressure", "جسم سے اضافی پانی نکالنے اور بلڈ پریشر کے لیے", "rx"),
    "Ceftriaxone": ("Injection antibiotic for serious infections, given by a doctor or nurse", "شدید انفیکشن کے لیے اینٹی بائیوٹک انجکشن (ڈاکٹر/نرس لگائیں)", "rx"),
}

# Real emergency ambulance helplines (no simulated vehicles)
HELPLINES = [
    {"name": "Rescue 1122 (Punjab Emergency Service)", "number": "1122"},
    {"name": "Edhi Ambulance", "number": "115"},
]


DEPT_SIZE = {"Emergency": 30, "Medicine": 50, "Surgery": 40, "Cardiology": 30, "Paediatrics": 35,
             "Gynae/Obstetrics": 40, "Orthopaedics": 30, "ICU": 14, "Burns": 12}
_FIRST_F = ["Sana", "Ayesha", "Fatima", "Hira", "Mehwish", "Saba", "Amna", "Rabia", "Zara", "Maryam", "Nida", "Iqra"]
_FIRST_M = ["Ahmed", "Usman", "Bilal", "Faisal", "Hamza", "Imran", "Kamran", "Saad", "Zain", "Ali", "Omer", "Waqas"]
_LAST = ["Khan", "Siddiqui", "Raza", "Tariq", "Hussain", "Iqbal", "Sheikh", "Butt", "Javed", "Malik", "Qureshi", "Aslam"]


def build_demo_items():
    """Clearly-flagged DEMO availability (demo=True) so the pilot can be explored before real staff report.
    Rows carry demoAgeMin instead of a fixed time; the API shows them as 'demo' and lets users switch them off.
    A real staff report on the same item overwrites the demo row."""
    import random
    rnd = random.Random(7)
    items = []
    used = set()

    def name(female):
        for _ in range(50):
            n = f"Dr {rnd.choice(_FIRST_F if female else _FIRST_M)} {rnd.choice(_LAST)}"
            if n not in used:
                used.add(n)
                return n
        return n

    def row(pk, kind, key, **kw):
        return {"pk": pk, "sk": f"RES#{kind}#{key}", "kind": kind, "key": key, "demo": True,
                "demoAgeMin": rnd.randint(2, 75), "updatedBy": "demo sample", **kw}

    for hid, _n, _u, _la, _lo, depts, ownership in HOSPITALS:
        pk = f"FACILITY#hosp-{hid}"
        private = ownership == "private"
        for d in depts:
            size = max(4, int(DEPT_SIZE[d] * (0.4 if private else 1)))
            free = rnd.choice([0, 0, 1, 2, 3, 4, 6, 8] if not private else [0, 1, 2, 3, 4, 5])
            items.append(row(pk, "bed", d, free=min(free, size)))
            for j in range(2 if d in ("Emergency", "Medicine") else 1):
                female = d == "Gynae/Obstetrics" or hid.startswith("lady") or rnd.random() < 0.35
                if hid == "mayo" and d == "Medicine" and j == 0:
                    n, female = "Dr Sana Khan", True
                else:
                    n = name(female)
                key = n.lower().replace("dr ", "").replace(" ", "-")
                items.append(row(pk, "doctor", key, name=n, dept=d, gender="F" if female else "M",
                                 onDuty=rnd.random() < 0.75, shiftEnds=rnd.choice(["14:00", "20:00", "22:00", "08:00"])))
        for e in (EQUIPMENT if len(depts) > 4 else ["XRay", "Oxygen", "Ventilator"]):
            status = "working" if e == "Oxygen" else rnd.choices(["working", "busy", "down"], [0.75, 0.13, 0.12])[0]
            items.append(row(pk, "equipment", e, status=status))
    for pid, _n, _la, _lo in PHARMACIES[::2]:  # about half the pharmacies
        for key, mname, salt, strength in MEDICINES:
            if rnd.random() < 0.55:
                q = rnd.choice([0, 3, 6, 10, 15, 20, 30])
                items.append(row(f"FACILITY#{pid}", "medicine", key, qty=q))
    for bid, *_ in BLOOD_BANKS:
        for g in BLOOD_GROUPS:
            lo, hi = (0, 3) if g.endswith("-") else (2, 15)
            items.append(row(f"FACILITY#{bid}", "blood", g, units=rnd.randint(lo, hi)))
    return items


def build_items(now=None):
    """META rows for real facilities only. No availability rows: those come from staff reports."""
    items = []
    for hid, name, name_ur, lat, lon, depts, ownership in HOSPITALS:
        items.append({"pk": f"FACILITY#hosp-{hid}", "sk": "META", "type": "hospital", "id": f"hosp-{hid}",
                      "name": name, "nameUr": name_ur, "lat": lat, "lon": lon, "departments": depts,
                      "ownership": ownership, "locationPrecision": "exact", "source": "OpenStreetMap / Wikipedia"})
    for pid, name, lat, lon in PHARMACIES:
        items.append({"pk": f"FACILITY#{pid}", "sk": "META", "type": "pharmacy", "id": pid, "name": name,
                      "lat": lat, "lon": lon, "locationPrecision": "exact", "source": "OpenStreetMap"})
    for bid, name, lat, lon, precision in BLOOD_BANKS:
        items.append({"pk": f"FACILITY#{bid}", "sk": "META", "type": "bloodbank", "id": bid, "name": name,
                      "lat": lat, "lon": lon, "locationPrecision": precision, "source": "public listings"})
    return items
