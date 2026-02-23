import numpy as np

__all__ = ['rmse','bias','conservativeness']

def rmse(y_true, y_pred):
    y_true = np.array(y_true); y_pred = np.array(y_pred)
    return float(np.sqrt(np.mean((y_true - y_pred)**2)))

def bias(y_true, y_pred):
    y_true = np.array(y_true); y_pred = np.array(y_pred)
    return float(np.mean(y_pred - y_true))

def conservativeness(y_true, y_pred):
    y_true = np.array(y_true); y_pred = np.array(y_pred)
    over = np.sum(y_pred >= y_true)
    return float(over / max(len(y_true), 1))
