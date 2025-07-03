
import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
from fpdf import FPDF
from datetime import datetime

st.set_page_config(page_title="DRP Compliance Tool", layout="wide")
st.title("🛠️ DRP Compliance Estimate & Photo Scrubbing Tool")

# Select insurer
insurer = st.selectbox("Select DRP Program", ["State Farm", "Allstate", "GEICO", "Progressive"])

# Define rule sets
rules = {
    "State Farm": {
        "required_keywords": ["alignment", "calibration", "OEM"],
        "forbidden_keywords": ["aftermarket"]
    },
    "Allstate": {
        "required_keywords": ["alignment", "pre-scan"],
        "forbidden_keywords": []
    },
    "GEICO": {
        "required_keywords": ["VIN", "calibration"],
        "forbidden_keywords": ["aftermarket"]
    },
    "Progressive": {
        "required_keywords": ["alignment"],
        "forbidden_keywords": []
    }
}

findings = []

# Upload Estimate
estimate = st.file_uploader("📄 Upload Estimate (PDF)", type=["pdf"])
if estimate:
    pdf_doc = fitz.open(stream=estimate.read(), filetype="pdf")
    text = ""
    for page in pdf_doc:
        text += page.get_text()

    st.subheader("📋 Extracted Estimate Text")
    st.text_area("Estimate Content", text, height=300)

    for word in rules[insurer]["required_keywords"]:
        if word.lower() not in text.lower():
            findings.append((f"Missing required keyword: {word}", f"{insurer} DRP requires this."))
    for word in rules[insurer]["forbidden_keywords"]:
        if word.lower() in text.lower():
            findings.append((f"Forbidden keyword detected: {word}", f"{insurer} DRP does not allow this."))

# Upload Photos
photos = st.file_uploader("📷 Upload Damage Photos", accept_multiple_files=True, type=["jpg", "jpeg", "png"])
if photos:
    st.subheader("📸 Uploaded Photos Review")
    for photo in photos:
        img = Image.open(photo)
        st.image(img, caption=photo.name, use_column_width=True)
        if img.width < 800 or img.height < 600:
            findings.append((f"Photo '{photo.name}' is too low resolution", "Minimum 800x600 required."))

# Generate PDF Report
if findings and st.button("📄 Generate PDF Compliance Report"):
    class PDFReport(FPDF):
        def header(self):
            self.set_font("Arial", "B", 14)
            self.cell(0, 10, "DRP Compliance Report", ln=True, align="C")
            self.set_font("Arial", "", 11)
            self.cell(0, 10, f"Date: {datetime.today().strftime('%Y-%m-%d')}", ln=True, align="R")
            self.ln(5)

        def footer(self):
            self.set_y(-15)
            self.set_font("Arial", "I", 8)
            self.cell(0, 10, f"Page {self.page_no()}", align="C")

        def add_findings(self, findings):
            self.set_font("Arial", "", 11)
            self.cell(0, 10, f"Findings for {insurer} DRP Program:", ln=True)
            for i, (issue, detail) in enumerate(findings, start=1):
                self.multi_cell(0, 10, f"{i}. {issue}\n   -> {detail}")
                self.ln(1)

    pdf = PDFReport()
    pdf.add_page()
    pdf.add_findings(findings)
    pdf_path = "/mnt/data/DRP_Report_Generated.pdf"
    pdf.output(pdf_path)
    st.success("PDF report generated.")
    with open(pdf_path, "rb") as file:
        st.download_button("📥 Download Report", file.read(), file_name="DRP_Compliance_Report.pdf")

if not findings and st.button("📄 Generate PDF Compliance Report"):
    st.info("No issues found. Nothing to include in report.")

st.info("This tool adapts to insurer rules and generates a compliance summary PDF.")
