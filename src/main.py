from fastapi import FastAPI
import requests
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import csv
#why fastapi - met with cors error so to debug it had to
airlines={}
airports={}
routes={}
def load_airports():
    with open ('airports.dat',newline="",encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        for x in reader:
            if(x[4]=="\\N"):
                continue
            airports[x[4]]={"Name":x[1],"City":x[2],"Country":x[3],"IATA":x[4],"ICAO":x[5],"Lat":x[6],"Lng":x[7]}

def load_routes():
    global routes
    with open('routes.dat', newline="",encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        for x in reader:
            if x[0] == "\\N" or x[2] == "\\N" or x[4] == "\\N":
                continue
            routes.setdefault(x[0], []).append({"src": x[2], "dst": x[4]})
def load_airlines():
    global airlines
    with open('airlines.dat', newline="",encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        for x in reader:
            if x[3] == "\\N" or x[4] == "\\N":
                continue
            airlines[x[4]] = x[3] 
        

def get_route(callsign):
    ICAOcode = callsign[:3]
    IATAcode = airlines.get(ICAOcode)
    if not IATAcode:
        return None
    route = routes.get(IATAcode)
    if not route:
        return None
    src = airports.get(route[0]["src"])
    dest = airports.get(route[0]["dst"])
    if not src or not dest:
        return None
    return {
        "src_airport": src.get("Name"),
        "src_country": src.get("Country"),
        "src_lat": src.get("Lat"),
        "src_lng": src.get("Lng"),
        "dst_airport": dest.get("Name"),
        "dst_country": dest.get("Country"),
    }

@asynccontextmanager
async def lifespan(app:FastAPI):
    load_airlines()
    load_airports()
    load_routes()
    yield  

app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:3000",
    "http://localhost",
    "http://localhost:8080",
    "http://192.168.0.3:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/")
async def main():
    return {"message": "Hello World"}

@app.get("/flights")
async def flights(lat:float,lng:float):
    headers = {
        "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0"
    }
    rectangle = [
    [lat - 1, lng - 1],
    [lat + 1, lng + 1]]
    resp = requests.get(f"https://opensky-network.org/api/states/all?lamin={lat-1}&lomin={lng-1}&lamax={lat+1}&lomax={lng+1}")
    resp.raise_for_status()
    data = resp.json()
    states = data.get("states") or []
    states = [s for s in states if s[5] is not None and s[6] is not None]
    states = sorted(states, key=lambda s: (s[6]-lat)**2 + (s[5]-lng)**2)
    states = states[:20]
    result = []
    for flight in states:
        callsign = flight[1].strip() if flight[1] else None
        route = get_route(callsign) if callsign else None
        result.append({
        "icao24": flight[0],
        "callsign": callsign,
        "lat": flight[6],
        "lng": flight[5],
        "altitude": flight[7],
        "velocity": flight[9],
        "heading": flight[10],
        "route": route
        })
    result = [f for f in result if f["route"] is not None]
    result = [f for f in result if f["route"]["src_country"] != f["route"]["dst_country"]]
    return result

