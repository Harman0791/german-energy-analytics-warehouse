import os
import numpy as np
import pandas as pd
import sqlalchemy as sa
from dotenv import load_dotenv
from prophet import Prophet
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing

load_dotenv()

HORIZON = 30  # days held back for testing
COUNTRIES = {"germany": "avg_germany", "france": "avg_france", "spain": "avg_spain"}


def get_engine():
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    db = os.getenv("POSTGRES_DB")
    host = os.getenv("POSTGRES_HOST")
    port = os.getenv("POSTGRES_PORT")
    return sa.create_engine(f"postgresql://{user}:{password}@{host}:{port}/{db}")


# ---------- Models: each takes the training series, returns `h` predictions ----------

def forecast_prophet(train, h):
    df = pd.DataFrame({"ds": train.index, "y": train.values})
    model = Prophet(daily_seasonality=False, weekly_seasonality=True, yearly_seasonality=True)
    model.fit(df)
    future = model.make_future_dataframe(periods=h, include_history=False)
    return model.predict(future)["yhat"].values


def forecast_arima(train, h):
    return ARIMA(train.values, order=(5, 1, 2)).fit().forecast(h)


def forecast_holt_winters(train, h):
    model = ExponentialSmoothing(train.values, trend="add", seasonal="add", seasonal_periods=7)
    return model.fit().forecast(h)


def forecast_seasonal_naive(train, h):
    # Baseline: repeat the last 7 days
    return np.resize(train.values[-7:], h)


MODELS = {
    "prophet": forecast_prophet,
    "arima": forecast_arima,
    "holt_winters": forecast_holt_winters,
    "seasonal_naive": forecast_seasonal_naive,
}


# ---------- Metrics ----------

def calc_metrics(actual, pred):
    error = actual - pred
    return {
        "mae": np.mean(np.abs(error)),
        "rmse": np.sqrt(np.mean(error ** 2)),
        "mape": np.mean(np.abs(error / actual)) * 100,
    }


# ---------- Backtest ----------

def main():
    engine = get_engine()
    df = pd.read_sql(
        "SELECT date, avg_germany, avg_france, avg_spain FROM daily_average_prices ORDER BY date",
        engine,
        parse_dates=["date"],
    ).set_index("date")

    # Fail fast: need at least a year of training data plus the test window
    if len(df) < 365 + HORIZON:
        raise ValueError(f"Only {len(df)} days of data - not enough for a backtest.")

    train, test = df.iloc[:-HORIZON], df.iloc[-HORIZON:]
    print(f"Train: {train.index.min().date()} to {train.index.max().date()} ({len(train)} days)")
    print(f"Test:  {test.index.min().date()} to {test.index.max().date()} ({len(test)} days)")

    results = []
    for country, col in COUNTRIES.items():
        for model_name, forecast_fn in MODELS.items():
            pred = forecast_fn(train[col], HORIZON)

            # Fail fast: never save a broken result
            if len(pred) != HORIZON or np.isnan(pred).any():
                raise ValueError(f"{model_name} returned invalid predictions for {country}.")

            results.append({
                "country": country,
                "model": model_name,
                **calc_metrics(test[col].values, pred),
                "test_start": test.index.min().date(),
                "test_end": test.index.max().date(),
            })
            print(f"{country:8} {model_name:15} done")

    out = pd.DataFrame(results)
    out.to_sql("model_evaluation", engine, if_exists="replace", index=False)

    print("\nMAE (EUR/MWh) - lower is better:")
    print(out.pivot(index="model", columns="country", values="mae").round(2))


if __name__ == "__main__":
    main()