@'
import os
from PIL import Image
import imagehash

DATASET_DIR = r"D:\AI TVH\dataset"

DELETED_IMAGES = [
    ("cay_phuong", "Hình ảnh hoa phượng đẹp nhất.jpg"),
    ("cay_phuong", "tải xuống (25).jpg"),
    ("hoa_hong", "tải xuống (22).jpg"),
    ("lan_mokara", "images.jpg"),
    ("muong_trau", "uong_la_muong_trau_co_tac_dung_gi_mot_so_bai_thuoc_tu_la_muong_trau1_5e19d7cacd.jpg"),
    ("vong_mong_ga", "Erythrina_crista-galli_01.jpg"),
    ("vong_mong_ga", "vong-mong-ga-ciebo-argentina-367425.jpg"),
]

def calculate_hash(path):
    try:
        with Image.open(path) as image:
            image = image.convert("RGB")
            return imagehash.phash(image)
    except Exception:
        return None

print()
print("=" * 70)
print("KIEM TRA ANH DA XOA TRONG DATASET")
print("=" * 70)

total_matches = 0

for species, filename in DELETED_IMAGES:

    print()
    print(f"Loai: {species}")
    print(f"Anh da xoa: {filename}")

    possible_files = []

    for root, _, files in os.walk(DATASET_DIR):
        for file in files:
            if file == filename:
                possible_files.append(
                    os.path.join(root, file)
                )

    if not possible_files:
        print("   Khong tim thay file cung ten.")
        continue

    first_hash = None

    for dataset_file in possible_files:

        dataset_hash = calculate_hash(dataset_file)

        if dataset_hash is None:
            continue

        if first_hash is None:
            first_hash = dataset_hash
            print(f"   Tim thay: {dataset_file}")
            total_matches += 1

        else:
            distance = dataset_hash - first_hash

            if distance == 0:
                print(f"   Trung hash: {dataset_file}")
                total_matches += 1

print()
print("=" * 70)
print(f"Tong so file dataset duoc phat hien: {total_matches}")
print("=" * 70)
print()
print("Chi kiem tra, khong xoa file.")
'@ | Set-Content -Encoding UTF8 "D:\AI TVH\check_deleted_duplicates.py"