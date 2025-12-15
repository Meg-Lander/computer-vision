import time
from tensorflow.keras.datasets import mnist
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense
from tensorflow.keras.utils import to_categorical
import matplotlib.pyplot as plt


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

x_train = x_train.astype('float32') / 255
x_test = x_test.astype('float32') / 255

x_train_cnn = x_train.reshape(x_train.shape[0], 28, 28, 1)
x_test_cnn = x_test.reshape(x_test.shape[0], 28, 28, 1)

y_train_ohe = to_categorical(y_train, num_classes=10)
y_test_ohe = to_categorical(y_test, num_classes=10)

print(f"Размерность данных для CNN: {x_train_cnn.shape}")
print(f"Размерность меток: {y_train_ohe.shape}")

cnn_model = Sequential([
    Conv2D(32, kernel_size=(3, 3), activation='relu', input_shape=(28, 28, 1), name='Conv_1'),
    MaxPooling2D(pool_size=(2, 2), name='Pool_1'),
    Conv2D(64, kernel_size=(3, 3), activation='relu', name='Conv_2'),
    MaxPooling2D(pool_size=(2, 2), name='Pool_2'),
    Flatten(name='Flatten'),
    Dense(128, activation='tanh', name='Dense_Hidden'),
    Dense(10, activation='softmax', name='Output_Layer')
])

cnn_model.summary()

cnn_model.compile(optimizer='adam',
                  loss='categorical_crossentropy',
                  metrics=['accuracy'])

start = time.time()
history_extended = cnn_model.fit(x_train_cnn, y_train_ohe,
                            epochs=20,
                            batch_size=32,
                            validation_data=(x_test_cnn, y_test_ohe),
                            verbose=1)
finish = time.time() - start
print(finish)



plot_history(history_extended)