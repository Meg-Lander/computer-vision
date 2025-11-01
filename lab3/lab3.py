import cv2 as cv
import numpy as np
import math

def gauss_matrix(size, sigma):
    a = size // 2
    b = size // 2
    multiplier = 1.0 / (2 * math.pi * sigma**2)
    ker = np.zeros((size, size), dtype=np.float64)
    for i in range(size):
        for j in range(size):
            dx = i - a
            dy = j - b
            exp = -(dx*dx + dy*dy) / (2 * sigma**2)
            ker[i, j] = multiplier * math.exp(exp)
    return ker

def normalize(ker):
    total = np.sum(ker)
    print(total)
    if total == 0:
        return ker
    return ker / total

def gaussi_filter(image, ker):
    img_h, img_w = image.shape
    k_h, k_w = ker.shape
    pad = k_h // 2
    output = np.zeros_like(image, dtype=np.float64)
    for i in range(pad, img_h - pad):
        for j in range(pad, img_w - pad):
            region = image[i - pad:i + pad + 1, j - pad:j + pad + 1]
            output[i, j] = np.sum(region * ker)
    output = np.clip(output, 0, 255).astype(np.uint8)
    return output


img_path = 'photo_dog.jpg'
img = cv.imread(img_path, cv.IMREAD_GRAYSCALE)

param = [ (9, 2.0), (5, 1.0)]

cv.imshow('my image', img)

for size, sigma in param:
    ker = gauss_matrix(size, sigma)
    ker = normalize(ker)

    filtered_manual = gaussi_filter(img, ker)
    filtered_cv = cv.GaussianBlur(img, (size, size), sigma)

    cv.imshow(f'my blur  {size}, {sigma}', filtered_manual)
    cv.imshow(f'CV blur {size}, {sigma})', filtered_cv)

cv.waitKey(0)
cv.destroyAllWindows()
