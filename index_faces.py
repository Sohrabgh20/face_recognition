import os
import numpy as np
import face_recognition
from elasticsearch import Elasticsearch

# تنظیمات دیتاست
dataset_folder = "/root/dataset_faces"  

# تنظیمات Elasticsearch
ES_HOST = "http://localhost:9200"
es = Elasticsearch([{"host": "localhost", "port": 9200, "scheme": "http"}])
index_name = "faces"

# بررسی وجود ایندکس
if es.indices.exists(index=index_name):
    print("✅ ایندکس 'faces' قبلاً وجود دارد. نیازی به ایندکس مجدد نیست.")
    exit()

# ایجاد ایندکس جدید
es.indices.create(index=index_name, body={
    "mappings": {
        "properties": {
            "face_encoding": {"type": "dense_vector", "dims": 128, "index": True, "similarity": "cosine"},
            "image_path": {"type": "keyword"}
        }
    }
})
print(" ایندکس جدید 'faces' ایجاد شد.")

# تابع استخراج وکتور چهره‌ها
def get_face_encodings(image_path):
    try:
        image = face_recognition.load_image_file(image_path)
        face_locations = face_recognition.face_locations(image)
        encodings = face_recognition.face_encodings(image, face_locations)
        return encodings
    except Exception as e:
        print(f" خطا در پردازش {image_path}: {e}")
        return []

# ایندکس کردن تصاویر دیتاست
print(" در حال ایندکس کردن تصاویر...")
valid_extensions = ('.jpg', '.jpeg', '.png')

for root_dir, _, files in os.walk(dataset_folder):
    for file_name in files:
        if file_name.lower().endswith(valid_extensions):
            img_path = os.path.join(root_dir, file_name)
            encodings = get_face_encodings(img_path)
            for encoding in encodings:
                doc = {"face_encoding": encoding.tolist(), "image_path": img_path}
                es.index(index=index_name, body=doc)

print("ایندکس کردن تصاویر به پایان رسید.")