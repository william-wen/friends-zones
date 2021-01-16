import datetime
from time import mktime
import re
import configparser
import requests

config = configparser.ConfigParser()
config.read('config.ini')
api_key = config['googleapi']["API_KEY"]

place_api_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
direction_api_url = "https://maps.googleapis.com/maps/api/directions/json"

travel_modes = ["DRIVING", "WALKING", "BICYCLING", "TRANSIT"]
regex_hours = r"\d+ hours"
regex_mins = r"\d+ mins"

    
def get_filtered_object(lat: int, lng: int, obj: dict, arrival_time: int):
    if obj["business_status"] != "OPERATIONAL":
        return False
    if "opening_hours" not in obj:
        return False
    if obj["opening_hours"]["open_now"] == False:
        return False
    
    travel_info = []
    destination = obj["place_id"]

    for travel_mode in travel_modes:
        params = {
            "mode": travel_mode,
            "origin": f"{lat},{lng}",
            "destination": f"place_id:{destination}",
            "arrival_time": int(arrival_time),
            "key": api_key
        }
        response = requests.get(direction_api_url, params=params).json()
        
        if response["routes"]:
            travel_time = response["routes"][0]["legs"][0]["duration"]["text"]

            hours = re.findall(regex_hours, travel_time)
            mins = re.findall(regex_mins, travel_time)

            hours = hours[0] if hours else 0
            mins = mins[0] if mins else 0
            
            travel_info.append({travel_mode: travel_time})

    if travel_info:
        obj["travel_info"] = travel_info
        return obj
    
    return False


def get_recommended_locations(
    lat: int, 
    lng: int, 
    interests: list, 
    end_time: datetime.datetime, 
    max_budget: int,
    min_budget: int
):
    params = {
        "location": f"{lat},{lng}",
        "rankby": "distance",
        "maxprice": max_budget,
        "minprice": min_budget,
        "key": api_key,
    }
    
    arrival_time = end_time - datetime.timedelta(minutes=30) #hardcoded assuming spending 30 min/destination
    arrival_time = mktime(arrival_time.timetuple())

    chosen_locations = []

    for interest in interests:
        params["keyword"] = interest
        response = requests.get(place_api_url, params=params)
        data = response.json()

        for obj in data["results"]:
            obj = get_filtered_object(lat, lng, obj, arrival_time)
            if obj:
                chosen_locations.append(obj)

    return chosen_locations


lat = -33.8670522
lng = 151.1957362
interests = ["restaurant", "cruise"]
end_time = datetime.datetime.strptime("2020-01-17 10:00", "%Y-%m-%d %H:%M")
max_budget = 4
min_budget = 0

print(get_recommended_locations(lat, lng, interests, end_time, max_budget, min_budget))
# print(get_api_results(f"{lat},{lng}"))
