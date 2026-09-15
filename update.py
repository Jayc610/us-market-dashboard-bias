import yfinance as yf
import pandas as pd
import numpy as np
import json

def update_market_data():
    sp500 = yf.download("^GSPC", period="2y")
    close = sp500["Close"]["^GSPC"] if isinstance(sp500.columns, pd.MultiIndex) else sp500["Close"]

    sma60 = close.rolling(60).mean()
    sma200 = close.rolling(200).mean()
    log_dev60 = np.log(close / sma60)
    log_dev200 = np.log(close / sma200)

    latest_price = float(close.iloc[-1])
    latest_ld60 = float(log_dev60.iloc[-1])
    latest_ld200 = float(log_dev200.iloc[-1])
    latest_date = sp500.index[-1].strftime("%Y-%m-%d")

    # 判定规则与历史概率统计
    if latest_ld200 > -0.08 and latest_ld60 < -0.0639:
        status, win_rate, color = "💡 触发【牛市回调抄底】", "60.0% (20日反弹胜率)", "text-green-400"
    elif latest_ld200 > 0.1414:
        status, win_rate, color = "⚠️ 触发【高位发散预警】", "56.4% (60日回撤概率)", "text-red-400"
    else:
        status, win_rate, color = "✅ 正常区间震荡", "44.7% (常态胜率)", "text-blue-400"

    history = []
    recent_df = pd.DataFrame({"price": close, "dev60": log_dev60, "dev200": log_dev200}).dropna().tail(120)
    for date, row in recent_df.iterrows():
        history.append({
            "date": date.strftime("%Y-%m-%d"),
            "price": round(float(row["price"]), 2),
            "dev60": round(float(row["dev60"]), 4),
            "dev200": round(float(row["dev200"]), 4)
        })

    data = {
        "updated_at": latest_date,
        "price": round(latest_price, 2),
        "dev60": round(latest_ld60, 4),
        "dev200": round(latest_ld200, 4),
        "status": status,
        "win_rate": win_rate,
        "color": color,
        "history": history
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    update_market_data()
