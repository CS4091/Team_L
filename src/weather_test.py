import src.weather_util.weather as weather
# From the Linux CLI weather app https://fungi.yuggoth.org/weather/ 
import os


def ext_weather(air_code: str = "YOY") -> dict:
    print(os.getcwd())
    os.chdir("src/weather_util")
    wet = dict()
    
    try: 
        s = weather.get_uri(weather.guess(air_code,quiet=True)["metar"])
    except Exception as e:
        os.chdir("../..")
        return {"Wind": "No data", "Visibility": "No data", "Sky conditions": "No data", "Dew Point": "No data", "Relative Humidity": "No data", "Pressure (altimeter)": "No data"}
    for it in s.splitlines():
        if any([j in it for j in ["Wind", "Visibility", "Sky conditions", "Dew Point", "Relative Humidity", "Pressure (altimeter)"]]):
            a, b = it.split(":",maxsplit=1)
            wet.update({a:b})
    os.chdir("../..")
    return wet
    # Returns dict example: {'Wind': ' from the SSE (160 degrees) at 2 MPH (2 KT):0', 'Visibility': ' greater than 7 mile(s):0', 'Dew Point': ' 48 F (9 C)', 'Relative Humidity': ' 93%', 'Pressure (altimeter)': ' 30.15 in. Hg (1021 hPa)'}

def debug():
    print(ext_weather("LEBZ"))
    print(ext_weather("CRS"))
    print(ext_weather("CFR"))

# YOY, CRS