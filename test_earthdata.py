import requests

url = "https://data.gesdisc.earthdata.nasa.gov/data/GPM_L3/GPM_3IMERGDF.07/2024/01/3B-DAY.MS.MRG.3IMERG.20240101-S000000-E235959.V07B.nc4"

r = requests.get(url)

print("Status:", r.status_code)
print("Content-Type:", r.headers.get("Content-Type"))
print("Size:", len(r.content))

if r.status_code == 200:
    print("SUCCESS - Earthdata authentication works!")
else:
    print(r.text[:500])