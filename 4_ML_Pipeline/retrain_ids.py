import pandas as pd
import numpy as np
import os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import RobustScaler
from xgboost import XGBClassifier
from sklearn.metrics import classification_report, confusion_matrix

# ==========================================
# STEP 1: LOAD, FILTER, AND SAMPLE DATA
# ==========================================
print("[Step 1] Loading and cleaning dataset...")

# Define the exact 15 features your ESP32 sniffer extracts
FEATURES_LIST = [
    'flow_duration', 'Header_Length_var', 'Protocol_Type', 'Rate', 'Tot_size',
    'IAT', 'Max', 'AVG', 'Num', 'Variance',
    'ack_flag_number', 'rst_count', 'syn_flag_number', 'fin_flag_number', 'urg_flag_number'
]
LABEL_COL = 'label'  # Adjust based on your CSV file structure

# Load dataset (Replace with your actual CIC-IoT 2023 partition CSV file path)
csv_path = "CIC_IoT_2023_Sample.csv" 
df = pd.read_csv(csv_path)

# Map all multi-class attacks into a strict binary format: 0 for Benign, 1 for Attack
df['binary_label'] = df[LABEL_COL].apply(lambda x: 0 if str(x).strip().lower() == 'benign' else 1)

# Down-sample attack classes to balance with Benign class and avoid bias
benign_samples = df[df['binary_label'] == 0]
attack_samples = df[df['binary_label'] == 1]

print(f"Original counts - Benign: {len(benign_samples)}, Attacks: {len(attack_samples)}")

# Balance out the data down to a 1:2 or 1:1 ratio depending on your sample size
if len(attack_samples) > len(benign_samples) * 2:
    attack_samples = attack_samples.sample(n=len(benign_samples) * 2, random_state=42)

balanced_df = pd.concat([benign_samples, attack_samples]).sample(frac=1, random_state=42)
X = balanced_df[FEATURES_LIST]
y = balanced_df['binary_label']

# ==========================================
# STEP 2: STRATIFIED SPLIT
# ==========================================
print("[Step 2] Splitting data into Train and Test sets...")
# Stratified split ensures an even distribution of Benign vs Attack rows in both split zones
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, stratify=y, random_state=42)

# ==========================================
# STEP 3: ROBUST SCALING
# ==========================================
print("[Step 3] Fitting RobustScaler...")
# Fits the median and Interquartile Range (IQR) to withstand high rate flooding outliers
scaler = RobustScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# ==========================================
# STEP 4: MODEL TRAINING (OPTIMIZED FOR ESP32)
# ==========================================
print("[Step 4] Training optimized XGBoost Binary Classifier...")
# Strict pruning parameters to fit into the ESP32 DevKit memory boundaries
model = XGBClassifier(
    n_estimators=40,       # Max 40 trees to maintain small binary size
    max_depth=3,           # Shallow trees limit memory footprint
    learning_rate=0.1,
    verbosity=1,
    random_state=42
)
model.fit(X_train_scaled, y_train)

# Evaluation
y_pred = model.predict(X_test_scaled)
print("\n=== PERFORMANCE REPORT ===")
print(classification_report(y_test, y_pred))

# ==========================================
# STEP 5: EXPORT C++ HARDWARE HEADERS
# ==========================================
print("\n[Step 5] Exporting C++ array files for ESP32 layout...")

# 5A: Export scaler parameters
with open("scaler.h", "w") as f:
    f.write("// Microcontroller RobustScaler Arrays\n\n")
    f.write(f"const float scaler_center[15] = {{ {', '.join([str(x) for x in scaler.center_])} }};\n")
    f.write(f"const float scaler_scale[15] = {{ {', '.join([str(x) for x in scaler.scale_])} }};\n")
print("--> Saved 'scaler.h' successfully.")

# 5B: Convert model rules using native arrays (via EloquentTinyML array formatting)
# If using EloquentTinyML, use its provided converter module or direct text array export:
try:
    from m2cgen import export_to_c
    c_code = export_to_c(model)
    with open("model_binary.h", "w") as f:
        f.write("// Auto-generated hardware calculation logic layout\n\n")
        f.write(c_code)
    print("--> Saved 'model_binary.h' successfully via structural array lines.")
except ImportError:
    print("m2cgen not found. Please run 'pip install m2cgen' to compile the math trees into C++ rules.")