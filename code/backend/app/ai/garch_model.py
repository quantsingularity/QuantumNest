import json
import os
import numpy as np
import pandas as pd
from arch import arch_model
from core.logging import get_logger

logger = get_logger(__name__)


class GARCHModel:

    def __init__(self, config: Any = None) -> Any:
        """
        Initialize GARCH model for volatility forecasting

        Parameters:
        -----------
        config : dict
            Configuration parameters for the model
        """
        self.config = {
            "p": 1,
            "q": 1,
            "mean": "Constant",
            "vol": "GARCH",
            "dist": "normal",
            "horizon": 5,
            "window": 252,
        }
        if config:
            self.config.update(config)
        self.model = None
        self.result = None
        self.returns_scaler = None

    def _prepare_data(self, data: Any) -> Any:
        """
        Prepare data for GARCH model

        Parameters:
        -----------
        data : pandas.DataFrame or pandas.Series
            Price data

        Returns:
        --------
        returns : pandas.Series
            Return series
        """
        if isinstance(data, pd.DataFrame):
            if "close" in data.columns:
                prices = data["close"]
            elif "price" in data.columns:
                prices = data["price"]
            else:
                raise ValueError("DataFrame must contain 'close' or 'price' column")
        else:
            prices = data
        returns = 100 * prices.pct_change().dropna()
        return returns

    def build_model(self, returns: Any) -> Any:
        """
        Build GARCH model

        Parameters:
        -----------
        returns : pandas.Series
            Return series

        Returns:
        --------
        model : arch_model
            GARCH model
        """
        model = arch_model(
            returns,
            p=self.config["p"],
            q=self.config["q"],
            mean=self.config["mean"],
            vol=self.config["vol"],
            dist=self.config["dist"],
        )
        self.model = model
        return model

    def train(self, data: Any, update: Any = False, verbose: Any = 1) -> Any:
        """
        Train GARCH model

        Parameters:
        -----------
        data : pandas.DataFrame or pandas.Series
            Price data
        update : bool
            Whether to update existing model
        verbose : int
            Verbosity mode

        Returns:
        --------
        result : ARCHModelResult
            Training result
        """
        returns = self._prepare_data(data)
        if self.model is None or not update:
            self.build_model(returns)
        self.result = self.model.fit(disp="off" if verbose == 0 else "on")
        if verbose > 0:
            logger.info(self.result.summary())
        return self.result

    def forecast(self, horizon: Any = None, start: Any = None) -> Any:
        """
        Generate volatility forecast

        Parameters:
        -----------
        horizon : int
            Forecast horizon
        start : int or str
            Start index for forecast

        Returns:
        --------
        forecast : ARCHModelForecast
            Volatility forecast
        """
        if self.result is None:
            raise ValueError("Model not trained yet. Call train() first.")
        horizon = horizon or self.config["horizon"]
        forecast = self.result.forecast(horizon=horizon, start=start)
        return forecast

    def rolling_forecast(self, data: Any, window: Any = None) -> Any:
        """
        Generate rolling volatility forecasts

        Parameters:
        -----------
        data : pandas.DataFrame or pandas.Series
            Price data
        window : int
            Rolling window size

        Returns:
        --------
        forecasts : pandas.DataFrame
            Rolling volatility forecasts
        """
        returns = self._prepare_data(data)
        window = window or self.config["window"]
        horizon = self.config["horizon"]
        forecasts = []
        for i in range(window, len(returns)):
            train_returns = returns.iloc[i - window : i]
            model = arch_model(
                train_returns,
                p=self.config["p"],
                q=self.config["q"],
                mean=self.config["mean"],
                vol=self.config["vol"],
                dist=self.config["dist"],
            )
            result = model.fit(disp="off")
            forecast = result.forecast(horizon=horizon)
            forecast_variance = forecast.variance.iloc[-1].values
            forecast_volatility = np.sqrt(forecast_variance)
            forecasts.append(
                {
                    "date": returns.index[i],
                    "volatility_1d": forecast_volatility[0],
                    "volatility_5d": (
                        forecast_volatility[min(4, len(forecast_volatility) - 1)]
                        if horizon >= 5
                        else None
                    ),
                }
            )
        return pd.DataFrame(forecasts).set_index("date")

    def evaluate(self, data: Any) -> Any:
        """
        Evaluate model performance

        Parameters:
        -----------
        data : pandas.DataFrame or pandas.Series
            Test data

        Returns:
        --------
        metrics : dict
            Evaluation metrics
        """
        returns = self._prepare_data(data)
        if self.result is None:
            raise ValueError("Model not trained yet. Call train() first.")
        realized_vol = (
            returns.rolling(window=self.config["horizon"])
            .std()
            .shift(-self.config["horizon"])
        )
        forecast = self.forecast(horizon=self.config["horizon"])
        forecast_vol = np.sqrt(forecast.variance.iloc[-1].values[0])
        mse = np.mean((realized_vol.dropna() - forecast_vol) ** 2)
        rmse = np.sqrt(mse)
        mae = np.mean(np.abs(realized_vol.dropna() - forecast_vol))
        metrics = {"mse": float(mse), "rmse": float(rmse), "mae": float(mae)}
        return metrics

    def save(self, path: Any) -> Any:
        """
        Save model

        Parameters:
        -----------
        path : str
            Directory path to save model
        """
        if self.result is None:
            raise ValueError("Model not trained yet. Call train() first.")
        os.makedirs(path, exist_ok=True)
        model_params = {"config": self.config, "params": self.result.params.to_dict()}
        with open(os.path.join(path, "garch_model.json"), "w") as f:
            json.dump(model_params, f)

    @classmethod
    def load(cls: Any, path: Any) -> Any:
        """
        Load model

        Parameters:
        -----------
        path : str
            Directory path to load model from

        Returns:
        --------
        model : GARCHModel
            Loaded model
        """
        with open(os.path.join(path, "garch_model.json"), "r") as f:
            model_params = json.load(f)
        instance = cls(model_params["config"])
        dummy_returns = pd.Series(np.random.normal(0, 1, 100))
        instance.build_model(dummy_returns)
        return instance


if __name__ == "__main__":
    dates = pd.date_range(start="2020-01-01", periods=1000, freq="D")
    prices = 1000 + np.cumsum(np.random.normal(0, 20, 1000))
    data = pd.Series(prices, index=dates)
    train_data = data.iloc[:800]
    test_data = data.iloc[800:]
    model = GARCHModel()
    result = model.train(train_data)
    forecast = model.forecast()
    metrics = model.evaluate(test_data)
    rolling_forecasts = model.rolling_forecast(test_data, window=100)
    model.save("garch_model")
    loaded_model = GARCHModel.load("garch_model")
