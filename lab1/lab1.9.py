import cv2

# Задача 8

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    h, w = frame.shape[:2]
    center_x, center_y = w // 2, h // 2

    b, g, r = frame[center_y, center_x]

    if r >= g and r >= b:
        color = (0, 0, 255)
    elif g >= r and g >= b:
        color = (0, 255, 0)
    else:
        color = (255, 0, 0)

    bar_thickness = 30
    bar_length = 100

    cv2.rectangle(
        frame,
        (center_x - bar_length, center_y - bar_thickness // 2),
        (center_x + bar_length, center_y + bar_thickness // 2),
        color, -1
    )

    cv2.rectangle(
        frame,
        (center_x - bar_thickness // 2, center_y - bar_length),
        (center_x + bar_thickness // 2, center_y - bar_thickness // 2),
        color, -1
    )

    cv2.rectangle(
        frame,
        (center_x - bar_thickness // 2, center_y + bar_thickness // 2),
        (center_x + bar_thickness // 2, center_y + bar_length),
        color, -1
    )

    cv2.imshow("Cross", frame)

    if cv2.waitKey(1) & 0xFF == 27:  # ESC
        break

cap.release()
cv2.destroyAllWindows()



# Задача 9


url = "http://192.168.0.13:8080..3.3/video"

cap = cv2.VideoCapture(url)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    cv2.imshow("Phone Cam", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
