import numpy as np
import soundfile as sf
from numpy.fft import fft, ifft
from scipy.signal import get_window
import matplotlib.pyplot as plt


def noise_reduction(
        input_file,
        output_file,
        frame_size=1024,
        overlap=0.5,
        noise_start=5,
        noise_end=1200,
        suppression_factor=1.8,
        protection_factor=0.05
):

    audio, sample_rate = sf.read(input_file)

    # преобразование в моно
    if audio.ndim > 1:
        audio = np.mean(audio, axis=1)

    # нормирование всего сигнала
    audio = audio.astype(np.float32)
    peak = np.max(np.abs(audio))
    audio /= peak

    # вычисление шага смещения фрейма
    hop_size = int(frame_size * (1 - overlap))

    # генерация оконной функции Ханна
    window = get_window('hann', frame_size)

    noise_frames = []
    for i in range(noise_start * sample_rate // 1000, min(noise_end * sample_rate // 1000, len(audio) - frame_size), hop_size):
        # выделяем участок и умножаем его на окно
        frame = audio[i:i + frame_size] * window

        # вычисляем БПФ
        noise_fft = fft(frame)

        noise_frames.append(np.abs(noise_fft))

    # вычисление профиля шума
    noise_footprint = np.mean(noise_frames, axis=0) if noise_frames else np.zeros(frame_size)

    output_signal = np.zeros(len(audio))
    window_sum = np.zeros(len(audio))

    for i in range(0, len(audio) - frame_size, hop_size):
        # оконное преобразование
        frame = audio[i:i + frame_size] * window

        # вычисляем БПФ
        frame_fft = fft(frame)

        # получаем амплитудный спектра
        magnitude = np.abs(frame_fft)

        # получаем фазовый спектра
        phase = np.angle(frame_fft)

        # вычисление очищенного амплитудного спектра
        clean_magnitude = np.maximum(magnitude - suppression_factor * noise_footprint,
                                     protection_factor * magnitude
                                     )

        # объединение очищенной амплитуды с исходной фазой
        clean_fft = clean_magnitude * np.exp(1j * phase)

        # вычисляем обратное БПФ
        clean_frame = np.real(ifft(clean_fft))

        # наложение обработанного фрейма с перекрытиемсс
        output_signal[i:i + frame_size] += clean_frame
        window_sum[i:i + frame_size] += window

    window_sum[window_sum == 0] = 1
    output_signal /= window_sum

    output_signal = output_signal * 32767
    output_signal = np.clip(output_signal, -32768, 32767)
    output_signal = output_signal.astype(np.int16)

    plt.figure(figsize=(12, 8))

    plt.subplot(2, 1, 1)
    plt.specgram(audio, Fs=sample_rate, NFFT=frame_size, noverlap=hop_size)
    plt.colorbar()
    plt.title('Original Audio Spectrogram')
    plt.ylabel('Frequency (Hz)')

    plt.subplot(2, 1, 2)
    plt.specgram(output_signal, Fs=sample_rate, NFFT=frame_size, noverlap=hop_size)
    plt.colorbar()
    plt.title('Cleaned Audio Spectrogram')
    plt.ylabel('Frequency (Hz)')
    plt.xlabel('Time (s)')

    plt.tight_layout()
    plt.show()

    sf.write(output_file, output_signal, sample_rate)


def main():
    input_file = '20250521_200621_3.mp3'
    output_file = 'output1.mp3'

    noise_reduction(input_file, output_file)

if __name__ == '__main__':
    main()