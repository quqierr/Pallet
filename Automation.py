import streamlit as st
import pandas as pd
from collections import Counter

# === 1. Konfiguration & Custom Styling ===
st.set_page_config(page_title="Paletten-Assistent PRO", page_icon="📦", layout="wide")

# Custom CSS für professionelle Farben und Buttons
st.markdown("""
    <style>
    /* Hintergrund und Schrift */
    .stApp { background-color: #f8f9fa; }
    
    /* Buttons anpassen */
    div.stButton > button:first-child {
        border-radius: 5px;
        height: 3em;
        transition: all 0.3s;
    }
    
    /* Primärer Button (Hinzufügen / Speichern) */
    div[data-testid="stBaseButton-primary"] {
        background-color: #1a4a73 !important;
        border: none !important;
        color: white !important;
    }
    
    /* Roter Button (Leeren/Löschen) */
    div.stButton > button:contains("Leeren") {
        color: #d9534f !important;
        border: 1px solid #d9534f !important;
    }

    /* Karten-Look für Container */
    div[data-testid="stVerticalBlock"] > div[style*="border"] {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# === 2. Daten laden ===
EXCEL_PATH = "Expert Automation.xlsx"

@st.cache_data
def load_data(file_path):
    try:
        models = pd.read_excel(file_path, sheet_name="Models")
    except Exception:
        # Fallback für Testzwecke
        data = {
            "Product code": ["SKU-01", "SKU-02", "SKU-03"],
            "Category code": ["A", "B", "K6"],
            "Product name": ["Hochleistungsmotor A", "Steuergerät B", "Kabeltrommel K6"],
            "Product price": [450.00, 120.50, 45.00],
            "Sub-Categories": ["Motoren", "Elektronik", "Zubehör"]
        }
        models = pd.DataFrame(data)

    p_to_cat = dict(zip(models["Product code"], models["Category code"]))
    p_to_name = dict(zip(models["Product code"], models["Product name"]))
    p_to_price = dict(zip(models["Product code"], models["Product price"]))
    p_to_cat_fullname = dict(zip(models["Product code"], models["Sub-Categories"]))
    all_prods = list(p_to_cat.keys())
    return p_to_cat, p_to_name, p_to_price, p_to_cat_fullname, all_prods

product_to_category, product_to_name, product_to_price, product_to_cat_fullname, ALL_PRODUCTS = load_data(EXCEL_PATH)

# === 3. Regel-Logik ===
PALLET_RULES = [
    {"K1": 1}, {"K
