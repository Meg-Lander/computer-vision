import cv2

# Задание 2
img1 = cv2.imread("photo_dog.jpg") # IMREAD_COLOR по умолчанию
img2 = cv2.imread("photo_dog_bmp.bmp", cv2.IMREAD_GRAYSCALE)
img3 = cv2.imread("photo_dog_png.png", cv2.IMREAD_UNCHANGED)

cv2.namedWindow("Window1", cv2.WINDOW_NORMAL)
cv2.imshow("Window1", img1)

cv2.namedWindow("Window2", cv2.WINDOW_AUTOSIZE)
cv2.imshow("Window2", img2)

cv2.namedWindow("Window3", cv2.WINDOW_FREERATIO)
cv2.imshow("Window3", img3)

cv2.waitKey(0)
cv2.destroyAllWindows()

# Задание 3
cap = cv2.VideoCapture("sample-5s.mp4")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.resize(frame, (1000, 400))
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    cv2.imshow("Video Gray", gray)

    if cv2.waitKey(25) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()

# Задание 4
cap = cv2.VideoCapture("sample-5s.mp4")
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)

fourcc = cv2.VideoWriter_fourcc(*"XVID")
out = cv2.VideoWriter("output.avi", fourcc, fps, (width, height))

while True:
    ret, frame = cap.read()
    if not ret:
        break
    out.write(frame)
    cv2.imshow("Recording", frame)
    if cv2.waitKey(25) & 0xFF == 27:
        break

cap.release()
out.release()
cv2.destroyAllWindows()

# Задание 5
img = cv2.imread("photo_dog.jpg")
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

cv2.imshow("Original", img)
cv2.imshow("HSV", hsv)
cv2.waitKey(0)
cv2.destroyAllWindows()
