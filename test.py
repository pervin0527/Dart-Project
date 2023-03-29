import io
import requests
import zipfile
import xml.etree.ElementTree as ET

def read_api_key():
    with open("./API_KEY.txt", "r") as f:
        api_key = f.read()

    return api_key

crtfc_key = read_api_key()
api = "https://opendart.fss.or.kr/api/corpCode.xml"
res = requests.get(api, params={"crtfc_key" : crtfc_key})
print(res.status_code)
zfile = zipfile.ZipFile(io.BytesIO(res.content))
fin = zfile.open(zfile.namelist()[0]) ## CORPCODE.xml type -> list
root = ET.fromstring(fin.read().decode("utf-8"))

for child in root:
    corp_name = child.find("corp_name").text.strip()
    print(type(corp_name), corp_name)

    break