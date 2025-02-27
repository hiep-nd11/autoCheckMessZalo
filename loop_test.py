import requests

def read_data(cdt ,value):
    timeout=100
    # URL của Flask server
    url = "http://127.0.0.1:5000/update_sheet"
    
    data = {
        "cdt": cdt,
        "value": value
    }
    response = requests.post(url, json=data, timeout=timeout)

# cdt = "Sari đc 000005"
# value = "39 khâm thiên kín 201 nhé e"
# read_data(cdt, value)