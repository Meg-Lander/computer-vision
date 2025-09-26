import cv2

# Задание 6

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    h, w = frame.shape[:2]
    center_x, center_y = w // 2, h // 2

    bar_thickness = 30
    bar_length = 100

    cv2.rectangle(
        frame,
        (center_x - bar_length, center_y - bar_thickness // 2),
        (center_x + bar_length, center_y + bar_thickness // 2),
        (0, 0, 255), 2
    )

    cv2.rectangle(
        frame,
        (center_x - bar_thickness // 2, center_y - bar_length),
        (center_x + bar_thickness // 2, center_y - bar_thickness // 2),
        (0, 0, 255), 2
    )

    cv2.rectangle(
        frame,
        (center_x - bar_thickness // 2, center_y + bar_thickness // 2),
        (center_x + bar_thickness // 2, center_y + bar_length),
        (0, 0, 255), 2
    )

    cv2.imshow("Cross", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()

# Задание 7

cap = cv2.VideoCapture(0)

width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)

fourcc = cv2.VideoWriter_fourcc(*"XVID")
out = cv2.VideoWriter("output.avi", fourcc, fps, (width, height))

while True:
    ret, frame = cap.read()
    if not ret:
        break

    cv2.imshow("Webcam", frame)

    out.write(frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
out.release()
cv2.destroyAllWindows()