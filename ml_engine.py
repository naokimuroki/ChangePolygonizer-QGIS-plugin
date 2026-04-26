import numpy as np


class SimpleModel:
    def __init__(self):
        self.w = None

    def _add_bias(self, X):
        ones = np.ones((X.shape[0], 1))
        return np.hstack([X, ones])

    def fit(self, X, y):
        Xb = self._add_bias(X)
        self.w = np.linalg.pinv(Xb) @ y

    def predict(self, X):
        Xb = self._add_bias(X)
        y = Xb @ self.w

        # 安定化（0〜1にクリップ）
        return np.clip(y, 0.0, 1.0)