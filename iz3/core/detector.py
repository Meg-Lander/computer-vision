# core/detector.py
import os
import cv2
import time
import numpy as np
from math import hypot
from itertools import combinations
from ultralytics import YOLO
from qreader import QReader


class QRDetector:
    def __init__(self, model_path):
        self.model_path = model_path
        self.model = None
        self.qreader = None
        self._load_model()

    def _load_model(self):
        if os.path.exists(self.model_path):
            # Загрузка YOLO модели
            self.model = YOLO(self.model_path)
            # Загрузка QReader для декодирования (размер 'm' - баланс скорости/точности)
            self.qreader = QReader(model_size='m')
            print(f"[SYSTEM] Model Loaded: {self.model_path}")
        else:
            raise FileNotFoundError(f"Model file not found at {self.model_path}")

    def _get_triangle_score(self, boxes_indices, all_boxes):
        """
        Геометрическая проверка: образуют ли 3 квадрата (finder patterns)
        правильный треугольник, характерный для QR кода.
        """
        idx1, idx2, idx3 = boxes_indices
        b1, b2, b3 = all_boxes[idx1], all_boxes[idx2], all_boxes[idx3]

        # 1. Проверка соотношения сторон самих боксов (они должны быть квадратными)
        for b in [b1, b2, b3]:
            w_box = b[2] - b[0]
            h_box = b[3] - b[1]
            if min(w_box, h_box) == 0: return float('inf'), None, None
            aspect = max(w_box, h_box) / min(w_box, h_box)
            if aspect > 1.8: return float('inf'), None, None

        # 2. Проверка размеров (боксы должны быть примерно одинаковыми)
        w1, w2, w3 = b1[2] - b1[0], b2[2] - b2[0], b3[2] - b3[0]
        sizes = [w1, w2, w3]
        avg_size = sum(sizes) / 3
        max_size = max(sizes)
        min_size = min(sizes)

        if max_size > min_size * 1.5: return float('inf'), None, None

        # Центры боксов
        p1 = ((b1[0] + b1[2]) // 2, (b1[1] + b1[3]) // 2)
        p2 = ((b2[0] + b2[2]) // 2, (b2[1] + b2[3]) // 2)
        p3 = ((b3[0] + b3[2]) // 2, (b3[1] + b3[3]) // 2)
        points = [p1, p2, p3]

        # Расстояния между центрами
        dists = []
        dists.append((hypot(p1[0] - p2[0], p1[1] - p2[1]), 0, 1, 2))
        dists.append((hypot(p1[0] - p3[0], p1[1] - p3[1]), 0, 2, 1))
        dists.append((hypot(p2[0] - p3[0], p2[1] - p3[1]), 1, 2, 0))
        dists.sort(key=lambda x: x[0])

        short1, _, _, _ = dists[0]
        short2, _, _, _ = dists[1]
        long_side, _, _, corner_idx = dists[2]

        if short1 == 0: return float('inf'), None, None

        # 3. Проверка дистанции относительно размера паттерна
        rel_dist = long_side / avg_size
        if rel_dist > 15.0: return float('inf'), None, None

        # Длинная сторона должна быть гипотенузой
        if long_side < short1 or long_side < short2: return float('inf'), None, None

        # Катеты должны быть примерно равны
        ratio_legs = max(short1, short2) / min(short1, short2)
        if ratio_legs > 2.5: return float('inf'), None, None

        # 4. Проверка угла (должен быть 90 градусов, теорема косинусов)
        cos_angle = (short1 ** 2 + short2 ** 2 - long_side ** 2) / (2 * short1 * short2)
        angle_err = abs(cos_angle)
        if angle_err > 0.5: return float('inf'), None, None

        # Рассчет итоговой оценки (чем меньше, тем лучше)
        size_diff = (max_size - min_size) / min_size
        score = (size_diff * 3.0) + (angle_err * 2.0) + (rel_dist * 0.05)

        return score, points[corner_idx], [p1, p2, p3]

    def group_finder_patterns(self, boxes, confidences):
        """
        Перебирает все комбинации найденных боксов по 3 штуки
        и ищет среди них валидные QR-паттерны.
        """
        n = len(boxes)
        if n < 3: return []
        possible_groups = []

        # Перебор всех троек
        for indices in combinations(range(n), 3):
            score, corner, pts = self._get_triangle_score(indices, boxes)
            if score != float('inf'):
                avg_yolo_conf = (confidences[indices[0]] + confidences[indices[1]] + confidences[indices[2]]) / 3

                # Максимальный размах для определения зоны обрезки
                max_span = max(hypot(pts[0][0] - pts[1][0], pts[0][1] - pts[1][1]),
                               hypot(pts[1][0] - pts[2][0], pts[1][1] - pts[2][1]),
                               hypot(pts[0][0] - pts[2][0], pts[0][1] - pts[2][1]))

                possible_groups.append({
                    'score': score,
                    'yolo_conf': avg_yolo_conf,
                    'indices': set(indices),
                    'points': pts,
                    'corner': corner,
                    'span': max_span
                })

        # Сортируем по "геометрической идеальности"
        possible_groups.sort(key=lambda x: x['score'])

        # Убираем дубликаты (если один паттерн попал в несколько групп)
        final_groups = []
        used_indices = set()
        for g in possible_groups:
            if not g['indices'].intersection(used_indices):
                final_groups.append(g)
                used_indices.update(g['indices'])
        return final_groups

    def get_qr_crop(self, image, group):
        """Вырезает область с QR кодом из изображения"""
        points = group['points']
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        span = group['span']

        # Добавляем отступы
        pad = int(span * 0.6) + 20
        h, w = image.shape[:2]

        x1 = max(0, min(xs) - pad)
        y1 = max(0, min(ys) - pad)
        x2 = min(w, max(xs) + pad)
        y2 = min(h, max(ys) + pad)

        if (x2 - x1) < 20 or (y2 - y1) < 20: return None
        return image[y1:y2, x1:x2]

    def try_decode_rotated(self, roi):
        """Пытается декодировать ROI, вращая его на 0, 90, 180 градусов"""
        if roi is None: return None

        rotations = [(0, roi), (90, cv2.rotate(roi, cv2.ROTATE_90_CLOCKWISE)), (180, cv2.rotate(roi, cv2.ROTATE_180))]

        for _, img in rotations:
            # 1. Попытка на RGB
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            decoded = self.qreader.detect_and_decode(image=rgb)
            if decoded and decoded[0]: return decoded[0]

            # 2. Попытка на Бинаризованном (для сложных условий)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            decoded_bin = self.qreader.detect_and_decode(image=thresh)
            if decoded_bin and decoded_bin[0]: return decoded_bin[0]

        return None

    def detect_and_decode(self, image_bgr):
        """
        Основной метод.
        Вход: изображение (BGR).
        Выход: список данных, отрисованное изображение, время выполнения.
        """
        t_start = time.time()
        qr_data_list = []
        output_img = image_bgr.copy()

        # 1. Запуск YOLO
        results = self.model(image_bgr, conf=0.25, verbose=False)
        boxes_list = []
        conf_list = []

        if results and results[0].boxes:
            for box in results[0].boxes:
                boxes_list.append(box.xyxy[0].cpu().numpy().astype(int))
                conf_list.append(float(box.conf[0].cpu().numpy()))

        # 2. Группировка квадратов в треугольники
        groups = self.group_finder_patterns(boxes_list, conf_list)

        # 3. Декодирование и отрисовка
        for i, group in enumerate(groups):
            pts = np.array(group['points'], np.int32)

            # Попытка декодировать контент
            text = self.try_decode_rotated(self.get_qr_crop(image_bgr, group))

            # Цвет: Зеленый если декодирован, Оранжевый если просто геометрически найден
            color = (100, 255, 0) if text else (0, 165, 255)

            # Рисуем треугольник между Finder Patterns
            cv2.polylines(output_img, [pts], True, color, 3, cv2.LINE_AA)

            if text:
                qr_data_list.append({
                    'text': text,
                    'conf': group['yolo_conf'],
                    'geo_score': group['score'],
                    # ВАЖНО: сохраняем координаты для перерисовки в галерее
                    'points': group['points'],
                    'corner': group['corner']
                })

                corner = group['corner']
                label = f"ID:{i} | C:{group['yolo_conf']:.2f}"
                # Рисуем подпись
                cv2.putText(output_img, label, (int(corner[0]), int(corner[1]) - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)

        t_end = time.time()
        # Возвращаем: Данные, Картинку с рисунками, Время
        return qr_data_list, output_img, (t_end - t_start)