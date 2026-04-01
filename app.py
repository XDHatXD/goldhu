from flask import Flask, render_template
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_percentage_error

app = Flask(__name__)

def get_market_data(symbol, name):
    # Default values to prevent UnboundLocalError
    current_val = 0.0
    prediction = 0.0
    accuracy_score = 0.0
    pct_change = 0.0
    history_list = []
    trend = "Neutral"
    color = "secondary"

    try:
        # 1. Fetch Data
        ticker = yf.Ticker(symbol)
        live_price = ticker.fast_info.last_price
        
        data_raw = yf.download(symbol, period="5y", interval="1d", progress=False)
        dxy_raw = yf.download("DX-Y.NYB", period="5y", interval="1d", progress=False)
        
        # Clean Multi-Index columns for 2026 yfinance structure
        if isinstance(data_raw.columns, pd.MultiIndex):
            data_raw.columns = data_raw.columns.get_level_values(0)
        if isinstance(dxy_raw.columns, pd.MultiIndex):
            dxy_raw.columns = dxy_raw.columns.get_level_values(0)

        # 2. Build Dataset
        df = pd.DataFrame({
            'Price': data_raw['Close'].squeeze(),
            'USD': dxy_raw['Close'].squeeze()
        }).dropna()
        
        # Feature Engineering
        df['Returns'] = df['Price'].pct_change()
        df['MA5'] = df['Price'].rolling(window=5).mean()
        df['Target'] = df['Price'].shift(-1)
        train_df = df.dropna()

        # 3. AI Model Training
        X = train_df[['Price', 'USD', 'Returns', 'MA5']]
        y = train_df['Target']
        
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)

        # 4. Predictions & Accuracy
        last_row = X.tail(1)
        prediction = float(model.predict(last_row)[0])
        current_val = float(live_price) if live_price else float(last_row['Price'].values[0])
        
        # Calculate Accuracy (MAPE) on last 30 days
        y_true = train_df['Target'].tail(30)
        y_pred_test = model.predict(X.tail(30))
        mape = mean_absolute_percentage_error(y_true, y_pred_test)
        accuracy_score = round(100 - (mape * 100), 2)

        # 5. Trend & Percentages
        pct_change = ((prediction - current_val) / current_val) * 100
        trend = "UP" if prediction > current_val else "DOWN"
        color = "success" if trend == "UP" else "danger"
        history_list = data_raw['Close'].tail(30).tolist()

    except Exception as e:
        print(f"Error processing {name}: {e}")

    return {
        "name": name,
        "symbol": symbol,
        "current": round(current_val, 2),
        "pred": round(prediction, 2),
        "pct": round(pct_change, 2),
        "accuracy": accuracy_score,
        "history": history_list,
        "trend": trend,
        "color": color
    }

@app.route('/')
def home():
    gold = get_market_data("GC=F", "Gold")
    silver = get_market_data("SI=F", "Silver")
    return render_template('index.html', gold=gold, silver=silver)

if __name__ == '__main__':
    app.run(debug=True)