import requests

def send_to_opa(s, j):
    url = 'http://localhost:8181/v1/data/{}'.format(s)
    r = requests.put(url, json=j)
    return r
