import io
import re
import json
import requests
import zipfile
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import date

APIS = [
    {"고유번호" : "https://opendart.fss.or.kr/api/corpCode.xml"},
    {"상장기업 재무정보" : "https://opendart.fss.or.kr/api/fnlttSinglAcnt.json"},
    {"단일회사 전체 재무제표" : "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json"}
]

class Dart:
    def __init__(self, crtfc_key, save_path, exclude_pattern=None):
        # self.key_path = "./API_KEY.txt"
        # self.crtfc_key = self.read_api_key()
        self.crtfc_key = crtfc_key
        self.exclude_pattern = exclude_pattern
        self.save_path = save_path
        
    def read_api_key(self):
        with open(self.key_path, "r") as f:
            api_key = f.read()

        return api_key
    
    def open_request(self, res_raw):
        zfile = zipfile.ZipFile(io.BytesIO(res_raw.content))
        fin = zfile.open(zfile.namelist()[0]) ## CORPCODE.xml type -> list
        root = ET.fromstring(fin.read().decode("utf-8"))

        return root

    def search_company(self, root, target_name):
        for child in root:
            corp_name = child.find("corp_name").text.strip()
            
            if corp_name == target_name:
                corp_code = child.find("corp_code").text.strip()
                stock_code = child.find("stock_code").text.strip()
                modify_date = child.find("modify_date").text.strip()
                
                return {"corp_name" : corp_name, 
                        "corp_code" : corp_code,
                        "stock_code" : stock_code, 
                        "latest modified date" : modify_date}
        
        return "Sorry, Nothing Found."

    def get_corp_info(self, target_name):
        res = requests.get(APIS[0]["고유번호"], params={"crtfc_key" : self.crtfc_key})
        root = self.open_request(res)
        data = self.search_company(root, target_name)

        return data
    
    def get_financial_data(self, corp_code, target_list, boundary):
        tmp_date = date.today()
        tmp_year = tmp_date.year

        result_set = {}
        for i in range(boundary, 0, -1):
            params={"crtfc_key" : self.crtfc_key,
                    "corp_code" : corp_code, 
                    "bsns_year" : str(tmp_year - i),
                    "reprt_code" : str(11011),
                    "fs_div" : "CFS"}
        
            res = requests.get(APIS[2]["단일회사 전체 재무제표"], params=params)
            json_dict = json.loads(res.text)
            dataset = json_dict["list"]
            
            subjects = []
            subject_values = []
            for data in dataset:
                for target in target_list:
                    account_name = data["account_nm"]
                    if re.search(target, account_name) and not re.search(self.exclude_pattern, account_name):
                        subjects.append(account_name)
                        current_amount = format(int(data["thstrm_amount"][:-6]), ",")
                        subject_values.append(current_amount)

            result_set.update({str(tmp_year - i) : subject_values})
        
        df = pd.DataFrame(result_set, index=subjects)
        df.to_csv(self.save_path, encoding="utf-8-sig")