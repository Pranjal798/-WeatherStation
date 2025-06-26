from uagents import Agent, Context, Model
from fastapi import FastAPI, Request
from pydantic import BaseModel
import threading
import uvicorn
from fastapi import Request, Form
from fastapi.responses import JSONResponse

# uAgent part
class WeatherData(Model):
    temperature: float
    humidity: float
    pressure: float

weather_agent = Agent(name="weather_station")

# Store the latest data
latest_data = {"temperature": None, "humidity": None, "pressure": None}

@weather_agent.on_message(model=WeatherData)
async def handle_request(ctx: Context, sender: str, msg: WeatherData):
    # This handles updates (optional if POST handles everything)
    latest_data.update(msg.dict())
    ctx.logger.info(f"Weather data updated by agent: {msg}")

@weather_agent.on_query(model=Model)
async def serve_current_weather(ctx: Context, sender: str, _):
    if all(latest_data.values()):
        await ctx.send(sender, WeatherData(**latest_data))
    else:
        ctx.logger.info("No weather data available yet.")

# FastAPI part
app = FastAPI()

@app.post("/weather")
async def receive_weather_ecowitt(
    tempf: float = Form(...),
    humidity: int = Form(...),
    baromrelin: float = Form(...)
):
    try:
        # Convert Fahrenheit to Celsius
        temp_c = (tempf - 32) * 5.0/9.0
        pressure = baromrelin * 33.8639  # inHg to hPa

        latest_data.update({
            "temperature": round(temp_c, 2),
            "humidity": humidity,
            "pressure": round(pressure, 2)
        })
        return JSONResponse(content={"status": "received", "data": latest_data})
    except Exception as e:
        return JSONResponse(status_code=400, content={"status": "error", "detail": str(e)})
from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    if all(latest_data.values()):
        return f"""
        <html>
            <head>
                <title>Live Weather Station</title>
                <meta http-equiv="refresh" content="30" />
                <style>
                    body {{ font-family: sans-serif; padding: 2em; background: #f0f0f0; }}
                    .card {{ background: white; padding: 1.5em; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); width: 300px; margin: auto; }}
                    h1 {{ font-size: 1.5em; margin-bottom: 1em; }}
                    p {{ font-size: 1.2em; }}
                </style>
            </head>
            <body>
                <div class="card">
                    <h1>Current Weather</h1>
                    <p>🌡️ Temperature: <b>{latest_data['temperature']}°C</b></p>
                    <p>💧 Humidity: <b>{latest_data['humidity']}%</b></p>
                    <p>🌬️ Pressure: <b>{latest_data['pressure']} hPa</b></p>
                    <small>🔄 Updates every 30 seconds</small>
                </div>
            </body>
        </html>
        """
    else:
        return """
        <html><body><h2>No data received yet.</h2></body></html>
        """
# Run both agent + FastAPI server
def run():
    threading.Thread(target=lambda: uvicorn.run(app, host="0.0.0.0", port=10000)).start()
    weather_agent.run()

if __name__ == "__main__":
    run()
