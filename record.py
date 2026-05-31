import cv2
import os
import glob

# ==============================
# SETTINGS
# ==============================

# إدخال اسم الكلمة
label = input("Enter word label: ")

# عدد الفريمات المطلوب تسجيلها
total_frames = 30

# FPS للحفظ
fps = 20

# ==============================
# CREATE SAVE FOLDER
# ==============================

save_path = f"dataset/{label}"
os.makedirs(save_path, exist_ok=True)

# ==============================
# CONTINUE NUMBERING
# ==============================

existing_files = glob.glob(f"{save_path}/{label}_*.mp4")
existing_numbers = []

for file in existing_files:
    try:
        num = int(file.split("_")[-1].split(".")[0])
        existing_numbers.append(num)
    except:
        pass

count = max(existing_numbers) + 1 if existing_numbers else 0

print(f"Starting from sample number: {count}")

# ==============================
# CAMERA
# ==============================

cap = cv2.VideoCapture(0)

fourcc = cv2.VideoWriter_fourcc(*'mp4v')

print("Press 's' to start recording")
print("Press 'q' to quit")

# ==============================
# MAIN LOOP
# ==============================

while True:

    ret, frame = cap.read()

    if not ret:
        break

    # عرض معلومات
    cv2.putText(
        frame,
        f"Word: {label} | Sample: {count}",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2
    )

    cv2.imshow("Camera", frame)

    key = cv2.waitKey(1) & 0xFF

    # ==========================
    # START RECORDING
    # ==========================

    if key == ord('s'):

        print(f"Recording sample {count}...")

        filename = f"{save_path}/{label}_{count}.mp4"

        height, width, _ = frame.shape

        out = cv2.VideoWriter(
            filename,
            fourcc,
            fps,
            (width, height)
        )

        # تسجيل عدد ثابت من الفريمات
        for frame_num in range(total_frames):

            ret, frame = cap.read()

            if not ret:
                break

            out.write(frame)

            # عرض حالة التسجيل
            cv2.putText(
                frame,
                f"Recording {frame_num+1}/{total_frames}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2
            )

            cv2.imshow("Camera", frame)

            # للخروج أثناء التسجيل
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        out.release()

        print(f"Saved: {filename}")

        count += 1

    # ==========================
    # EXIT
    # ==========================

    elif key == ord('q'):
        print("Exiting...")
        break

# ==============================
# CLEANUP
# ==============================

cap.release()
cv2.destroyAllWindows()