import io
import json
import zipfile
import requests
import pandas as pd
import xml.etree.ElementTree as ET


class Dart:
    def __init__(self):
        self.API_KEY = self.get_key()
        self.targets = self.basic_processing()

        self.URLS = {"고유번호" : "https://opendart.fss.or.kr/api/corpCode.xml",
                     "단일회사 전체 재무제표" : "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json",
                     "공시서류원본" : "https://opendart.fss.or.kr/api/document.xml"}
        
        self.name_to_code = {"1분기보고서" : "11013",
                             "반기보고서" : "11012",
                             "3분기보고서" : "11014",
                             "사업보고서" : "11011"}
        
        self.search_unique_number()
        self.get_financial_document()

        
    def get_key(self):
        with open("./API_KEY.txt", "r") as f:
            api_key = f.read()

        return api_key


    def basic_processing(self):
        df = pd.read_csv("./company_list.csv")
        rows_all_filled = list(df.notnull().all(axis=1))

        targets = []
        for idx, row in df.iterrows():
            if rows_all_filled[idx] != False:
                targets.append({"company_name" : row[0],
                                "years" : row[1],
                                "report_types" : row[2],
                                "bs_types" :row[3]})

        for target in targets:
            for idx, (key, value) in enumerate(target.items()):
                if idx > 0:
                    value = value.split(',')
                    target[key] = value
        
        return targets


    def send_request(self, request_name, parameters):
        ## Send_request
        response = requests.get(self.URLS[request_name], params=parameters)

        ## Open data
        zfile = zipfile.ZipFile(io.BytesIO(response.content))
        data = zfile.open(zfile.namelist()[0]) ## CORPCODE.xml type -> list
        data = ET.fromstring(data.read().decode("utf-8"))

        return data


    def search_unique_number(self):
        parameters = {"crtfc_key" : self.API_KEY}
        response_data = self.send_request("고유번호", parameters)

        for target in self.targets:
            for data in response_data:
                corp_name = data.find("corp_name").text.strip()
                
                target_name = target["company_name"]
                if corp_name == target_name:
                    corp_code = data.find("corp_code").text.strip()
                    stock_code = data.find("stock_code").text.strip()
                    modify_date = data.find("modify_date").text.strip()
                    
                    target.update({"corp_name" : corp_name, 
                                   "corp_code" : corp_code,
                                   "stock_code" : stock_code, 
                                   "latest modified date" : modify_date})        
        print(self.targets)
        

    def get_financial_document(self):
        for target in self.targets:
            for year in target["years"]:
                for report in target["report_types"]:
                    for bs_type in target["bs_types"]:
                        parameters = {"crtfc_key" : self.API_KEY,
                                      "corp_code" : target["corp_code"],
                                      "bsns_year" : str(year),
                                      "reprt_code" : self.name_to_code[report],
                                      "fs_div" : bs_type.upper()}
                        
                        ## TODO 이 부분 수정 필요. 접수번호 rcept_no 가져오고, 공시서류원본 가져오기.
                        response_data = self.send_request("단일회사 전체 재무제표", parameters)
                        print(response_data)