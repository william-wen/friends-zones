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
maps_url = "https://www.google.com/maps/search/?api=1&query="

travel_modes = ["driving", "walking", "bicycling", "transit"]
regex_hours = r"(?P<hours>\d+) hours"
regex_mins = r"(?P<minutes>\d+) mins"

    
def get_filtered_object(lat: int, lng: int, obj: dict, end_time: datetime.datetime):
    if obj["business_status"] != "OPERATIONAL":
        return False
    if "opening_hours" not in obj:
        return False
    if obj["opening_hours"]["open_now"] == False:
        return False
    
    travel_info = []
    destination = obj["place_id"]
    distance_found = False

    for travel_mode in travel_modes:
        params = {
            "mode": travel_mode,
            "origin": f"{lat},{lng}",
            "destination": f"place_id:{destination}",
            "key": api_key
        }
        response = requests.get(direction_api_url, params=params).json()
        
        if response["routes"]:
            travel_time = response["routes"][0]["legs"][0]["duration"]["text"]
            hours_match = re.search(regex_hours, travel_time)
            mins_match = re.search(regex_mins, travel_time)

            hours = int(hours_match.group("hours")) if hours_match else 0
            mins = int(mins_match.group("minutes")) if mins_match else 0

            now = datetime.datetime.now()
            time_left = end_time - datetime.timedelta(hours=hours, minutes=mins) - now

            if time_left >= datetime.timedelta(0):
                if not distance_found:
                    travel_distance = response["routes"][0]["legs"][0]["distance"]["text"]
                    travel_info.append({"TRAVEL_DISTANCE": travel_distance})
                    distance_found = True
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
        
    chosen_locations = []

    for interest in interests:
        params["keyword"] = interest
        response = requests.get(place_api_url, params=params)
        data = response.json()

        for obj in data["results"]:
            obj = get_filtered_object(lat, lng, obj, end_time)

            if obj:
                location_info = {}
                coordinates = obj["geometry"]["location"]
                latitude = coordinates["lat"]
                longitude = coordinates["lng"]
                address = obj["vicinity"]

                location_info["name"] = obj["name"]
                location_info["latitude"] = latitude
                location_info["longitude"] = longitude
                location_info["address"] = address
                location_info["photo_reference"] = obj["photos"][0]["photo_reference"] #https://developers.google.com/places/web-service/photos
                location_info["price_level"] = obj["price_level"]
                location_info["rating"] = obj["rating"]
                location_info["types"] = obj["types"]
                location_info["user_ratings_total"] = obj["user_ratings_total"]
                location_info["travel_info"] = obj["travel_info"]
                location_info["google_maps_link"] = f"{maps_url}{address}"
                
                chosen_locations.append(location_info)

    return chosen_locations


# lat = 43.5556018 # Get from Yifei's part
# lng = -79.7241566 # Get from Yifei's part
# interests = ["restaurant"] # Get from Will's part
# end_time = datetime.datetime.strptime("2021-01-17 20:15", "%Y-%m-%d %H:%M") # Get from Will's part
# max_budget = 4 # Get from Will's part
# min_budget = 0 # Get from Will's part

# print(get_recommended_locations(lat, lng, interests, end_time, max_budget, min_budget))
