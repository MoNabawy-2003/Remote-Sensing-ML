import os
import numpy as np
import spectral.io.envi as envi
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib

# ==========================================
# 1. Paths & Config
# ==========================================
current_dir = os.path.dirname(os.path.abspath(__file__))

hdr_path = os.path.join(current_dir, 'Final.hdr')
dat_path = os.path.join(current_dir, 'Final')
roi_path = os.path.join(current_dir, 'Labeled_ROIs.csv')

class_name_to_id = {'water': 1, 'vegetation': 2, 'urban': 3, 'desert': 4}

# ==========================================
# 2. ROI Parsing Logic (Updated)
# ==========================================
def parse_roi_file(path):
    roi_order, roi_counts, data_points = [], [], []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            stripped = line.strip()
            if not stripped: continue
            if stripped.startswith(';'):
                if 'ROI name:' in stripped:
                    roi_order.append(stripped.split(':', 1)[1].strip())
                elif 'ROI npts:' in stripped:
                    roi_counts.append(int(stripped.split(':', 1)[1].strip()))
                continue
            parts = [p.strip() for p in stripped.split(',')]
            if len(parts) >= 2:
                try:
                    data_points.append((int(parts[0]), int(parts[1])))
                except ValueError: continue
    return roi_order, roi_counts, data_points

# ==========================================
# 3. Load Data & Extract Features
# ==========================================
print("Loading image and ROIs for training...")
img = envi.open(hdr_path, dat_path)
rows, cols, bands = img.nrows, img.ncols, img.nbands
data_3d = np.array(img.load(), dtype=np.float32)

roi_order, roi_counts, roi_points = parse_roi_file(roi_path)

X, y = [], []
current_pt_idx = 0
for roi_name, count in zip(roi_order, roi_counts):
    class_id = class_name_to_id.get(roi_name.strip().lower())
    if class_id is None: continue
    for _ in range(count):
        if current_pt_idx < len(roi_points):
            x_coord, y_coord = roi_points[current_pt_idx]
            c, r = x_coord - 1, y_coord - 1 # 1-based to 0-based
            if 0 <= r < rows and 0 <= c < cols:
                pixel_data = data_3d[r, c, :]
                if not np.any(np.isnan(pixel_data)):
                    X.append(pixel_data)
                    y.append(class_id)
            current_pt_idx += 1

X, y = np.array(X), np.array(y)

# ==========================================
# 4. Training & Saving
# ==========================================
print(f"Training on {len(X)} samples...")
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)

model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
model.fit(X_train_scaled, y_train)

joblib.dump(model, os.path.join(current_dir, 'model.pkl'))
joblib.dump(scaler, os.path.join(current_dir, 'scaler.pkl'))
print("Training complete! model.pkl and scaler.pkl saved.")