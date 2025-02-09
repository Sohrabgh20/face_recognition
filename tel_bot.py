import os
import face_recognition
from elasticsearch import Elasticsearch
from telegram import Update, InputMediaPhoto
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext

# تنظیمات Elasticsearch
ES_HOST = "http://localhost:9200"
es = Elasticsearch([{"host": "localhost", "port": 9200, "scheme": "http"}])
index_name = "faces"

# تنظیمات ربات تلگرام
TELEGRAM_BOT_TOKEN = "7311454323:AAEsb3DSEgFB4QzZY6Bi_Nr1CXRGtkBA64I"
updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)
dispatcher = updater.dispatcher

# تابع استخراج وکتور چهره‌ها
def get_face_encodings(image_path):
    try:
        image = face_recognition.load_image_file(image_path)
        face_locations = face_recognition.face_locations(image)
        encodings = face_recognition.face_encodings(image, face_locations)
        return encodings
    except Exception as e:
        print(f"❌ خطا در پردازش {image_path}: {e}")
        return []

# جستجوی چهره‌های مشابه
def search_similar_faces(image_path, top_n=5):
    encodings = get_face_encodings(image_path)
    if not encodings:
        print("❌ هیچ چهره‌ای در تصویر ورودی یافت نشد.")
        return []

    query_vector = encodings[0].tolist()
    query = {
        "size": top_n,
        "query": {
            "script_score": {
                "query": {"match_all": {}},
                "script": {
                    "source": "cosineSimilarity(params.query_vector, 'face_encoding') + 1.0",
                    "params": {"query_vector": query_vector}
                }
            }
        }
    }

    res = es.search(index=index_name, body=query)
    hits = res.get("hits", {}).get("hits", [])
    return [(hit["_source"]["image_path"], hit["_score"]) for hit in hits]

# دریافت عکس از کاربر و ارسال نتایج
def handle_photo(update: Update, context: CallbackContext):
    file = update.message.photo[-1].get_file()
    received_img_path = "received_image.jpg"
    file.download(received_img_path)
    print(f" تصویر دریافتی ذخیره شد: {received_img_path}")

    similar_faces = search_similar_faces(received_img_path, top_n=5)

    if similar_faces:
        media_group = []
        response_text = "🔍 تصاویر مشابه یافت شده:\n"
        for path, score in similar_faces:
            response_text += f"{path} (score: {score:.3f})\n"
            if os.path.exists(path):  # بررسی وجود فایل قبل از ارسال
                media_group.append(InputMediaPhoto(open(path, "rb"), caption=f"Score: {score:.3f}"))

        update.message.reply_text(response_text)

        if media_group:
            update.message.reply_media_group(media_group)
    else:
        update.message.reply_text("❌ چهره‌ای مشابه یافت نشد.")

dispatcher.add_handler(MessageHandler(Filters.photo, handle_photo))

def main():
    print(" ربات تلگرام در حال اجراست...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()