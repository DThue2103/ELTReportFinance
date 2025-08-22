import os
from pdf2image import convert_from_path
import cv2
import pytesseract
from PIL import Image
import numpy as np
from ultralytics import YOLO
from pytesseract import Output
import pdfplumber
from unidecode import unidecode

# Load YOLO model
model = YOLO(r"/home/huedt/Documents/PythonProjects/ELTReportFinance/transformation/train/weights/last.pt")


# ======== PDF UTIL ========
def count_pdf_pages(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        return len(pdf.pages)


# ======== IMAGE PREPROCESSING ========
def detect_text_direction(image):
    pil_image = Image.fromarray(image)
    d = pytesseract.image_to_osd(pil_image, output_type=Output.DICT)
    return d['rotate']


def adjust_image_orientation(image):
    rotation = detect_text_direction(image)
    if rotation == 90:
        image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
    elif rotation == 180:
        image = cv2.rotate(image, cv2.ROTATE_180)
    elif rotation == 270:
        image = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
    return image


def process_and_rotate_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Tăng độ tương phản + adaptive threshold
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                   cv2.THRESH_BINARY_INV, 15, 10)

    # Morphology để nối đường kẻ bảng
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)

    # Deskew bằng Hough transform
    edges = cv2.Canny(morph, 50, 150)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 100, minLineLength=100, maxLineGap=10)

    angles = [np.degrees(np.arctan2(y2 - y1, x2 - x1))
              for line in lines for x1, y1, x2, y2 in line] if lines is not None else []
    median_angle = np.median(angles) if angles else 0

    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h),
                             flags=cv2.INTER_CUBIC,
                             borderMode=cv2.BORDER_REPLICATE)

    return rotated


# ======== YOLO DETECTION ========
def detect_table(image, conf_threshold=0.5):
    results = model.predict(source=image, verbose=False)
    table_regions, table_coordinates = [], []
    table_count, column_count, table_name_count = 0, 0, 0

    for result in results:
        boxes = result.boxes
        for box in boxes:
            class_id = int(box.cls[0].item())
            conf = box.conf[0].item()

            if conf < conf_threshold:
                continue

            if class_id == 1:  # table
                table_count += 1
            elif class_id == 0:  # column_name
                column_count += 1
            elif class_id == 2:  # table_name
                table_name_count += 1

            if class_id == 1:  # lưu box bảng
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                table_regions.append(image[y1:y2, x1:x2])
                table_coordinates.append((x1, y1, x2, y2))

    # Rule-based filter
    if column_count >= 2 and table_count >= 1:
        # Merge nếu có 2 bảng gần nhau
        if len(table_coordinates) == 2:
            x1_1, y1_1, x2_1, y2_1 = table_coordinates[0]
            x1_2, y1_2, x2_2, y2_2 = table_coordinates[1]
            distance = abs(y1_2 - y2_1) if y1_2 > y1_1 else abs(y1_1 - y2_2)

            if distance < image.shape[0] / 6:
                x1, y1, x2, y2 = min(x1_1, x1_2), min(y1_1, y1_2), max(x2_1, x2_2), max(y2_1, y2_2)
                return image, image[y1:y2, x1:x2], (x1, y1, x2, y2), table_name_count

        # Nếu chỉ có 1 bảng
        elif len(table_coordinates) == 1:
            return image, table_regions[0], table_coordinates[0], table_name_count

    return None, None, None, None


# ======== CHECK AREA ========
def check_area(image, coords):
    img_w, img_h = image.size
    x1, y1, x2, y2 = coords
    table_w, table_h = x2 - x1, y2 - y1
    table_area = table_w * table_h
    percentage_area = (table_area / (img_w * img_h)) * 100
    percentage_height = (table_h / img_h) * 100

    if percentage_area > 5 and percentage_height > 15 and y1 < img_h / 4:
        return True
    return False

def remove_vietnamese_accent(text):
    return unidecode(text)

def check_report_image(image):
    # Crop the image to only keep the top 1/4 part
    height, width = image.shape[:2]
    cropped_image = image[0:int(height / 4), 0:width]  # Keep only the first quarter of the image

    # Kiểm tra và chuyển đổi ảnh thành định dạng phù hợp cho pytesseract
    if isinstance(cropped_image, np.ndarray):
        # Nếu image là numpy array, chuyển sang định dạng PIL
        cropped_image = Image.fromarray(cropped_image)
    elif not isinstance(cropped_image, Image.Image):
        # Nếu không phải là numpy array hoặc PIL Image, báo lỗi
        raise TypeError("Unsupported image format for OCR processing.")

    # Sử dụng 'vie' cho tiếng Việt để nhận diện văn bản
    text = pytesseract.image_to_string(cropped_image, lang='vie')
    remove_text = remove_vietnamese_accent(text).lower()  # Remove Vietnamese accents and convert to lowercase

    print(remove_text)

    # Kiểm tra văn bản với các từ khóa
    keywords = [
        'bao cao ket qua',
        'bang can doi ke toan',
        'bao cao luu chuyen tien te',
        'bao cao tinh hinh tai chinh',
        'bao cao thay doi von',
        'bao cao tinh hinh',
        'bao cao tinh hjnh',
        'bao cao tjnh hinh',
        'bao cao thay doj von',
        'bao cao luu chuyen tjen te',
        'bao cao ket cjua',
        'baang can doi ke toan',
        'baang can doj ke toan',
        'bao cao luu chizen',
        'bao cao luu chl_jyen',
        'bao cao luu chizjen',
        'bao cao luu chizjyen'
    ]

    # Nếu văn bản có chứa bất kỳ từ khóa nào, trả về True
    if any(keyword in remove_text for keyword in keywords):
        return True
    else:
        return False

# ======== MAIN PIPELINE ========
if __name__ == "__main__":
    root_path = r"/home/huedt/Documents/PythonProjects/ELTReportFinance/pdfs"
    pdf2image_path = r'/home/huedt/Documents/PythonProjects/ELTReportFinance/imageTable'
    os.makedirs(pdf2image_path, exist_ok=True)

    for dirpath, _, filenames in os.walk(root_path):
        for filename in filenames:
            if filename.endswith('.pdf'):
                pdf_path = os.path.join(dirpath, filename)
                pdfname = os.path.splitext(filename)[0]
                folder_image_path = os.path.join(pdf2image_path, pdfname)
                os.makedirs(folder_image_path, exist_ok=True)

                pdf_page = count_pdf_pages(pdf_path)
                convert_page = min(pdf_page, 15)

                images = convert_from_path(pdf_path, first_page=1, last_page=convert_page)
                for i, image in enumerate(images):
                    adjusted = adjust_image_orientation(np.array(image))
                    processed = process_and_rotate_image(np.array(adjusted))

                    img_has_table, table_img, coords, tname_count = detect_table(processed, 0.5)

                    if img_has_table is not None and coords is not None:
                        if check_area(Image.fromarray(img_has_table), coords):
                            pil_table = Image.fromarray(table_img)
                            image_path = os.path.join(folder_image_path, f"page_{i + 1}.jpg")
                            pil_table.save(image_path, "JPEG")
                            print("Saved:", image_path)
