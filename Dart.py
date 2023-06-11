import io
import zipfile
import requests
import pandas as pd
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

class Dart:
    def __init__(self):
        self.API_KEY = self.get_key()
        self.targets = self.basic_processing()
        self.total_fs = []
        self.final_result = []

        self.URLS = {"고유번호" : "https://opendart.fss.or.kr/api/corpCode.xml",
                     "단일회사 전체 재무제표" : "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.xml",
                     "공시서류원본" : "https://opendart.fss.or.kr/api/document.xml"}
        
        self.name_to_code = {"1분기보고서" : "11013",
                             "반기보고서" : "11012",
                             "3분기보고서" : "11014",
                             "사업보고서" : "11011"}

    def get_key(self):
        with open("./API_KEY.txt", "r") as f:
            api_key = f.read()

        return api_key


    def basic_processing(self):
        df = pd.read_csv("./input.csv")
        rows_all_filled = list(df.notnull().all(axis=1))

        targets = []
        for idx, row in df.iterrows():
            if rows_all_filled[idx] != False:
                targets.append({"company_name" : row[0],
                                "years" : row[1],
                                "report_types" : row[2],
                                "bs_types" :row[3],
                                "subjects" : row[4]})

        for target in targets:
            for idx, (key, value) in enumerate(target.items()):
                if idx > 0 and isinstance(value, str):
                    value = value.split(',')
                    value = [s.strip() for s in value]
                    target[key] = value
                
                elif idx > 0 and isinstance(value, int):
                    target[key] = [str(value)]
        
        return targets


    def send_request(self, request_name, parameters):
        ## Send_request
        response = requests.get(self.URLS[request_name], params=parameters)

        ## Open data
        try:
            data = zipfile.ZipFile(io.BytesIO(response.content))
            data = data.open(data.namelist()[0])
            data = ET.fromstring(data.read().decode("utf-8"))

        except zipfile.BadZipFile:
            data = ET.fromstring(response.text)

        except UnicodeDecodeError:
            zf = zipfile.ZipFile(io.BytesIO(response.content))
            info_list = zf.infolist()
            fnames = sorted([info.filename for info in info_list])
            xml_data = zf.read(fnames[0])
            data = xml_data.decode("cp949")

        except ET.ParseError:
            data = zipfile.ZipFile(io.BytesIO(response.content))
            data = data.open(data.namelist()[0]).read().decode("utf-8")
    
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
        
        
    def get_financial_document(self):
        for target in self.targets:
            rcept_numbers = [] 
            for year in target["years"]:
                for report in target["report_types"]:
                    for bs_type in target["bs_types"]:
                        parameters = {"crtfc_key" : self.API_KEY,
                                      "corp_code" : target["corp_code"],
                                      "bsns_year" : str(year),
                                      "reprt_code" : self.name_to_code[report.strip()],
                                      "fs_div" : bs_type.upper()}
                        
                        # print(target["corp_code"], year, self.name_to_code[report.strip()], bs_type.upper())
                        data = self.send_request("단일회사 전체 재무제표", parameters)
                        rcept_number = data[2].find("rcept_no").text
                        rcept_numbers.append(rcept_number)
                        
                        parameters = {"crtfc_key" : self.API_KEY, "rcept_no" : rcept_number}         
                        financial_statement = self.send_request("공시서류원본", parameters)               

                        self.total_fs.append({"company" : target["company_name"],
                                                "year" : year,
                                                "report" : report,
                                                "bs_type" : bs_type,
                                                "subjects" : target["subjects"],
                                                "content" : financial_statement})

    def search1(self, document, target):
        p_list = []
        total_tbody = document.find_all("tbody")
        for tbody in total_tbody:
            total_tr = tbody.find_all("tr")
        
            for tr in total_tr:
                total_td = tr.find_all("td")

                for td in total_td:
                    total_p = td.find_all("p")

                    for p in total_p:
                        p_list.append(p)

        for p in p_list:
            if target in p.text:
                target_value = p_list.index(p) + 1
                break
        else:
            return False
        
        return p.text, p_list[target_value].text


    def search2(self, document, target):
        td_list = []
        total_tbody = document.select("tbody")
        for tbody in total_tbody:
            total_tr = tbody.find_all("tr")
        
            for tr in total_tr:
                total_td = tr.find_all("td")

                for td in total_td:
                    td_list.append(td)

        for td in td_list:
            if target in td.text:
                target_value = td_list.index(td) + 1
                break
        else:
            return False
        
        return td.text, td_list[target_value].text
    

    def make_final_result(self):
        for fs in self.total_fs:
            fs_soup = BeautifulSoup(fs["content"], features="html.parser")
            company, year, report, bs_type = fs["company"], fs["year"], fs["report"], fs["bs_type"]
            subjects = fs["subjects"]

            search_result = {}
            for subject in subjects:
                result = self.search1(fs_soup, subject)

                if result:
                    search_result.update({result[0] : result[1]})
                else:
                    result = self.search2(fs_soup, subject)
                    if result:
                        search_result.update({result[0] : result[1]})
                
            self.final_result.append({"company_name" : company,
                                      "years" : year,
                                      "report_name" :report,
                                      "bs type" : bs_type,
                                      "subjects" : search_result})


    def write_final_result(self):
        company_data = {}
        for entry in self.final_result:
            company_name = entry['company_name']
            if company_name in company_data:
                company_data[company_name][entry['years']] = entry['subjects']
            else:
                company_data[company_name] = {entry['years']: entry['subjects']}

        writer = pd.ExcelWriter('output.xlsx')
        for company_name, years_data in company_data.items():
            df = pd.DataFrame(years_data)
            # df = df.transpose()
            df.to_excel(writer, sheet_name=company_name, index_label='Years')

        writer.close()