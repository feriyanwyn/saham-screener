"""Feature Engineering & Time-Series Sequence Generator for Stock Prediction."""
from typing import Tuple
import numpy as np
import pandas as pd
try:
    from sklearn.preprocessing import StandardScaler
except ImportError:
    class StandardScaler:
        """Lightweight numpy fallback when scikit-learn is omitted in serverless deploy."""
        def fit_transform(self, X: np.ndarray) -> np.ndarray:
            self.mean_ = np.mean(X, axis=0)
            self.scale_ = np.where(np.std(X, axis=0) == 0, 1.0, np.std(X, axis=0))
            return (X - self.mean_) / self.scale_

        def transform(self, X: np.ndarray) -> np.ndarray:
            return (X - self.mean_) / self.scale_


class FeatureEngineer:
    """Extracts, normalizes, and packages time-series features for LSTM & BiLSTM."""

    FEATURE_COLS = [
        "return_pct", "rsi_14", "macd", "macd_hist",
        "ema_dist_9", "ema_dist_20", "vwap_dist", "atr_pct", "relative_volume"
    ]

    @classmethod
    def prepare_features(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Menghasilkan fitur stasioner yang dinormalisasi."""
        if df.empty or len(df) < 20:
            return pd.DataFrame()

        data = df.copy()
        data["return_pct"] = data["close"].pct_change().fillna(0.0)
        data["ema_dist_9"] = (data["close"] - data["ema_9"]) / data["close"]
        data["ema_dist_20"] = (data["close"] - data["ema_20"]) / data["close"]
        data["vwap_dist"] = (data["close"] - data["vwap"]) / data["close"]
        data["atr_pct"] = data["atr_14"] / data["close"]

        data["target_next_return"] = data["close"].pct_change().shift(-1)
        data["target_next_direction"] = (data["target_next_return"] > 0).astype(int)
        return data

    @classmethod
    def create_sequences(
        cls, 
        df_features: pd.DataFrame, 
        sequence_length: int = 20, 
        is_training: bool = True
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, StandardScaler]:
        """Membuat 3D tensor sequences (samples, sequence_length, features) tanpa data leakage."""
        clean_df = df_features.dropna(subset=cls.FEATURE_COLS).copy()
        if is_training:
            clean_df = clean_df.dropna(subset=["target_next_return", "target_next_direction"])

        raw_features = clean_df[cls.FEATURE_COLS].values
        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(raw_features)

        X, y_reg, y_clf = [], [], []
        target_returns = clean_df["target_next_return"].values if is_training else None
        target_directions = clean_df["target_next_direction"].values if is_training else None

        for i in range(len(scaled_features) - sequence_length + (1 if not is_training else 0)):
            X.append(scaled_features[i : i + sequence_length])
            if is_training:
                y_reg.append(target_returns[i + sequence_length - 1])
                y_clf.append(target_directions[i + sequence_length - 1])

        X_arr = np.array(X, dtype=np.float32)
        y_reg_arr = np.array(y_reg, dtype=np.float32) if is_training else np.array([])
        y_clf_arr = np.array(y_clf, dtype=np.int64) if is_training else np.array([])

        return X_arr, y_reg_arr, y_clf_arr, scaler
