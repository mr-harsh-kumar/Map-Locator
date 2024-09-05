from django.shortcuts import render
from django.http import HttpResponse
import folium
import geocoder
from .models import map_locator_table
from .db_connection import db

from datetime import datetime

# Create your views here.

def map_locator(request):
    if request.method == "POST":
        address = request.POST.get('address')
        
        location = geocoder.osm(address)
        print(f"Location: {location}")
    
        if location.ok:
            latitude = location.lat
            longitude = location.lng
            country = location.country
            state = location.state
            details = f"Country: {country}  <-----> \nState: {state}"
        
            m = folium.Map(location=[latitude, longitude], zoom_start=6)
            folium.Marker([latitude, longitude], 
                          tooltip="Click for more",
                          popup=folium.Popup(details, max_width=900, max_height=500)).add_to(m)

            m = m._repr_html_()  # Convert the map to HTML

            # Function to get the next sequence value
            def get_next_sequence(name):
                sequence_doc = db['map_locator_table'].find_one_and_update(
                    {'id': name},
                    {'$inc': {'seq': 1}},
                    return_document=True,
                    upsert=True
                )
                return sequence_doc['seq']
            
            def insert_location():
                search = {
                        "id": get_next_sequence('map_locator_table'),
                        "Location" : address,
                        "Time" : datetime.now()
                        }
               
                map_locator_table.insert_one(search)
                
            insert_location()
            context = {'m': m}
        else:
            # Handle the case where the geocoder could not find the location
            latitude, longitude = 20.5937, 78.9629  # Default to the center of India
            country = "India (default location)"
        
            no_place = "There is no such place or Server Error.\n Try again after few minutes"
            
            context = {'no_place': no_place}

        return render(request, 'location.html', context)
    else:
        latitude, longitude = 20.5937, 78.9629  # Default to the center of India
        country = "India (default location)"
        m = folium.Map(location=[latitude, longitude], zoom_start=6)
        folium.Marker([latitude, longitude], 
                        tooltip="Click for more",
                        popup=folium.Popup(country, max_width=900, max_height=500)).add_to(m)

        no_place = "search any place"
        
        context = {'m':m,
                   'no_place': no_place}
        return render(request, 'location.html', context)


def analysis(request):

    # Retrieve all documents
    searches = list(map_locator_table.find({}))

    # Aggregation pipeline for maximum location count
    max_pipeline = [
        {
            "$group": {
                "_id": "$Location",
                "count": {"$sum": 1}
            }
        },
        {
            "$sort": {"count": -1}
        },
        {
            "$limit": 1
        }
    ]

    max_result = list(map_locator_table.aggregate(max_pipeline))
    max_location, max_count = None, 0
    
    if max_result:
        max_location = max_result[0]['_id']
        max_count = max_result[0]['count']
    
    
    # Aggregation pipeline for minimum location count
    min_pipeline = [
        {
            "$group": {
                "_id": "$Location",
                "count": {"$sum": 1}
            }
        },
        {
            "$sort": {"count": 1}
        },
        {
            "$limit": 1
        }
    ]

    # Execute the pipelines
    min_result = list(map_locator_table.aggregate(min_pipeline))
    
    # Initialize max and min locations and counts
 
    min_location, min_count = None, 0
    
    if min_result:
        min_location = min_result[0]['_id']
        min_count = min_result[0]['count']
    
    # last = map_locator_table.find_one(sort=[('_id',-1)]).get('Location')
    last = map_locator_table.find_one(sort=[('_id', -1)])

    if last:
      last_location = last.get('Location')
    else:
       last_location = None

    print(f"last: {last}")
    print(f"last_location: {last_location}")
    # print(last)
    
    first = map_locator_table.find_one(sort=[('id', 1)])

    if first:
      first_location = first.get('Location')
    else:
       first_location = None

    print(f"first: {first}")
    print(f"first_location: {first_location}")
# last_document = collection.find_one(sort=[('_id', -1)])
    context = {
        'searches': searches,
        'max_location': max_location,
        'max_count': max_count,
        'min_location': min_location,
        'min_count': min_count,
        'last_location' : last_location,
        'first_location' : first_location,
    }

    return render(request, 'analysis.html', context)