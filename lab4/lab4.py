import cv2 as cv
import numpy as np
import math


def gradient_intensity(image):
    sobel_x = np.array([
        [-1, 0, 1],
        [-2, 0, 2],
        [-1, 0, 1]
    ], dtype=np.float32)

    sobel_y = np.array([
        [-1, -2, -1],
        [0, 0, 0],
        [1, 2, 1]
    ], dtype=np.float32)

    padded = np.pad(image, pad_width=1, mode='edge')
    rows, cols = image.shape
    grad_x = np.zeros_like(image, dtype=np.float32)
    grad_y = np.zeros_like(image, dtype=np.float32)

    for i in range(rows):
        for j in range(cols):
            roi = padded[i:i + 3, j:j + 3]
            grad_x[i, j] = np.sum(roi * sobel_x)
            grad_y[i, j] = np.sum(roi * sobel_y)

    vector_length = np.sqrt(grad_x ** 2 + grad_y ** 2)
    vector_angle = np.arctan2(grad_y, grad_x)
    return vector_length, vector_angle


def non_maximum_suppression(vec_length, vec_angle):

    suppressed = np.zeros_like(vec_length, dtype=np.float32)

    angle = vec_angle * 180.0 / np.pi
    angle[angle < 0] += 180

    for i in range(1, vec_length.shape[0] - 1):
        for j in range(1, vec_length.shape[1] - 1):
            if (0 <= angle[i, j] < 22.5) or (157.5 <= angle[i, j] <= 180):

                q = vec_length[i, j + 1]
                r = vec_length[i, j - 1]
            elif 22.5 <= angle[i, j] < 67.5:

                q = vec_length[i + 1, j - 1]
                r = vec_length[i - 1, j + 1]
            elif 67.5 <= angle[i, j] < 112.5:

                q = vec_length[i + 1, j]
                r = vec_length[i - 1, j]
            elif 112.5 <= angle[i, j] < 157.5:

                q = vec_length[i - 1, j - 1]
                r = vec_length[i + 1, j + 1]

            if vec_length[i, j] >= q and vec_length[i, j] >= r:
                suppressed[i, j] = vec_length[i, j]
            else:
                suppressed[i, j] = 0

    max_grad = np.max(suppressed)
    low_level = max_grad * 0.05
    high_level = max_grad * 0.15

    return suppressed, low_level, high_level


def double_threshold(suppressed_image, low_level, high_level):
    strong_edges = np.zeros_like(suppressed_image, dtype=np.uint8)


    for i in range(suppressed_image.shape[0]):
        for j in range(suppressed_image.shape[1]):
            if suppressed_image[i, j] >= high_level:
                strong_edges[i, j] = 255
            elif suppressed_image[i, j] >= low_level:
                strong_edges[i, j] = 75


    return strong_edges


def hysteresis(weak_edges):

    rows, cols = weak_edges.shape
    edges = weak_edges.copy()


    for i in range(1, rows - 1):
        for j in range(1, cols - 1):

            if edges[i, j] == 75:

                has_strong_neighbor = False
                for di in [-1, 0, 1]:
                    for dj in [-1, 0, 1]:
                        if edges[i + di, j + dj] == 255:
                            has_strong_neighbor = True
                            break
                    if has_strong_neighbor:
                        break


                if has_strong_neighbor:
                    edges[i, j] = 255
                else:
                    edges[i, j] = 0


    final_edges = np.zeros_like(edges, dtype=np.uint8)
    final_edges[edges == 255] = 255
    return final_edges



if __name__ == "__main__":

    image_path = 'photo_dog.jpg'
    image = cv.imread(image_path)


    if image is None:
        print(f"Ошибка: не удалось загрузить изображение '{image_path}'")
        exit()


    gray_image = cv.cvtColor(image, cv.COLOR_BGR2GRAY)

    sigma = 1.0
    kernel_size = 5
    blurred_image = cv.GaussianBlur(gray_image, (kernel_size, kernel_size), sigma)

    gradient_mag, gradient_angle = gradient_intensity(blurred_image)

    mag_normalized = cv.normalize(gradient_mag, None, 0, 255, cv.NORM_MINMAX, dtype=cv.CV_8U)

    suppressed, low_thresh, high_thresh = non_maximum_suppression(gradient_mag, gradient_angle)


    thresholded = double_threshold(suppressed, low_thresh, high_thresh)
    edges = hysteresis(thresholded)

    cv_canny = cv.Canny(blurred_image, int(low_thresh), int(high_thresh))

    cv.imshow("1. Grayscale Image", gray_image)
    cv.imshow("2. Blurred Image (Gaussian)", blurred_image)
    cv.imshow("3. Gradient Magnitude", mag_normalized)
    cv.imshow("4. Canny Edges (Our Implementation)", edges)
    cv.imshow("5. OpenCV Canny", cv_canny)

    cv.waitKey(0)
    cv.destroyAllWindows()
    