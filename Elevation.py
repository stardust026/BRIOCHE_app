import requests

def get_elevation(coordinate_list):
    coordinate = '|'.join(','.join(map(str, coordinate)) for coordinate in coordinate_list)
    url = f'https://api.open-elevation.com/api/v1/lookup?locations={coordinate}'
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()['results']
        return data
    else:
        print("response failed, status code:", response.status_code)
        return None
         
    
def elevation_difference(coordinate_list):
    data = get_elevation(coordinate_list)
    if data is not None:
        elevation_list = [item.get('elevation', 0) for item in data]
        elevation_pairs = [elevation_list[i + 1] - elevation_list[i] for i in range(len(elevation_list) - 1)]
        return elevation_pairs
    # If data is None, set elevation_list None
    return None

    

