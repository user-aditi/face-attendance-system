import os
import cv2
import face_recognition
import pickle
import shutil

def generate_encodings(images_folder='Images', failed_folder='FailedImages'):
    os.makedirs(failed_folder, exist_ok=True)
    student_ids, encode_list = [], []
    
    print("Encoding started...")
    image_files = [f for f in os.listdir(images_folder) if f.endswith(('.png', '.jpg', '.jpeg'))]
    
    if not image_files:
        print("No images found to encode.")
        return False

    for i, filename in enumerate(image_files):
        student_id = os.path.splitext(filename)[0]
        path = os.path.join(images_folder, filename)
        print(f"--> Processing {i+1}/{len(image_files)}: {filename}")
        
        img = cv2.imread(path)
        if img is None: continue
        
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encodes = face_recognition.face_encodings(img_rgb)
        
        if encodes:
            encode_list.append(encodes[0])
            student_ids.append(student_id)
        else:
            print(f"  [FAILED] No face in {filename}. Moving to '{failed_folder}'.")
            shutil.move(path, os.path.join(failed_folder, filename))

    if not encode_list:
        print("No faces could be encoded.")
        return False

    with open('EncodeFile.p', 'wb') as file:
        pickle.dump([encode_list, student_ids], file)
    
    print("\nEncoding complete. 'EncodeFile.p' saved.")
    return True