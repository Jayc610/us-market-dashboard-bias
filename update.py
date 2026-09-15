import json
import numpy as np
import pandas as pd
import yfinance as yf


def update_market_data():
    # 抓取 10 年历史数据以支持胜率分桶与分位数
    df = yf.download("^GSPC", period="10y", interval="1d")

    # 兼容新旧版本 yfinance 的数据结构处理
    if isinstance(df.columns, pd.MultiIndex):
        close_series = df["Close"].iloc[:, 0]
    else:
        close_series = df["Close"]

    clean_df = pd.DataFrame({"Close": close_series}).dropna()

    clean_df["SMA_60"] = clean_df["Close"].rolling(60).mean()
    clean_df["SMA_200"] = clean_df["Close"].rolling(200).mean()

    clean_df["BIAS_60"] = np.log(clean_df["Close"] / clean_df["SMA_60"])
    clean_df["BIAS_200"] = np.log(clean_df["Close"] / clean_df["SMA_200"])

    # 计算未来收益率用于胜率分桶
    clean_df["Fwd_20d"] = clean_df["Close"].shift(-20) / clean_df["Close"] - 1
    clean_df["Fwd_60d"] = clean_df["Close"].shift(-60) / clean_df["Close"] - 1
    clean_df["Fwd_252d"] = clean_df["Close"].shift(-252) / clean_df["Close"] - 1

    clean_df = clean_df.dropna(subset=["BIAS_60", "BIAS_200"])

    curr_p = float(clean_df["Close"].iloc[-1])
    curr_b60 = float(clean_df["BIAS_60"].iloc[-1])
    curr_b200 = float(clean_df["BIAS_200"].iloc[-1])
    curr_date = clean_df.index[-1].strftime("%Y-%m-%d")

    # 历史分位数
    pct_60 = float((clean_df["BIAS_60"] <= curr_b60).mean() * 100)
    pct_200 = float((clean_df["BIAS_200"] <= curr_b200).mean() * 100)

    # 距临界值百分点
    dist_60_oversold = (-0.08 - curr_b60) * 100
    dist_60_overbought = (0.08 - curr_b60) * 100
    dist_200_oversold = (-0.15 - curr_b200) * 100
    dist_200_bubble = (0.16 - curr_b200) * 100

    # 200日偏离度 5% 步长历史分桶
    bucket_floor = float(np.floor(curr_b200 * 20) / 20.0)
    bucket_ceil = bucket_floor + 0.05
    bucket_df = clean_df[
        (clean_df["BIAS_200"] >= bucket_floor)
        & (clean_df["BIAS_200"] < bucket_ceil)
    ]

    valid_bucket = bucket_df.dropna(subset=["Fwd_20d"])
    win_20d = (
        float((valid_bucket["Fwd_20d"] > 0).mean() * 100)
        if len(valid_bucket) > 0
        else 0
    )
    win_60d = (
        float((valid_bucket["Fwd_60d"] > 0).mean() * 100)
        if len(valid_bucket) > 0
        else 0
    )
    win_1y = (
        float((valid_bucket["Fwd_252d"] > 0).mean() * 100)
        if len(valid_bucket) > 0
        else 0
    )

    # 提取近 120 日趋势图数据
    recent = clean_df.tail(120)
    history = []
    for date, row in recent.iterrows():
        history.append(
            {
                "date": date.strftime("%Y-%m-%d"),
                "bias_60": round(float(row["BIAS_60"]), 4),
                "bias_200": round(float(row["BIAS_200"]), 4),
            }
        )

    output = {
        "update_date": curr_date,
        "close": round(curr_p, 2),
        "bias_60": round(curr_b60, 4),
        "bias_200": round(curr_b200, 4),
        "pct_60": round(pct_60, 1),
        "pct_200": round(pct_200, 1),
        "dist_60_oversold": round(dist_60_oversold, 2),
        "dist_60_overbought": round(dist_60_overbought, 2),
        "dist_200_oversold": round(dist_200_oversold, 2),
        "dist_200_bubble": round(dist_200_bubble, 2),
        "bucket_range": f"{bucket_floor*100:+.0f}% ~ {bucket_ceil*100:+.0f}%",
        "sample_cnt": len(valid_bucket),
        "win_20d": round(win_20d, 1),
        "win_60d": round(win_60d, 1),
        "win_1y": round(win_1y, 1),
        "history": history,
    }

    with open("data.json", "w") as f:
        json.dump(output, f, indent=2)


if __name__ == "__main__":
    update_market_data()
