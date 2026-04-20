import numpy as np

class SimpleModel:
    def __init__(self):
        self.w = None

    def fit(self, X, y):
        self.w = np.linalg.pinv(X) @ y

    def predict(self, X):
        return X @ self.w