import pandas as pd

def run_forecast_analysis():
    forecast = pd.read_json("forecast_output.json")
    events = pd.read_csv("events.csv")
    sentiment = pd.read_csv("sentiment.csv")

    forecast['ds'] = pd.to_datetime(forecast['ds'])
    events['date'] = pd.to_datetime(events['date'])
    sentiment['date'] = pd.to_datetime(sentiment['date'])

    forecast['rolling_yhat'] = forecast['yhat'].rolling(window=30, min_periods=1).mean()
    sentiment['rolling_score'] = sentiment['sentiment_score'].rolling(window=7, min_periods=1).mean()

    if 'y' in forecast.columns:
        forecast['residual'] = forecast['y'] - forecast['yhat']

    events_count = events.groupby('date').size().reset_index(name='event_count')

    merged = pd.merge(forecast[['ds', 'yhat']], sentiment[['date', 'sentiment_score']], left_on='ds', right_on='date', how='left')
    merged = pd.merge(merged, events_count, left_on='ds', right_on='date', how='left').fillna(0)

    # Prepare dict to return all needed data for plots
    return {
        "forecast": forecast.fillna('').to_dict(orient="records"),
        "events": events.fillna('').to_dict(orient="records"),
        "sentiment": sentiment.fillna('').to_dict(orient="records"),
        "events_count": events_count.fillna('').to_dict(orient="records"),
        "merged": merged.fillna('').to_dict(orient="records")
    }
