import os
import numpy as np
import spectral.io.envi as envi
import joblib
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import matplotlib.patches as mpatches
from sklearn.metrics import accuracy_score, classification_report

# ==========================================
# 1. إعداد المسارات (Paths)
# ==========================================
current_dir = os.path.dirname(os.path.abspath(__file__))

# أسماء ملفات صاحبك زي ما هي في الفولدر عندك
model_path = os.path.join(current_dir, 'model.pkl')
scaler_path = os.path.join(current_dir, 'scaler.pkl')

# أسماء ملفات صورة الإسماعيلية بتاعتك
hdr_path = os.path.join(current_dir, 'Final.hdr')
dat_path = os.path.join(current_dir, 'Final')

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
    exit()

# ==========================================
# 3. تحميل مصفوفة صورة الإسماعيلية
# ==========================================
print("Reading Ismailia image data (10 bands)...")
img = envi.open(hdr_path, dat_path)
rows, cols, bands = img.nrows, img.ncols, img.nbands
data_3d = np.array(img.load(), dtype=np.float32)

# التأكد إن عدد الباندات مناسب للموديل/السكيلر
if hasattr(scaler, "n_features_in_") and bands != scaler.n_features_in_:
    raise ValueError(
        f"Band count mismatch: image has {bands} bands, scaler expects {scaler.n_features_in_}."
    )

# تحويل الصورة لشكل مصفوفة طولية عشان الموديل يفهمها
X_ismailia = data_3d.reshape((rows * cols, bands))
# تحديد المناطق اللي مفيهاش داتا (قيم صفرية بالكامل أو فيها NaN)
no_data_mask = np.all(X_ismailia == 0, axis=1) | np.any(np.isnan(X_ismailia), axis=1)

# تنظيف قيم NaN قبل السكيلر
X_ismailia = np.nan_to_num(X_ismailia, nan=0.0)

# ==========================================
# 4. مرحلة التوقع (الفالديشن)
# ==========================================
print("Predicting land cover using the imported model...")

# وزن البيانات بنفس "ميزان" صاحبك
X_ismailia_scaled = scaler.transform(X_ismailia)

# الموديل بيطلع توقعاته لكل بيكسل
predictions = model.predict(X_ismailia_scaled)

# تصفير المناطق اللي مفيهاش داتا
predictions[no_data_mask] = 0
classified_map = predictions.reshape((rows, cols))

# ==========================================
# 4.1 حساب دقة الفالديشن باستخدام ROIs
# ==========================================
roi_path = os.path.join(current_dir, 'Labeled_ROIs.csv')
class_name_to_id = {'water': 1, 'vegetation': 2, 'urban': 3, 'desert': 4}

def parse_roi_file(path):
    roi_order = []
    roi_counts = []
    data_points = []

    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith(';'):
                if 'ROI name:' in stripped:
                    roi_order.append(stripped.split(':', 1)[1].strip())
                elif 'ROI npts:' in stripped:
                    roi_counts.append(int(stripped.split(':', 1)[1].strip()))
                continue

            parts = [p.strip() for p in stripped.split(',')]
            if len(parts) < 2:
                continue
            try:
                x = int(parts[0])
                y = int(parts[1])
            except ValueError:
                continue
            data_points.append((x, y))

    if len(roi_order) != len(roi_counts):
        raise ValueError("ROI header parsing failed. Check Labeled_ROIs.csv format.")

    return roi_order, roi_counts, data_points

roi_order, roi_counts, roi_points = parse_roi_file(roi_path)

roi_labels = []
start_idx = 0
for roi_name, count in zip(roi_order, roi_counts):
    class_id = class_name_to_id.get(roi_name.strip().lower())
    if class_id is None:
        raise ValueError(f"Unknown ROI name '{roi_name}' in Labeled_ROIs.csv")
    roi_labels.extend([class_id] * count)
    start_idx += count

if len(roi_points) < len(roi_labels):
    raise ValueError("ROI points fewer than expected based on ROI counts.")

y_true = []
y_pred = []

for (x, y), label in zip(roi_points, roi_labels):
    # تحويل 1-based إلى 0-based
    col = x - 1
    row = y - 1
    if row < 0 or col < 0 or row >= rows or col >= cols:
        continue
    pred = classified_map[row, col]
    if pred == 0:
        continue
    y_true.append(label)
    y_pred.append(int(pred))

print("\n--- VALIDATION ACCURACY (ROIs) ---")
if len(y_true) == 0:
    print("No valid ROI points found after masking. Check ROI file and no-data handling.")
else:
    overall_acc = accuracy_score(y_true, y_pred)
    print(f"Overall Accuracy: {overall_acc:.4f}")
    print("Classification Report:")
    print(
        classification_report(
            y_true,
            y_pred,
            labels=[1, 2, 3, 4],
            target_names=["Water", "Vegetation", "Urban", "Desert"],
            zero_division=0,
        )
    )

# ==========================================
# 5. رسم الخريطة وحساب المساحات
# ==========================================
print("Finalizing results...")

# الألوان: 0=أبيض، 1=أزرق (مية)، 2=أخضر (زرع)، 3=أحمر (مباني)، 4=أصفر (صحراء)
colors = ['white', 'blue', 'green', 'red', 'yellow']
cmap = ListedColormap(colors)

plt.figure(figsize=(12, 10))
plt.imshow(classified_map, cmap=cmap, vmin=0, vmax=4)
plt.title('Ismailia Validation Map (Using Nile Delta Model)', fontsize=14)

legend_patches = [
    mpatches.Patch(color='blue', label='Water'),
    mpatches.Patch(color='green', label='Vegetation'),
    mpatches.Patch(color='red', label='Urban'),
    mpatches.Patch(color='yellow', label='Desert')
]
plt.legend(handles=legend_patches, loc='lower right')
plt.axis('off')

# حفظ الخريطة كصورة
plt.savefig(os.path.join(current_dir, 'Ismailia_Validation_Result.png'), dpi=300)

# حساب إحصائيات المساحة (Step 8 في المشروع)
pixel_area_km2 = (30 * 30) / 1_000_000 # بيكسل لاندسات 30 متر
valid_pixels = np.sum(classified_map > 0)
class_names = {1: 'Water', 2: 'Vegetation', 3: 'Urban', 4: 'Desert'}

print("\n--- STATISTICS FOR ISMAILIA REGION ---")
if valid_pixels == 0:
    print("No valid pixels found. Check no-data mask or input image values.")
else:
    for cid, name in class_names.items():
        count = np.sum(classified_map == cid)
        area = count * pixel_area_km2
        percentage = (count / valid_pixels) * 100
        print(f"{name}: {area:.2f} km² ({percentage:.2f}%)")

print("\nProcess Complete! Image saved as 'Ismailia_Validation_Result.png'.")