import os
import base64
from flask import Flask, render_template, request, jsonify
import numpy as np
import cv2

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "dataset")
os.makedirs(DATASET_DIR, exist_ok=True)

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
if face_cascade.empty():
    raise RuntimeError("Failed to load haarcascade. Check your OpenCV installation.")

def read_image_from_file_storage(fs):
    data = fs.read()  # bytes
    nparr = np.frombuffer(data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img

def read_image_from_base64(data_url):
    
    if data_url.startswith("data:"):
        header, data = data_url.split(",", 1)
    else:
        data = data_url
    img_bytes = base64.b64decode(data)
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img

def encode_image_to_dataurl(img_bgr):
    _, buf = cv2.imencode(".jpg", img_bgr)
    b64 = base64.b64encode(buf).decode("utf-8")
    return "data:image/jpeg;base64," + b64

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/detect", methods=["POST"])
def detect():
    img = None
    username = None

    if "image" in request.files and request.files["image"].filename != "":
        img = read_image_from_file_storage(request.files["image"])
        username = request.form.get("username", None)
    else:

        data = None
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form
        b64 = data.get("imageBase64") if data else None
        username = data.get("username") if data else None
        if b64:
            img = read_image_from_base64(b64)

    if img is None:
        return jsonify({"status": "error", "message": "No image received"}), 400

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    annotated = img.copy()
    faces_dataurls = []
    saved = 0

    for i, (x, y, w, h) in enumerate(faces):
        cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 255, 0), 2)
        face_crop = img[y:y+h, x:x+w]

        
        if username:
            user_dir = os.path.join(DATASET_DIR, username)
            os.makedirs(user_dir, exist_ok=True)
            fname = f"{username}_{saved}.jpg"
            cv2.imwrite(os.path.join(user_dir, fname), face_crop)
            saved += 1

        faces_dataurls.append(encode_image_to_dataurl(face_crop))

    annotated_url = encode_image_to_dataurl(annotated)
    return jsonify({
        "status": "ok",
        "annotated": annotated_url,
        "faces": faces_dataurls,
        "count": len(faces),
        "saved": saved
    })

if __name__ == "__main__":
    app.run(debug=True)
