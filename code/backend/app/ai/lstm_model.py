from typing import Any
import json
import os
import joblib
import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.models import Sequential


class LSTMModel:

    def __init__(self, config: Any = None) -> Any:
        """
        Initialize LSTM model for financial prediction

        Parameters:
        -----------
        config : dict
            Configuration parameters for the model
        """
        self.config = {
            "sequence_length": 60,
            "prediction_horizon": 5,
            "features": ["close", "volume", "open", "high", "low"],
            "target": "close",
            "lstm_units": 50,
            "dropout_rate": 0.2,
            "dense_units": 25,
            "epochs": 50,
            "batch_size": 32,
            "validation_split": 0.2,
            "optimizer": "adam",
            "loss": "mean_squared_error",
            "metrics": ["mae"],
        }
        if config:
            self.config.update(config)
        self.model = None
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.feature_scalers = {}

    def _prepare_data(self, data: Any) -> Any:
        """
        Prepare data for LSTM model

        Parameters:
        -----------
        data : pandas.DataFrame
            Input data with features

        Returns:
        --------
        X : numpy.ndarray
            Input sequences
        y : numpy.ndarray
            Target values
        """
        scaled_features = {}
        for feature in self.config["features"]:
            scaler = MinMaxScaler(feature_range=(0, 1))
            scaled_features[feature] = scaler.fit_transform(
                data[feature].values.reshape(-1, 1)
            )
            self.feature_scalers[feature] = scaler
        target_scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_target = target_scaler.fit_transform(
            data[self.config["target"]].values.reshape(-1, 1)
        )
        self.feature_scalers["target"] = target_scaler
        X, y = ([], [])
        for i in range(
            len(data)
            - self.config["sequence_length"]
            - self.config["prediction_horizon"]
            + 1
        ):
            features = []
            for feature in self.config["features"]:
                features.append(
                    scaled_features[feature][i : i + self.config["sequence_length"]]
                )
            X.append(np.hstack(features))
            y.append(
                scaled_target[
                    i
                    + self.config["sequence_length"]
                    + self.config["prediction_horizon"]
                    - 1
                ]
            )
        return (np.array(X), np.array(y))

    def build_model(self, input_shape: Any) -> Any:
        """
        Build LSTM model

        Parameters:
        -----------
        input_shape : tuple
            Shape of input data (sequence_length, num_features)
        """
        model = Sequential()
        model.add(
            LSTM(
                units=self.config["lstm_units"],
                return_sequences=True,
                input_shape=input_shape,
            )
        )
        model.add(Dropout(self.config["dropout_rate"]))
        model.add(LSTM(units=self.config["lstm_units"], return_sequences=False))
        model.add(Dropout(self.config["dropout_rate"]))
        model.add(Dense(units=self.config["dense_units"], activation="relu"))
        model.add(Dense(units=1))
        model.compile(
            optimizer=self.config["optimizer"],
            loss=self.config["loss"],
            metrics=self.config["metrics"],
        )
        self.model = model
        return model

    def train(self, data: Any, verbose: Any = 1) -> Any:
        """
        Train LSTM model

        Parameters:
        -----------
        data : pandas.DataFrame
            Training data
        verbose : int
            Verbosity mode

        Returns:
        --------
        history : dict
            Training history
        """
        X, y = self._prepare_data(data)
        num_features = len(self.config["features"])
        X = X.reshape(X.shape[0], self.config["sequence_length"], num_features)
        if self.model is None:
            self.build_model((self.config["sequence_length"], num_features))
        history = self.model.fit(
            X,
            y,
            epochs=self.config["epochs"],
            batch_size=self.config["batch_size"],
            validation_split=self.config["validation_split"],
            verbose=verbose,
        )
        return history.history

    def predict(self, data: Any) -> Any:
        """
        Make predictions with trained model

        Parameters:
        -----------
        data : pandas.DataFrame
            Input data for prediction

        Returns:
        --------
        predictions : numpy.ndarray
            Predicted values (unscaled)
        """
        if self.model is None:
            raise ValueError("Model not trained yet. Call train() first.")
        X, _ = self._prepare_data(data)
        num_features = len(self.config["features"])
        X = X.reshape(X.shape[0], self.config["sequence_length"], num_features)
        scaled_predictions = self.model.predict(X)
        predictions = self.feature_scalers["target"].inverse_transform(
            scaled_predictions
        )
        return predictions

    def evaluate(self, data: Any) -> Any:
        """
        Evaluate model performance

        Parameters:
        -----------
        data : pandas.DataFrame
            Test data

        Returns:
        --------
        metrics : dict
            Evaluation metrics
        """
        X, y = self._prepare_data(data)
        num_features = len(self.config["features"])
        X = X.reshape(X.shape[0], self.config["sequence_length"], num_features)
        scaled_predictions = self.model.predict(X)
        predictions = self.feature_scalers["target"].inverse_transform(
            scaled_predictions
        )
        actual = self.feature_scalers["target"].inverse_transform(y)
        mse = mean_squared_error(actual, predictions)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(actual, predictions)
        r2 = r2_score(actual, predictions)
        metrics = {
            "mse": float(mse),
            "rmse": float(rmse),
            "mae": float(mae),
            "r2": float(r2),
        }
        return metrics

    def save(self, path: Any) -> Any:
        """
        Save model and scalers

        Parameters:
        -----------
        path : str
            Directory path to save model
        """
        os.makedirs(path, exist_ok=True)
        self.model.save(os.path.join(path, "lstm_model.h5"))
        for feature, scaler in self.feature_scalers.items():
            joblib.dump(scaler, os.path.join(path, f"scaler_{feature}.pkl"))
        with open(os.path.join(path, "config.json"), "w") as f:
            json.dump(self.config, f)

    @classmethod
    def load(cls: Any, path: Any) -> Any:
        """
        Load model and scalers

        Parameters:
        -----------
        path : str
            Directory path to load model from

        Returns:
        --------
        model : LSTMModel
            Loaded model
        """
        with open(os.path.join(path, "config.json"), "r") as f:
            config = json.load(f)
        instance = cls(config)
        instance.model = tf.keras.models.load_model(os.path.join(path, "lstm_model.h5"))
        for feature in instance.config["features"] + ["target"]:
            instance.feature_scalers[feature] = joblib.load(
                os.path.join(path, f"scaler_{feature}.pkl")
            )
        return instance


if __name__ == "__main__":
    dates = pd.date_range(start="2020-01-01", periods=1000, freq="D")
    data = pd.DataFrame(
        {
            "date": dates,
            "close": np.random.normal(100, 10, 1000).cumsum() + 1000,
            "volume": np.random.normal(1000000, 200000, 1000),
            "open": np.random.normal(100, 10, 1000).cumsum() + 1000,
            "high": np.random.normal(100, 10, 1000).cumsum() + 1010,
            "low": np.random.normal(100, 10, 1000).cumsum() + 990,
        }
    )
    train_data = data.iloc[:800]
    test_data = data.iloc[800 - 60 :]
    model = LSTMModel()
    history = model.train(train_data)
    metrics = model.evaluate(test_data)
    predictions = model.predict(test_data)
    model.save("lstm_model")
    loaded_model = LSTMModel.load("lstm_model")
    loaded_predictions = loaded_model.predict(test_data)
