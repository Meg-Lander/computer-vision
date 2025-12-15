import time
import matplotlib.pyplot as plt
from tensorflow.keras.datasets import mnist
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Flatten
from tensorflow.keras.utils import to_categorical


def plot_history(history):
    loss = history.history['loss']
    val_loss = history.history['val_loss']
    accuracy = history.history['accuracy']
    val_accuracy = history.history['val_accuracy']
    epochs = range(1, len(loss) + 1)

    plt.figure(figsize=(10, 6))
    plt.plot(epochs, loss, 'go-', linewidth=2, markersize=8, label='Training Loss')  # зеленый цвет
    plt.plot(epochs, val_loss, 'mo--', linewidth=2, markersize=8, label='Validation Loss')  # пурпурный цвет
    plt.title('Training and Validation Loss', fontsize=14)
    plt.xlabel('Epochs', fontsize=12)
    plt.ylabel('Loss (Categorical Crossentropy)', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(fontsize=12)
    plt.tight_layout()

    plt.figure(figsize=(10, 6))
    plt.plot(epochs, accuracy, 'co-', linewidth=2, markersize=8, label='Training Accuracy')  # голубой цвет
    plt.plot(epochs, val_accuracy, 'yo--', linewidth=2, markersize=8, label='Validation Accuracy')  # желтый цвет
    plt.title('Training and Validation Accuracy', fontsize=14)
    plt.xlabel('Epochs', fontsize=12)
    plt.ylabel('Accuracy', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(fontsize=12)
    plt.tight_layout()

    plt.show()


(x_train, y_train), (x_test, y_test) = mnist.load_data()

print(f"Размерность обучающих изображений: {x_train.shape}")
print(f"Размерность обучающих меток: {y_train.shape}")
print(f"Количество тестовых примеров: {x_test.shape[0]}")

x_train = x_train.astype('float32') / 255
x_test = x_test.astype('float32') / 255

num_classes = 10
y_train_ohe = to_categorical(y_train, num_classes=num_classes)
y_test_ohe = to_categorical(y_test, num_classes=num_classes)

model = Sequential([
    Flatten(input_shape=(28, 28)),
    Dense(256, activation='relu', name='Hidden_1'),
    Dense(128, activation='relu', name='Hidden_2'),
    Dense(num_classes, activation='softmax', name='Output_Layer')
])
model.summary()

model.compile(optimizer='adam',
              loss='categorical_crossentropy',
              metrics=['accuracy'])

start = time.time()
history_extended = model.fit(x_train, y_train_ohe,
                            epochs=20,
                            batch_size=32,
                            validation_data=(x_test, y_test_ohe),
                            verbose=1)
finish = time.time() - start
print(f"Время обучения: {finish:.2f} секунд")

plot_history(history_extended)