import os
import sys
import numpy as np
import spectral.io.envi as envi
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import matplotlib.patches as mpatches
import joblib
import json
from sklearn.metrics import accuracy_score, classification_report, cohen_kappa_score

# ==========================================
# 1. إعداد المسارات (Paths) & Input
# ==========================================
if len(sys.argv) != 3:
    print("Usage: python predict.py <hdr_file> <dat_file>")
    sys.exit(1)

hdr_path = sys.argv[1]
dat_path = sys.argv[2]

current_dir = os.path.dirname(os.path.abspath(__file__))

model_path = os.path.join(current_dir, 'model.pkl')
scaler_path = os.path.join(current_dir, 'scaler.pkl')

print("\n--- HYSPERSPECTRAL CLASSIFICATION PIPELINE ---\n")

# ==========================================
# 2. تحميل "العقل والسكيلر" الجاهزين
# ==========================================
print("Loading pre-trained model and scaler...")
try:
    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
    print("Successfully loaded model and scaler!")
except Exception as e:
    print(f"Error loading files: {e}")
    sys.exit(1)

# ==========================================
# 3. تحميل مصفوفة صورة الإسماعيلية
# ==========================================
print("Reading Ismailia image data...")
img = envi.open(hdr_path, dat_path)
rows, cols, bands = img.nrows, img.ncols, img.nbands
data_3d = np.array(img.load(), dtype=np.float32)

print(f"Image shape: {rows} x {cols} x {bands}")

if hasattr(scaler, "n_features_in_") and bands != scaler.n_features_in_:
    raise ValueError(
        f"Band count mismatch: image has {bands} bands, scaler expects {scaler.n_features_in_}."
    )

X_ismailia = data_3d.reshape((rows * cols, bands))
no_data_mask = np.all(X_ismailia == 0, axis=1) | np.any(np.isnan(X_ismailia), axis=1)
X_ismailia = np.nan_to_num(X_ismailia, nan=0.0)

print(f"No-data pixels detected: {np.sum(no_data_mask)}\n")

# ==========================================
# 4. مرحلة التوقع (الفالديشن)
# ==========================================
print("Predicting land cover using the imported model...")

X_ismailia_scaled = scaler.transform(X_ismailia)
predictions = model.predict(X_ismailia_scaled)

predictions[no_data_mask] = 0
classified_map = predictions.reshape((rows, cols)).astype(np.uint8)

print("Prediction complete.\n")

# ==========================================
# 4.1 حساب دقة الفالديشن باستخدام ROIs
# ==========================================
print("--- VALIDATION ACCURACY (ROIs) ---")
roi_path = os.path.join(current_dir, 'Labeled_ROIs.csv')
class_name_to_id = {'water': 1, 'vegetation': 2, 'urban': 3, 'desert': 4}

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

roi_order, roi_counts, roi_points = parse_roi_file(roi_path)

y_true, y_pred = [], []
current_idx = 0
for roi_name, count in zip(roi_order, roi_counts):
    class_id = class_name_to_id.get(roi_name.strip().lower())
    for _ in range(count):
        if current_idx < len(roi_points):
            x, y = roi_points[current_idx]
            col, row = x - 1, y - 1
            if 0 <= row < rows and 0 <= col < cols:
                pred = classified_map[row, col]
                if pred != 0:
                    y_true.append(class_id)
                    y_pred.append(int(pred))
            current_idx += 1

overall_acc = 0.0
kappa_val = 0.0
clf_report_dict = {}

if len(y_true) == 0:
    print("No valid ROI points found after masking.")
else:
    overall_acc = accuracy_score(y_true, y_pred)
    kappa_val = cohen_kappa_score(y_true, y_pred)
    clf_report_dict = classification_report(y_true, y_pred, labels=[1, 2, 3, 4],
                                            target_names=["Water", "Vegetation", "Urban", "Desert"],
                                            zero_division=0, output_dict=True)
    print(f"Overall Accuracy: {overall_acc:.4f}")
    print(f"Kappa: {kappa_val:.4f}")
    print("Classification Report Calculated.")

# ==========================================
# 5. رسم الخريطة وحساب المساحات
# ==========================================
print("\nFinalizing results...")

colors = ['white', 'blue', 'green', 'red', 'yellow']
cmap = ListedColormap(colors)

plt.figure(figsize=(12, 10))
plt.imshow(classified_map, cmap=cmap, vmin=0, vmax=4)

# Title removed to keep the upper part of the image clean
# plt.title('Ismailia Validation Map (Using Nile Delta Model)', fontsize=14)

legend_patches = [
    mpatches.Patch(color='blue', label='Water'),
    mpatches.Patch(color='green', label='Vegetation'),
    mpatches.Patch(color='red', label='Urban'),
    mpatches.Patch(color='yellow', label='Desert')
]
plt.legend(handles=legend_patches, loc='lower right', fontsize=12, frameon=True)
plt.axis('off')

output_dir = os.path.join(os.path.dirname(current_dir), "output")
os.makedirs(output_dir, exist_ok=True)
base_name = os.path.splitext(os.path.basename(dat_path))[0]
output_path = os.path.join(output_dir, f"{base_name}.png")

plt.savefig(output_path, dpi=300, bbox_inches='tight')

pixel_area_km2 = (30 * 30) / 1_000_000
valid_pixels = np.sum(classified_map > 0)
class_names = {1: 'Water', 2: 'Vegetation', 3: 'Urban', 4: 'Desert'}

area_stats = {}

print("\n--- STATISTICS FOR ISMAILIA REGION ---")
if valid_pixels == 0:
    print("No valid pixels found.")
else:
    for cid, name in class_names.items():
        count = np.sum(classified_map == cid)
        area = float(count * pixel_area_km2)
        percentage = float((count / valid_pixels) * 100)
        area_stats[name] = {"area_km2": area, "percentage": percentage}
        print(f"{name}: {area:.2f} km² ({percentage:.2f}%)")

print(f"\nProcess Complete! Image saved as '{base_name}.png' in the output folder.")

# Build JSON report
final_report = {
    "metrics": {
        "overall_accuracy": float(overall_acc),
        "kappa": float(kappa_val),
        "classification_report": clf_report_dict
    },
    "area_stats": area_stats
}

print("###JSON_START###" + json.dumps(final_report) + "###JSON_END###")