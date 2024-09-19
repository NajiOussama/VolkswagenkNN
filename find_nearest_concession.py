from sklearn.neighbors import NearestNeighbors
import numpy as np
import requests
from requests.auth import HTTPBasicAuth
from geopy.geocoders import Nominatim
import certifi
import ssl 

USERNAME = "232fd97ad7ef45d7a54e1f341f9e9ed8"
PASSWORD = "51A7F33F80CD483d8f12BEC230637840"
crt_file = "Diago.crt.txt"
pem_file = "Diago-private.pem"
#resp = requests.get("https://api.non-prod.volkswagengroup.fr/tools/qa/leads/v2/dealers/export", params={"page": 2, "per_page": 10, "brand": "Volkswagen"}, auth=HTTPBasicAuth(USERNAME, PASSWORD), cert=(crt_file, pem_file))

concessions_exploitables = []
concessions_non_exploitables = []
for page in range(1, 58):
    resp = requests.get(
        "https://api.non-prod.volkswagengroup.fr/tools/qa/leads/v2/dealers/export", 
        params={"page": page, "per_page": 10, "brand": "Volkswagen"},
        auth=HTTPBasicAuth(USERNAME, PASSWORD),
        cert=(crt_file, pem_file)
    )

    # Dynamically determine the number of items on the current page
    data = resp.json().get('data', [])
    for i, dealer in enumerate(data):
        try:
            conc = dealer['address'][0]
            if 'longitude' in conc and 'latitude' in conc:
                d = {k: conc[k] for k in ['line','city', 'country','postalCode', 'longitude', 'latitude']}
                concessions_exploitables.append(d)
            else:
                d = {k: conc[k] for k in ['line','city','country', 'postalCode']}
                concessions_non_exploitables.append(d)
        except (IndexError, KeyError) as e:
            print(f"Error at page {page}, item {i}: {e}")

def get_lat_lon(zip_code, country="France"):
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    geolocator = Nominatim(user_agent="geoapi", ssl_context=ssl_context)
    location = geolocator.geocode(f"{zip_code}, {country}")
    
    if location:
        return (location.latitude, location.longitude)
    else:
        return None

concessions = concessions_exploitables

def find_nearest_concession(client_zip_code):
    client_coords = get_lat_lon(client_zip_code)
    if client_coords is None:
        return "Invalid ZIP code or location not found."

    # Extract concession coordinates (latitude, longitude)
    concession_coords = np.array([[float(conc['latitude']), float(conc['longitude'])] for conc in concessions])
    # Step 3: Use KNN to find the nearest concession
    knn = NearestNeighbors(n_neighbors=1, algorithm='ball_tree')  # You can also use 'auto', 'kd_tree', or 'brute'
    knn.fit(concession_coords)

    # Find the nearest concession to the client's coordinates
    distance, index = knn.kneighbors([client_coords])

    # Return the nearest concession
    nearest_concession = concessions[index[0][0]]
    return (nearest_concession, distance[0][0])

print(find_nearest_concession("Versailles"))