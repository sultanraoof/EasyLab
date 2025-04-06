import streamlit as st
import pytesseract
from PIL import Image
import cv2
import numpy as np
import re

normal_ranges = {
    "Hemoglobin": (13.5, 17.5),
    "WBC": (4000, 11000),
    "RBC": (4.5, 5.9),
    "Platelets": (150000, 450000),
    "Glucose": (70, 99),
    "Creatinine": (0.6, 1.2),
    "Urea": (10, 50),
    "Cholesterol": (125, 200),
    "Hematocrit": (38.3, 48.6),
    "MCH": (27.0, 33.0),
    "MCHC": (31.5, 35.5),
    "RDW": (11.5, 14.5),
    "Total Leucocyte Count": (4000, 11000),
    "Neutrophils": (40, 70),
    "Lymphocytes": (20, 40),
    "Monocytes": (2, 8),
    "Eosinophils": (1, 6),
    "Basophils": (0, 1)
}

test_aliases = {
    "haemoglobin": "Hemoglobin",
    "hemoglobin (hb)": "Hemoglobin",
    "hb": "Hemoglobin",
    "white blood cell": "WBC",
    "wbc": "WBC",
    "red blood cell": "RBC",
    "rbc": "RBC",
    "platelet": "Platelets",
    "platelets": "Platelets",
    "plt": "Platelets",
    "glucose": "Glucose",
    "fasting blood sugar": "Glucose",
    "fbs": "Glucose",
    "creatinine": "Creatinine",
    "urea": "Urea",
    "cholesterol": "Cholesterol",
    "hematocrit": "Hematocrit",
    "hct": "Hematocrit",
    "mean corpuscular hemoglobin": "MCH",
    "mean corpuscular haemoglobin": "MCH",
    "mch": "MCH",
    "mean corpuscular hemoglobin concentration": "MCHC",
    "mean corpuscular haemoglobin concentration": "MCHC",
    "mchc": "MCHC",
    "red cell distribution width": "RDW",
    "rdw": "RDW",
    "total leucocyte count": "Total Leucocyte Count",
    "neutrophils": "Neutrophils",
    "lymphocytes": "Lymphocytes",
    "monocytes": "Monocytes",
    "eosinophils": "Eosinophils",
    "basophils": "Basophils"
}

status_colors = {
    "Normal": "green",
    "Low": "orange",
    "High": "orange",
    "Unknown": "gray"
}

def extract_text_with_positions(image):
    gray = cv2.cvtColor(np.array(image), cv2.COLOR_BGR2GRAY)
    data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)
    lines = {}
    for i in range(len(data["text"])):
        word = data["text"][i].strip()
        if word == "" or not re.search(r"[a-zA-Z0-9]", word):
            continue
        y = data["top"][i]
        line_id = y // 10
        lines.setdefault(line_id, []).append(word)
    merged_lines = [" ".join(words) for key, words in sorted(lines.items())]
    return merged_lines

def parse_lab_results(lines):
    results = []
    for line in lines:
        lower_line = line.lower()
        for alias, standard in test_aliases.items():
            if alias in lower_line:
                numbers = re.findall(r"\d+\.\d+|\d+", line)
                if numbers:
                    try:
                        value = float(numbers[0].replace(",", ""))
                        results.append({"test": standard, "value": value})
                        break
                    except:
                        pass
    return results

def analyze_results(results):
    for result in results:
        test = result["test"]
        value = result["value"]
        if test in normal_ranges:
            low, high = normal_ranges[test]
            if value < low:
                result["status"] = "Low"
            elif value > high:
                result["status"] = "High"
            else:
                result["status"] = "Normal"
        else:
            result["status"] = "Unknown"
    return results

def show_test_results(results):
    st.subheader("Lab Test Results")
    for res in results:
        test = res["test"]
        value = res["value"]
        status = res["status"]
        color = status_colors.get(status, "gray")
        st.markdown(f"""
        <div style='
            border-left: 5px solid {color}; 
            padding: 0.5rem 1rem; 
            margin-bottom: 1rem; 
            background-color: #f9f9f9;
            border-radius: 6px;'>
            <strong>{test}</strong><br>
            Value: {value}  
            <span style='color:{color}; font-weight: bold;'>({status})</span>
        </div>
        """, unsafe_allow_html=True)

st.title("Easylab - Lab Report Analyzer")
st.write("Upload a photo or scan of your blood test report.")

uploaded_file = st.file_uploader("Choose an image file (JPG, PNG)", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Report", use_column_width=True)

    with st.spinner("Extracting data..."):
        lines = extract_text_with_positions(image)
        results = parse_lab_results(lines)
        analyzed = analyze_results(results)

    if analyzed:
        show_test_results(analyzed)
    else:
        st.warning("No recognizable lab results found in the image.")
