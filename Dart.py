import io
import requests
import zipfile
import xml.etree.ElementTree as ET

class Dart:
    def __init__(self):
        self.key_path = "./API_KEY.txt"

    def read_api_key(self):
        with open(self.key_path, "r") as f:
            api_key = f.read()

        return api_key
    
    def search_company(self, root, target_name):
        for child in root:
            corp_name = child.find("corp_name").text.strip()
            
            if corp_name == target_name:
                corp_code = child.find("corp_code").text.strip()
                stock_code = child.find("stock_code").text.strip()
                modify_date = child.find("modify_date").text.strip()
                
                return {"corp_name" : corp_name, "corp_code" : corp_code, "stock_code" : stock_code, "latest modified date" : modify_date}
        
        return "Sorry, Nothing Found."

    def get_corp_info(self, target_name):
        crtfc_key = self.read_api_key()
        api = "https://opendart.fss.or.kr/api/corpCode.xml"
        res = requests.get(api, params={"crtfc_key" : crtfc_key})
        print(res.status_code)
        zfile = zipfile.ZipFile(io.BytesIO(res.content))
        fin = zfile.open(zfile.namelist()[0]) ## CORPCODE.xml type -> list
        root = ET.fromstring(fin.read().decode("utf-8"))

        data = self.search_company(root, target_name)
        return data


dart = Dart()
founded_data = dart.get_corp_info("삼성전자")
print(founded_data)