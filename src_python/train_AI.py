import sys
import numpy as np
import AI
from datetime import datetime

class NeuralNetwork:
    def __init__(self, layer_sizes: list[int]):
        # layer_sizes = [nb_entrées, nb_neurones_couche1, ..., nb_sorties]
        # ex: [5, 16, 8, 3] pour 5 entrées, 2 couches cachées, 3 sorties
        self.weights = []
        self.biases  = []

        for i in range(len(layer_sizes) - 1):
            # Initialisation de He : évite que le gradient explose ou disparaisse
            w = np.random.randn(layer_sizes[i], layer_sizes[i+1]) * np.sqrt(2 / layer_sizes[i])
            b = np.zeros((1, layer_sizes[i+1]))
            self.weights.append(w)
            self.biases.append(b)

    def relu(self, x):
        return np.maximum(0, x)

    def relu_derivative(self, x):
        return (x > 0).astype(float)

    def softmax(self, x):
        # Pour la couche de sortie (classification : BUY / SELL / HOLD)
        e = np.exp(x - np.max(x, axis=1, keepdims=True)) # stabilité numérique
        return e / e.sum(axis=1, keepdims=True)

    def forward(self, X):
        self.activations = [X]   # stocke les sorties de chaque couche
        self.z_values    = []    # stocke les valeurs avant activation

        current = X
        for i, (w, b) in enumerate(zip(self.weights, self.biases)):
            z = current @ w + b          # transformation linéaire
            self.z_values.append(z)

            if i < len(self.weights) - 1:
                current = self.relu(z)   # ReLU pour les couches cachées
            else:
                current = self.softmax(z) # Softmax pour la sortie
            self.activations.append(current)

        return current  # probabilités pour chaque classe

    def backward(self, X, y_true, learning_rate=0.001):
        m = X.shape[0]  # nombre d'exemples
        grad_weights = [None] * len(self.weights)
        grad_biases  = [None] * len(self.biases)

        # Gradient de la perte (cross-entropy + softmax combinés)
        delta = self.activations[-1] - y_true  # très simple grâce au softmax

        for i in reversed(range(len(self.weights))):
            grad_weights[i] = self.activations[i].T @ delta / m
            grad_biases[i]  = delta.mean(axis=0, keepdims=True)

            if i > 0:  # pas besoin de remonter avant la première couche
                delta = (delta @ self.weights[i].T) * self.relu_derivative(self.z_values[i-1])

        # Mise à jour des poids
        for i in range(len(self.weights)):
            self.weights[i] -= learning_rate * grad_weights[i]
            self.biases[i]  -= learning_rate * grad_biases[i]

    def cross_entropy_loss(self, y_pred, y_true):
        # Mesure l'erreur entre la prédiction et la réalité
        return -np.mean(np.sum(y_true * np.log(y_pred + 1e-9), axis=1))

    def train(self, X, y, epochs=1000, learning_rate=0.001):
        for epoch in range(epochs):
            y_pred = self.forward(X)
            loss   = self.cross_entropy_loss(y_pred, y)
            self.backward(X, y, learning_rate)

            if epoch % 100 == 0:
                print(f"Epoch {epoch:4d} | Loss: {loss:.4f}")

    def predict(self, X):
        probs = self.forward(X)
        return np.argmax(probs, axis=1)  # 0=HOLD, 1=BUY, 2=SELL
    
# train_AI.py — entraînement offline sur données historiques
def build_dataset(filepath: str) -> tuple[np.ndarray, np.ndarray]:
    if not filepath:
        print("Erreur : l'IA a besoin d'un dataset", file=sys.stderr)
        exit(1)

    start = datetime.now()
    print("Démarrage de la construction du dataset...", file=sys.stderr)

    stock_dict: dict[str, AI.Stock] = {}

    with open(filepath, "r") as file:
        for line in file:
            line = line.strip()
            if not line: continue

            parts = line.split(",")
            if len(parts) < 4: continue  # ligne mal formée

            date, ticker, price, volume = parts[0], parts[1], float(parts[2]), int(parts[3])

            if price == -1: continue

            if ticker not in stock_dict:
                stock_dict[ticker] = AI.Stock(ticker=ticker)

            stock_dict[ticker].historic_price.append(price)
            stock_dict[ticker].historic_quantity.append(volume)
            stock_dict[ticker].total_quantity += volume

    # Construction du dataset sur tous les stocks
    X, y = [], []
    for stock in stock_dict.values():
        prices = np.array(stock.historic_price)
        print(f"  {stock.ticker} : {len(prices)} points", file=sys.stderr)

        for i in range(26, len(prices) - 1):
            sub_stock = AI.Stock(
                ticker=stock.ticker,
                historic_price=list(prices[:i+1])
            )
            features = AI.compute_features(sub_stock)
            if features is None: continue

            variation = (prices[i+1] - prices[i]) / prices[i]
            if   variation >  0.01: label = [0, 1, 0]  # BUY
            elif variation < -0.01: label = [0, 0, 1]  # SELL
            else:                   label = [1, 0, 0]  # HOLD

            X.append(features)
            y.append(label)

    elapsed = (datetime.now() - start).seconds
    print(f"Dataset construit : {len(X)} exemples en {elapsed}s", file=sys.stderr)
    return np.array(X), np.array(y)