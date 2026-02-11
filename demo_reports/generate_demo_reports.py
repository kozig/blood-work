#!/usr/bin/env python3
"""
Generate synthetic LifeLabs-style demo PDF reports for testing.
Uses fictional patient data with realistic blood work values.
"""
import random
from datetime import datetime, timedelta
from fpdf import FPDF


class LifeLabsReport(FPDF):
    """Generate a PDF that mimics LifeLabs report format."""

    def __init__(self, patient_name, age, gender, dob, date_of_service, reported_on):
        super().__init__()
        self.patient_name = patient_name
        self.age = age
        self.gender = gender
        self.dob = dob
        self.date_of_service = date_of_service
        self.reported_on = reported_on
        self.page_num = 0
        self.total_pages = 0

    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 8, "LifeLabs", align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 10)
        self.cell(95, 5, f"Patient: {self.patient_name}")
        self.cell(0, 5, "", new_x="LMARGIN", new_y="NEXT")
        self.cell(95, 5, f"Age: {self.age} years          Gender: {self.gender}")
        self.cell(0, 5, f"Date of Service:{self.date_of_service}", new_x="LMARGIN", new_y="NEXT")
        self.cell(95, 5, f"Date of Birth:{self.dob}")
        self.cell(0, 5, f"Reported on:{self.reported_on}", new_x="LMARGIN", new_y="NEXT")
        self.ln(3)
        # Column headers
        self.set_font("Helvetica", "B", 9)
        self.cell(60, 5, "Test")
        self.cell(15, 5, "Flag")
        self.cell(30, 5, "Result")
        self.cell(45, 5, "Reference Range - Units")
        self.cell(0, 5, "Lab Lic. #", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(0)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(2)

    def footer(self):
        self.set_y(-25)
        self.set_font("Helvetica", "", 7)
        self.cell(0, 4, "Lab -5407: KENNEDY, 6560 Kennedy Road, Mississauga, Ontario.", new_x="LMARGIN", new_y="NEXT")
        self.cell(0, 4, "Lab -5687: LifeLabs, 100 International Blvd., Toronto, Ontario.", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "B", 8)
        self.cell(40, 5, "FINAL RESULTS")
        self.cell(0, 5, f"Page {self.page_no()}")

    def add_section(self, title):
        self.set_font("Helvetica", "B", 10)
        self.cell(0, 6, title, new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 9)

    def add_result(self, test_name, result, ref_range, units, flag=""):
        if self.get_y() > 250:
            self.add_page()
        self.set_font("Helvetica", "", 9)
        # Build the line to match LifeLabs text format the parser expects:
        # "    TestName            FLAG  result    ref_range    units"
        if flag:
            line = f"    {test_name} {flag} {result} {ref_range} {units}"
        else:
            line = f"    {test_name} {result} {ref_range} {units}"
        self.cell(0, 5, line, new_x="LMARGIN", new_y="NEXT")


def generate_report(filename, patient, date_service, results_data):
    """Generate a single demo PDF report."""
    dos_dt = datetime.strptime(date_service, "%b %d %Y")
    reported_dt = dos_dt + timedelta(days=random.randint(1, 3))
    dos_str = dos_dt.strftime("%b %d %Y %H:%M").replace(" 00:00", " 08:30")
    rep_str = reported_dt.strftime("%b %d %Y %H:%M").replace(" 00:00", " 14:22")
    age = dos_dt.year - datetime.strptime(patient["dob"], "%b %d %Y").year

    pdf = LifeLabsReport(
        patient_name=patient["name"],
        age=age,
        gender=patient["gender"],
        dob=patient["dob"],
        date_of_service=f"{date_service} 08:30",
        reported_on=rep_str,
    )
    pdf.add_page()

    # Hematology
    pdf.add_section("Hematology")
    for test_name, result, ref_range, units, flag in results_data.get("hematology", []):
        pdf.add_result(test_name, result, ref_range, units, flag)

    # Differential
    if "differential" in results_data:
        pdf.add_section("Differential")
        for test_name, result, ref_range, units, flag in results_data["differential"]:
            pdf.add_result(test_name, result, ref_range, units, flag)

    # Biochemical Investigation of Anemias
    if "anemias" in results_data:
        pdf.add_section("Biochemical Investigation of Anemias")
        for test_name, result, ref_range, units, flag in results_data["anemias"]:
            pdf.add_result(test_name, result, ref_range, units, flag)

    # General Chemistry
    pdf.add_section("General Chemistry")
    for test_name, result, ref_range, units, flag in results_data.get("chemistry", []):
        pdf.add_result(test_name, result, ref_range, units, flag)

    # Muscle Enzymes
    if "muscle" in results_data:
        pdf.add_section("Muscle Enzymes")
        for test_name, result, ref_range, units, flag in results_data["muscle"]:
            pdf.add_result(test_name, result, ref_range, units, flag)

    # Lipids
    if "lipids" in results_data:
        pdf.add_section("Lipids")
        for test_name, result, ref_range, units, flag in results_data["lipids"]:
            pdf.add_result(test_name, result, ref_range, units, flag)

    # Thyroid Function
    if "thyroid" in results_data:
        pdf.add_section("Thyroid Function")
        for test_name, result, ref_range, units, flag in results_data["thyroid"]:
            pdf.add_result(test_name, result, ref_range, units, flag)

    # Adrenal Function
    if "adrenal" in results_data:
        pdf.add_section("Adrenal Function")
        for test_name, result, ref_range, units, flag in results_data["adrenal"]:
            pdf.add_result(test_name, result, ref_range, units, flag)

    # Reproductive and Gonadal
    if "reproductive" in results_data:
        pdf.add_section("Reproductive and Gonadal")
        for test_name, result, ref_range, units, flag in results_data["reproductive"]:
            pdf.add_result(test_name, result, ref_range, units, flag)

    # Bone Markers
    if "bone" in results_data:
        pdf.add_section("Bone Markers")
        for test_name, result, ref_range, units, flag in results_data["bone"]:
            pdf.add_result(test_name, result, ref_range, units, flag)

    # Serum Proteins
    if "serum_proteins" in results_data:
        pdf.add_section("Serum Proteins")
        for test_name, result, ref_range, units, flag in results_data["serum_proteins"]:
            pdf.add_result(test_name, result, ref_range, units, flag)

    pdf.output(filename)
    print(f"Generated: {filename}")


def vary(base, pct=0.08):
    """Add random variation to a base value."""
    return round(base * (1 + random.uniform(-pct, pct)), 2)


def vary_int(base, pct=0.08):
    """Add random variation to an integer base value."""
    return int(round(base * (1 + random.uniform(-pct, pct))))


# Fictional patient for demo purposes
PATIENT = {
    "name": "DEMO, PATIENT",
    "gender": "M",
    "dob": "Jan 15 1985",
}

# Report dates (spread across time for trend visualization)
REPORT_DATES = [
    "Jun 15 2023",
    "Dec 10 2023",
    "Jun 20 2024",
    "Dec 05 2024",
    "Jun 10 2025",
]

# Base values (normal healthy male ~40 years)
# Each report will vary these and occasionally push some out of range
BASE = {
    "wbc": 6.0, "rbc": 5.2, "hemoglobin": 155, "hematocrit": 0.45,
    "mcv": 87, "mch": 29.5, "mchc": 340, "rdw": 12.2, "platelets": 300,
    "neutrophils": 3.3, "lymphocytes": 2.0, "monocytes": 0.5,
    "eosinophils": 0.1, "basophils": 0.0,
    "iron": 22.0, "transferrin": 2.8, "transferrin_sat": 0.30,
    "tibc": 70, "b12": 280,
    "hba1c": 5.4, "sodium": 141, "potassium": 4.3, "creatinine": 82,
    "egfr": 100, "alp": 85, "ggt": 55, "alt": 35, "ast": 28,
    "creatine_kinase": 60,
    "triglyceride": 1.5, "cholesterol": 4.2, "hdl": 1.1, "ldl": 2.5,
    "tsh": 2.5,
    "cortisol": 420,
    "testosterone": 12.0, "testosterone_free": 280,
    "vitamin_d": 85,
    "crp": 0.8,
    "glucose_fasting": 5.0,
}

# Trends: simulate gradual changes over time
# Report 1-5 modifications (some values improving, some worsening)
TRENDS = [
    # Report 1 (Jun 2023) - baseline, slightly elevated GGT, low vitamin D
    {"ggt_mult": 1.6, "vitamin_d_mult": 0.75, "hdl_mult": 0.88, "b12_mult": 1.1},
    # Report 2 (Dec 2023) - GGT still high, vitamin D lower (winter)
    {"ggt_mult": 1.8, "vitamin_d_mult": 0.70, "hdl_mult": 0.90, "b12_mult": 1.0},
    # Report 3 (Jun 2024) - GGT improving, vitamin D recovering
    {"ggt_mult": 1.3, "vitamin_d_mult": 0.95, "hdl_mult": 0.95, "b12_mult": 0.95},
    # Report 4 (Dec 2024) - GGT near normal, vitamin D dips again
    {"ggt_mult": 1.1, "vitamin_d_mult": 0.80, "hdl_mult": 1.0, "b12_mult": 0.90},
    # Report 5 (Jun 2025) - mostly normalized
    {"ggt_mult": 1.0, "vitamin_d_mult": 1.05, "hdl_mult": 1.02, "b12_mult": 0.95},
]


def build_results(report_idx):
    """Build result data for a specific report index."""
    t = TRENDS[report_idx]

    wbc = vary(BASE["wbc"])
    rbc = vary(BASE["rbc"])
    hgb = vary_int(BASE["hemoglobin"])
    hct = round(vary(BASE["hematocrit"]), 3)
    mcv = vary_int(BASE["mcv"])
    mch = vary(BASE["mch"])
    mchc = vary_int(BASE["mchc"])
    rdw = vary(BASE["rdw"])
    platelets = vary_int(BASE["platelets"])

    neutrophils = vary(BASE["neutrophils"])
    lymphocytes = vary(BASE["lymphocytes"])
    monocytes = vary(BASE["monocytes"])
    eosinophils = round(vary(BASE["eosinophils"], 0.5), 1)
    basophils = round(random.choice([0.0, 0.0, 0.1]), 1)

    iron = vary(BASE["iron"])
    transferrin = vary(BASE["transferrin"])
    transferrin_sat = vary(BASE["transferrin_sat"])
    tibc = vary_int(BASE["tibc"])
    b12 = vary_int(BASE["b12"] * t["b12_mult"])
    b12_flag = "LO" if b12 < 220 else ""

    hba1c = vary(BASE["hba1c"], 0.05)
    sodium = vary_int(BASE["sodium"], 0.02)
    potassium = vary(BASE["potassium"], 0.05)
    creatinine = vary_int(BASE["creatinine"])
    egfr = vary_int(BASE["egfr"])
    alp = vary_int(BASE["alp"])
    ggt = vary_int(BASE["ggt"] * t["ggt_mult"])
    ggt_flag = "HI" if ggt >= 65 else ""
    alt = vary_int(BASE["alt"])
    alt_flag = "HI" if alt >= 50 else ""
    ast = vary_int(BASE["ast"])
    ast_flag = "HI" if ast >= 35 else ""

    ck = vary_int(BASE["creatine_kinase"])

    trig = vary(BASE["triglyceride"])
    chol = vary(BASE["cholesterol"])
    hdl = vary(BASE["hdl"] * t["hdl_mult"])
    hdl_flag = "LO" if hdl < 1.0 else ""
    ldl = vary(BASE["ldl"])

    tsh = vary(BASE["tsh"])

    cortisol = vary_int(BASE["cortisol"])

    testosterone = vary(BASE["testosterone"])
    testosterone_free = vary_int(BASE["testosterone_free"])
    free_t_flag = "LO" if testosterone_free < 196 else ""

    vitamin_d = vary(BASE["vitamin_d"] * t["vitamin_d_mult"])
    vitamin_d_flag = "LO" if vitamin_d < 75.0 else ""

    crp = vary(BASE["crp"], 0.3)

    glucose = vary(BASE["glucose_fasting"], 0.06)

    results = {
        "hematology": [
            ("WBC", wbc, "4.0 - 11.0", "x E9/L", ""),
            ("RBC", rbc, "4.50 - 6.00", "x E12/L", ""),
            ("Hemoglobin", hgb, "135 - 175", "g/L", ""),
            ("Hematocrit", hct, "0.400 - 0.500", "L/L", ""),
            ("MCV", mcv, "80 - 100", "fL", ""),
            ("MCH", mch, "27.5 - 33.0", "pg", ""),
            ("MCHC", mchc, "305 - 360", "g/L", ""),
            ("RDW", rdw, "11.5 - 14.5", "%", ""),
            ("Platelet Count", platelets, "150 - 400", "x E9/L", ""),
        ],
        "differential": [
            ("Neutrophils", neutrophils, "2.0 - 7.5", "x E9/L", ""),
            ("Lymphocytes", lymphocytes, "1.0 - 3.5", "x E9/L", ""),
            ("Monocytes", monocytes, "0.2 - 1.0", "x E9/L", ""),
            ("Eosinophils", eosinophils, "0.0 - 0.5", "x E9/L", ""),
            ("Basophils", basophils, "0.0 - 0.2", "x E9/L", ""),
            ("Immature Granulocytes", 0.0, "0.0 - 0.1", "x E9/L", ""),
        ],
        "anemias": [
            ("Iron", iron, "10.6-33.8", "umol/L", ""),
            ("Transferrin", transferrin, "2.00-3.30", "g/L", ""),
            ("Transferrin Saturation", transferrin_sat, "0.13-0.50", "", ""),
            ("TIBC", tibc, "50-83", "umol/L", ""),
            ("Vitamin B12", b12, ">220", "pmol/L", b12_flag),
        ],
        "chemistry": [
            ("Glucose Fasting", glucose, "3.6 - 6.0", "mmol/L", ""),
            ("Hemoglobin A1C/Total Hemoglobin", hba1c, "<6.0", "%", ""),
            ("Sodium", sodium, "135-145", "mmol/L", ""),
            ("Potassium", potassium, "3.5-5.2", "mmol/L", ""),
            ("Creatinine", creatinine, "67-117", "umol/L", ""),
            ("Glomerular Filtration Rate (eGFR)", egfr, ">=60", "mL/min/1.73m2", ""),
            ("Alkaline Phosphatase", alp, "40-129", "U/L", ""),
            ("Gamma Glutamyl Transferase", ggt, "<65", "U/L", ggt_flag),
            ("Alanine Aminotransferase", alt, "<50", "U/L", alt_flag),
            ("Aspartate Aminotransferase", ast, "<35", "U/L", ast_flag),
        ],
        "muscle": [
            ("Creatine Kinase", ck, "44-275", "U/L", ""),
        ],
        "lipids": [
            ("Triglyceride", trig, "<1.70", "mmol/L", ""),
            ("Cholesterol", chol, "<5.20", "mmol/L", ""),
            ("HDL Cholesterol", hdl, ">=1.00", "mmol/L", hdl_flag),
            ("LDL Cholesterol", ldl, "<3.50", "mmol/L", ""),
        ],
        "thyroid": [
            ("Thyroid Stimulating Hormone", tsh, "0.32-4.00", "mIU/L", ""),
        ],
        "adrenal": [
            ("Cortisol AM", cortisol, "140-535", "nmol/L", ""),
        ],
        "reproductive": [
            ("Testosterone", testosterone, "8.4 - 28.8", "nmol/L", ""),
            ("Testosterone Free", testosterone_free, "196-636", "pmol/L", free_t_flag),
        ],
        "bone": [
            ("25-Hydroxy Vitamin D", vitamin_d, "75.0 - 250.0", "nmol/L", vitamin_d_flag),
        ],
        "serum_proteins": [
            ("C Reactive Protein", crp, "<5.0", "mg/L", ""),
        ],
    }
    return results


def main():
    random.seed(42)  # Reproducible results

    for i, date_str in enumerate(REPORT_DATES):
        filename = f"demo_report_{i + 2}.pdf"
        results = build_results(i)
        generate_report(filename, PATIENT, date_str, results)

    print(f"\nGenerated 5 demo reports (demo_report_2.pdf through demo_report_6.pdf)")


if __name__ == "__main__":
    main()
