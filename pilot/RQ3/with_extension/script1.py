class WeatherStation:
    def __init__(self, forecasts):
        self.forecasts = forecasts

    def summarize_weather(self):
        print("Weekly Weather Forecast:")
        for day, forecast in self.forecasts.items():
            print(f"{day}: {forecast}")

def fetch_weather_data():
    return {
        "Monday": "Sunny, 24°C",
        "Tuesday": "Cloudy, 18°C",
        "Wednesday": "Rain, 15°C"
    }

def add_weather_forecast(forecasts, new_day, weather):
    forecasts[new_day] = weather
    return forecasts

def manage_weather():
    current_forecast = fetch_weather_data()
    extended_forecast = add_weather_forecast(current_forecast, "Thursday", "Thunderstorms, 19°C")
    station = WeatherStation(extended_forecast)
    station.summarize_weather()

def main():
    manage_weather()

main()
