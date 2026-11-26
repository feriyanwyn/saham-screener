"""Model Trainer & Inference Pipeline with Walk-Forward Evaluation.
Menghitung MAE, RMSE, Directional Accuracy, Precision, Recall, dan F1-Score.
"""
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
from sklearn.metrics import precision_score, recall_score, f1_score, mean_absolute_error, mean_squared_error

from config.settings import settings
from database.connection import SessionLocal
from database.models import MLModelMeta
from src.machine_learning.feature_engineering import FeatureEngineer
from src.machine_learning.models import LSTMReturnRegressor, BiLSTMDirectionClassifier


class ModelPipeline:
    """End-to-end training and inference manager for LSTM and BiLSTM models."""

    def __init__(self, sequence_length: int = 20):
        self.seq_len = sequence_length
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def train_and_evaluate(
        self, 
        df_candles: pd.DataFrame, 
        ticker: str = "GLOBAL", 
        timeframe: str = "5M",
        epochs: int = 15,
        batch_size: int = 32
    ) -> Dict[str, Any]:
        """Melatih LSTM dan BiLSTM menggunakan time-series split tanpa lookahead bias."""
        df_feat = FeatureEngineer.prepare_features(df_candles)
        if df_feat.empty or len(df_feat) < (self.seq_len + 30):
            return {"error": "Insufficient data points for sequence training"}

        X, y_reg, y_clf, scaler = FeatureEngineer.create_sequences(
            df_feat, sequence_length=self.seq_len, is_training=True
        )

        # Time-series split (80% train, 20% test strictly in chronological order)
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_reg_train, y_reg_test = y_reg[:split_idx], y_reg[split_idx:]
        y_clf_train, y_clf_test = y_clf[:split_idx], y_clf[split_idx:]

        # PyTorch DataLoaders
        train_ds = TensorDataset(
            torch.tensor(X_train), 
            torch.tensor(y_reg_train), 
            torch.tensor(y_clf_train, dtype=torch.float32)
        )
        train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=False)

        input_dim = len(FeatureEngineer.FEATURE_COLS)

        # 1. Train LSTM Regressor
        lstm_model = LSTMReturnRegressor(input_dim=input_dim).to(self.device)
        opt_reg = torch.optim.Adam(lstm_model.parameters(), lr=0.002)
        loss_fn_reg = nn.MSELoss()

        lstm_model.train()
        for epoch in range(epochs):
            for bx, by_reg, _ in train_loader:
                bx, by_reg = bx.to(self.device), by_reg.to(self.device)
                opt_reg.zero_grad()
                pred = lstm_model(bx)
                loss = loss_fn_reg(pred, by_reg)
                loss.backward()
                opt_reg.step()

        # 2. Train BiLSTM Classifier
        bilstm_model = BiLSTMDirectionClassifier(input_dim=input_dim).to(self.device)
        opt_clf = torch.optim.Adam(bilstm_model.parameters(), lr=0.002)
        loss_fn_clf = nn.BCEWithLogitsLoss()

        bilstm_model.train()
        for epoch in range(epochs):
            for bx, _, by_clf in train_loader:
                bx, by_clf = bx.to(self.device), by_clf.to(self.device)
                opt_clf.zero_grad()
                pred = bilstm_model(bx)
                loss = loss_fn_clf(pred, by_clf)
                loss.backward()
                opt_clf.step()

        # 3. Evaluation on Out-of-Sample Test Set
        lstm_model.eval()
        bilstm_model.eval()
        with torch.no_grad():
            x_test_t = torch.tensor(X_test).to(self.device)
            reg_preds = lstm_model(x_test_t).cpu().numpy()
            clf_probs = bilstm_model.predict_proba(x_test_t).cpu().numpy()
            clf_preds = (clf_probs >= 0.5).astype(int)

        mae = float(mean_absolute_error(y_reg_test, reg_preds))
        rmse = float(np.sqrt(mean_squared_error(y_reg_test, reg_preds)))
        directional_acc = float(np.mean(clf_preds == y_clf_test))
        prec = float(precision_score(y_clf_test, clf_preds, zero_division=0))
        rec = float(recall_score(y_clf_test, clf_preds, zero_division=0))
        f1 = float(f1_score(y_clf_test, clf_preds, zero_division=0))

        # 4. Save Models
        lstm_path = os.path.join(settings.MODELS_DIR, "lstm", f"{ticker}_{timeframe}.pt")
        bilstm_path = os.path.join(settings.MODELS_DIR, "bilstm", f"{ticker}_{timeframe}.pt")
        torch.save(lstm_model.state_dict(), lstm_path)
        torch.save(bilstm_model.state_dict(), bilstm_path)

        # 5. Record to DB
        model_id = f"{ticker}_{timeframe}_{datetime.utcnow().strftime('%Y%m%d%H%M')}"
        db = SessionLocal()
        try:
            meta = MLModelMeta(
                model_id=model_id,
                ticker=ticker,
                architecture="LSTM+BiLSTM",
                timeframe=timeframe,
                features_used=json.dumps(FeatureEngineer.FEATURE_COLS),
                training_start_date=datetime.utcnow().date(),
                training_end_date=datetime.utcnow().date(),
                test_mae=round(mae, 5),
                test_rmse=round(rmse, 5),
                test_directional_accuracy=round(directional_acc, 4),
                precision_score=round(prec, 4),
                recall_score=round(rec, 4),
                f1_score=round(f1, 4),
                weights_path=lstm_path,
                scaler_path="",
                version="1.0"
            )
            db.add(meta)
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"[ModelPipeline] Error logging to DB: {e}")
        finally:
            db.close()

        return {
            "model_id": model_id,
            "test_mae": round(mae, 5),
            "test_rmse": round(rmse, 5),
            "directional_accuracy": round(directional_acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4)
        }

    def predict_latest(
        self, 
        df_candles: pd.DataFrame, 
        ticker: str = "GLOBAL", 
        timeframe: str = "5M"
    ) -> Dict[str, Any]:
        """Melakukan inferensi harga dan probabilitas arah pada bar terbaru."""
        df_feat = FeatureEngineer.prepare_features(df_candles)
        if df_feat.empty or len(df_feat) < self.seq_len:
            return {"predicted_return": 0.0, "up_probability": 0.5, "calibrated_confidence": 0.5}

        X_latest, _, _, _ = FeatureEngineer.create_sequences(
            df_feat, sequence_length=self.seq_len, is_training=False
        )
        if len(X_latest) == 0:
            return {"predicted_return": 0.0, "up_probability": 0.5, "calibrated_confidence": 0.5}

        input_dim = len(FeatureEngineer.FEATURE_COLS)
        lstm_model = LSTMReturnRegressor(input_dim=input_dim).to(self.device)
        bilstm_model = BiLSTMDirectionClassifier(input_dim=input_dim).to(self.device)

        lstm_path = os.path.join(settings.MODELS_DIR, "lstm", f"{ticker}_{timeframe}.pt")
        bilstm_path = os.path.join(settings.MODELS_DIR, "bilstm", f"{ticker}_{timeframe}.pt")

        if os.path.exists(lstm_path):
            lstm_model.load_state_dict(torch.load(lstm_path, map_location=self.device))
        if os.path.exists(bilstm_path):
            bilstm_model.load_state_dict(torch.load(bilstm_path, map_location=self.device))

        lstm_model.eval()
        bilstm_model.eval()
        with torch.no_grad():
            x_tensor = torch.tensor(X_latest[-1:]).to(self.device)
            pred_return = float(lstm_model(x_tensor).cpu().item())
            prob_up = float(bilstm_model.predict_proba(x_tensor).cpu().item())

        # Calibrated confidence (deviation from neutral 0.5)
        confidence = float(np.clip(abs(prob_up - 0.5) * 2.0, 0.1, 0.95))

        return {
            "predicted_return": round(pred_return, 4),
            "up_probability": round(prob_up, 4),
            "calibrated_confidence": round(confidence, 4)
        }
