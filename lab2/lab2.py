import cv2 as cv
import numpy as np

camera = cv.VideoCapture(0)

core = np.ones((5, 5), np.uint8)

while True:
    ret, frame = camera.read()
    if not ret:
        break

    hsv_img = cv.cvtColor(frame, cv.COLOR_BGR2HSV)

    lower_red1 = np.array([0, 100, 70])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 100, 70])
    upper_red2 = np.array([180, 255, 255])

    mask1 = cv.inRange(hsv_img, lower_red1, upper_red1)
    mask2 = cv.inRange(hsv_img, lower_red2, upper_red2)
    mask = cv.bitwise_or(mask1, mask2)
    cv.imshow('Mask', mask)

    eroded_mask = cv.erode(mask, core, iterations=2)
    dilated_mask = cv.dilate(eroded_mask, core, iterations=2)
    cv.imshow('Erode and Dilate', dilated_mask)

    moms = cv.moments(dilated_mask)
    ploshad = moms['m00']

    if ploshad > 400:

        center_x = int(moms['m10'] / ploshad)
        center_y = int(moms['m01'] / ploshad)


        coords = cv.findNonZero(dilated_mask)
        if coords is not None:
            x_vals = coords[:, 0, 0]
            y_vals = coords[:, 0, 1]

            min_x, max_x = int(x_vals.min()), int(x_vals.max())
            min_y, max_y = int(y_vals.min()), int(y_vals.max())

            cv.rectangle(frame, (min_x, min_y), (max_x, max_y), (0, 0, 0), 2)
            cv.circle(frame, (center_x, center_y), 5, (0, 0, 255), -1)

            cv.putText(frame, f'Ploshad: {int(ploshad)}', (min_x, min_y - 10), cv.FONT_HERSHEY_SIMPLEX, 0.6,
                       (0, 255, 0), 2)

    cv.imshow('Tracking', frame)

    if cv.waitKey(1) & 0xFF == ord('q'):
        break

camera.release()
cv.destroyAllWindows()