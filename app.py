from flask import Flask, render_template
import yfinance as yf
import pandas as pd
import numpy as np
from rgf.sklearn import RGFRegressor
from sklearn.metrics import mean_absolute_percentage_error
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="rgf.utils")

app = Flask(__name__)

def safe_float(val):
    """Force any input (Series, Array, or Scalar) into a standard float."""
    try:
        if isinstance(val, (pd.Series, np.ndarray)):
            return float(val.flatten()[0])
        return float(val)
    except:
        return 0.0

def get_market_data(symbol, name):
    # Initialize variables - Ensure 4 variables get 4 values
    current_val, current_vix, vix_pct_change = 0.0, 0.0, 0.0
    prediction, accuracy_score, pct_change = 0.0, 0.0, 0.0
    
    # CORRECTED LINE BELOW (added one more 0.0)
    yesterday_pred, actual_today, diff, error_pct = 0.0, 0.0, 0.0, 0.0
    
    history_list = []
    trend, color = "Neutral", "secondary"

    try:
        # 1. Download Data
        data_raw = yf.download(symbol, period="5y", interval="1d", progress=False)
        dxy_raw = yf.download("DX-Y.NYB", period="5y", interval="1d", progress=False)
        vix_raw = yf.download("^VIX", period="5y", interval="1d", progress=False)
        
        # 2. Flatten Multi-Index Columns
        for df_raw in [data_raw, dxy_raw, vix_raw]:
            if isinstance(df_raw.columns, pd.MultiIndex):
                df_raw.columns = df_raw.columns.get_level_values(0)

        # 3. Build Dataset - Using .squeeze() then .iloc if needed
        # This prevents the "too many indices" error by ensuring we have a 1D Series
        def clean_series(df):
            s = df['Close']
            if isinstance(s, pd.DataFrame):
                s = s.iloc[:, 0]
            return s.squeeze()

        price_series = clean_series(data_raw)
        usd_series = clean_series(dxy_raw)
        vix_series = clean_series(vix_raw)

        df = pd.DataFrame({
            'Price': price_series,
            'USD': usd_series,
            'VIX': vix_series
        }).dropna()
        
        # 4. Feature Engineering
        df['Returns'] = df['Price'].pct_change()
        df['MA5'] = df['Price'].rolling(window=5).mean()
        df['Target'] = df['Price'].shift(-1)
        train_df = df.dropna().copy()

# 5. RGF Model Training (Restoring to 97% Precision Settings)
        X = train_df[['Price', 'USD', 'VIX', 'Returns', 'MA5']].values.astype('float32')
        y = train_df['Target'].values.astype('float32')
        
        # Reverting to the original "Greedy" settings
        model = RGFRegressor(
            max_leaf=1000,       # Restored: Allows the AI to see more detailed patterns
            algorithm="RGF", 
            l2=0.1              # Restored: Lower penalty for complexity
        )
        model.fit(X, y)

        # 6. Predictions
        # Fix: Ensure last_row is exactly (1, 5) shape
        last_row = X[-1].reshape(1, -1)
        prediction = safe_float(model.predict(last_row))
        
        # Current Price Logic
        ticker = yf.Ticker(symbol)
        try:
            live_price = ticker.fast_info.last_price
            current_val = safe_float(live_price)
        except:
            current_val = safe_float(train_df['Price'].iloc[-1])

        # VIX Logic
        current_vix = safe_float(df['VIX'].iloc[-1])
        yesterday_vix = safe_float(df['VIX'].iloc[-2])
        vix_pct_change = ((current_vix - yesterday_vix) / yesterday_vix) * 100 if yesterday_vix != 0 else 0
        
        # 7. Accuracy (30-day window)
        y_pred_30 = model.predict(X[-30:])
        mape = mean_absolute_percentage_error(y[-30:], y_pred_30)
        accuracy_score = round(100 - (mape * 100), 2)

        # 8. Historical Validation
        yesterday_features = X[-2].reshape(1, -1)
        yesterday_pred = safe_float(model.predict(yesterday_features))
        actual_today = current_val
        diff = actual_today - yesterday_pred
        error_pct = (abs(diff) / actual_today) * 100 if actual_today != 0 else 0
        
        # UI Strings
        pct_change = ((prediction - current_val) / current_val) * 100 if current_val != 0 else 0
        trend = "UP" if prediction > current_val else "DOWN"
        color = "success" if trend == "UP" else "danger"
        history_list = train_df['Price'].tail(30).tolist()

    except Exception as e:
        print(f"CRITICAL ERROR on {name}: {e}")

    return {
        "name": name, "symbol": symbol, "current": round(current_val, 2),
        "vix": round(current_vix, 2), "vix_pct": round(vix_pct_change, 2),
        "pred": round(prediction, 2), "pct": round(pct_change, 2),
        "accuracy": accuracy_score, "history": history_list,
        "trend": trend, "color": color, "hist_pred": round(yesterday_pred, 2),
        "hist_actual": round(actual_today, 2), "hist_diff": round(diff, 2),
        "hist_error": round(error_pct, 2)
    }

@app.route('/')
def home():
    gold = get_market_data("GC=F", "Gold")
    silver = get_market_data("SI=F", "Silver")
    iau = get_market_data("IAU", "Gold ETF")
    slv = get_market_data("SLV", "Silver ETF")
    return render_template('index.html', gold=gold, silver=silver, iau=iau, slv=slv)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

