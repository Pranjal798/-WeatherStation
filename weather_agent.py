from uagents import Agent, Context, Model
from fastapi import FastAPI, Request
from pydantic import BaseModel
import threading
import uvicorn

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
async def receive_weather(request: Request):
    body = await request.json()
    try:
        data = WeatherData(**body)
        latest_data.update(data.dict())
        return {"status": "received", "data": latest_data}
    except Exception as e:
        return {"status": "error", "details": str(e)}

# Run both agent + FastAPI server
def run():
    threading.Thread(target=lambda: uvicorn.run(app, host="0.0.0.0", port=10000)).start()
    weather_agent.run()

if __name__ == "__main__":
    run()
