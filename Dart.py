import io
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
    def __init__(self, crtfc_key):
        # self.key_path = "./API_KEY.txt"
        # self.crtfc_key = self.read_api_key()
        self.crtfc_key = crtfc_key
        
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

        results = []
        for i in range(1, boundary + 1):
            params={"crtfc_key" : self.crtfc_key,
                    "corp_code" : corp_code, 
                    "bsns_year" : str(tmp_year - i),
                    "reprt_code" : str(11011),
                    "fs_div" : "CFS"}
        
            res = requests.get(APIS[2]["단일회사 전체 재무제표"], params=params)
            json_dict = json.loads(res.text)
            dataset = json_dict["list"]
            
            for data in dataset:
                current_year = data["thstrm_nm"] ## 당기
                account_name = data["account_nm"] ## 계정명
                current_amount = data["thstrm_amount"] ## 당기금액
                bsns_year = data["bsns_year"]

                if account_name in target_list:
                    results.append({"기수" : current_year, "사업연도" : bsns_year, "계정과목" : account_name, "금액" : format(int(current_amount[:-6]), ",")})

        df = pd.DataFrame(results)
        df.to_csv("./results.csv", index=False, columns=["기수", "사업연도", "계정과목", "금액"], encoding="utf-8-sig")

            
# dart = Dart()
# founded_data = dart.get_corp_info("삼성전자")
# print(founded_data, "\n")

# targets = ["매출액", "매출원가", "매출총이익", "판매비와관리비", "영업이익", "영업이익(손실)"]
# dart.get_financial_data(founded_data["corp_code"], targets, 5)