warnings.filterwarnings("ignore", category=UserWarning, module="rgf.utils")

app = Flask(__name__)

def safe_float(val):
    """Force any input (Series, Array, or Scalar) into a standard float."""
    try:
        if isinstance(val, (pd.Series, np.ndarray)):
            return float(val.flatten()[0])
        return float(val)
    except:
        return 0.0

def get_market_data(symbol, name):
    # Initialize variables - Ensure 4 variables get 4 values
    current_val, current_vix, vix_pct_change = 0.0, 0.0, 0.0
    prediction, accuracy_score, pct_change = 0.0, 0.0, 0.0
    
    # CORRECTED LINE BELOW (added one more 0.0)
    yesterday_pred, actual_today, diff, error_pct = 0.0, 0.0, 0.0, 0.0
    
    history_list = []
    trend, color = "Neutral", "secondary"

    try:
        # 1. Download Data
        data_raw = yf.download(symbol, period="5y", interval="1d", progress=False)
        dxy_raw = yf.download("DX-Y.NYB", period="5y", interval="1d", progress=False)
        vix_raw = yf.download("^VIX", period="5y", interval="1d", progress=False)
        
        # 2. Flatten Multi-Index Columns
        for df_raw in [data_raw, dxy_raw, vix_raw]:
            if isinstance(df_raw.columns, pd.MultiIndex):
                df_raw.columns = df_raw.columns.get_level_values(0)

        # 3. Build Dataset - Using .squeeze() then .iloc if needed
        # This prevents the "too many indices" error by ensuring we have a 1D Series
        def clean_series(df):
            s = df['Close']
            if isinstance(s, pd.DataFrame):
                s = s.iloc[:, 0]
            return s.squeeze()

        price_series = clean_series(data_raw)
        usd_series = clean_series(dxy_raw)
        vix_series = clean_series(vix_raw)

        df = pd.DataFrame({
            'Price': price_series,
            'USD': usd_series,
            'VIX': vix_series
        }).dropna()
        
        # 4. Feature Engineering
        df['Returns'] = df['Price'].pct_change()
        df['MA5'] = df['Price'].rolling(window=5).mean()
        df['Target'] = df['Price'].shift(-1)
        train_df = df.dropna().copy()

# 5. RGF Model Training (Restoring to 97% Precision Settings)
        X = train_df[['Price', 'USD', 'VIX', 'Returns', 'MA5']].values.astype('float32')
        y = train_df['Target'].values.astype('float32')
        
        # Reverting to the original "Greedy" settings
        model = RGFRegressor(
            max_leaf=1000,       # Restored: Allows the AI to see more detailed patterns
            algorithm="RGF", 
            l2=0.1              # Restored: Lower penalty for complexity
        )
        model.fit(X, y)

        # 6. Predictions
        # Fix: Ensure last_row is exactly (1, 5) shape
        last_row = X[-1].reshape(1, -1)
        prediction = safe_float(model.predict(last_row))
        
        # Current Price Logic
        ticker = yf.Ticker(symbol)
        try:
            live_price = ticker.fast_info.last_price
            current_val = safe_float(live_price)
        except:
            current_val = safe_float(train_df['Price'].iloc[-1])

        # VIX Logic
        current_vix = safe_float(df['VIX'].iloc[-1])
        yesterday_vix = safe_float(df['VIX'].iloc[-2])
        vix_pct_change = ((current_vix - yesterday_vix) / yesterday_vix) * 100 if yesterday_vix != 0 else 0
        
        # 7. Accuracy (30-day window)
        y_pred_30 = model.predict(X[-30:])
        mape = mean_absolute_percentage_error(y[-30:], y_pred_30)
        accuracy_score = round(100 - (mape * 100), 2)

        # 8. Historical Validation
        yesterday_features = X[-2].reshape(1, -1)
        yesterday_pred = safe_float(model.predict(yesterday_features))
        actual_today = current_val
        diff = actual_today - yesterday_pred
        error_pct = (abs(diff) / actual_today) * 100 if actual_today != 0 else 0
        
        # UI Strings
        pct_change = ((prediction - current_val) / current_val) * 100 if current_val != 0 else 0
        trend = "UP" if prediction > current_val else "DOWN"
        color = "success" if trend == "UP" else "danger"
        history_list = train_df['Price'].tail(30).tolist()

    except Exception as e:
        print(f"CRITICAL ERROR on {name}: {e}")

    return {
        "name": name, "symbol": symbol, "current": round(current_val, 2),
        "vix": round(current_vix, 2), "vix_pct": round(vix_pct_change, 2),
        "pred": round(prediction, 2), "pct": round(pct_change, 2),
        "accuracy": accuracy_score, "history": history_list,
        "trend": trend, "color": color, "hist_pred": round(yesterday_pred, 2),
        "hist_actual": round(actual_today, 2), "hist_diff": round(diff, 2),
        "hist_error": round(error_pct, 2)
    }
@app.route('/')
def home():
    gold = get_market_data("GC=F", "Gold")
    silver = get_market_data("SI=F", "Silver")
    iau = get_market_data("IAU", "Gold ETF")
    slv = get_market_data("SLV", "Silver ETF")
    return render_template('index.html', gold=gold, silver=silver, iau=iau, slv=slv)

if __name__ == '__main__':
    # Using 0.0.0.0 allows Render to 'see' the app externally
    app.run(host='0.0.0.0', port=5000, debug=True)