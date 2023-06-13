import io
import zipfile
import requests
import pandas as pd
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

URLS = ["https://opendart.fss.or.kr/api/corpCode.xml",
        "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.xml",
        "https://opendart.fss.or.kr/api/document.xml"]

REPORT_TYPES = {"1분기보고서" : "11013",
                "반기보고서" : "11012",
                "3분기보고서" : "11014",
                "사업보고서" : "11011"}

OUTPUT_DIR = "./output.xlsx"


class Dart:
    def __init__(self, api_key, targets):
        self.api_key = api_key
        self.targets = targets
        self.start_crawling()
        
    def start_crawling(self):
        print("크롤링을 시작합니다. \n")
        self.search_unique_number()
        self.search_financial_statements()
        self.search_comment_subjects()
        self.record()

    def show_targets(self):
        for target in self.targets:
            print(target)
        print()

    def send_request(self, url, parameters):
        ## Send_request
        response = requests.get(url, params=parameters)

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
        print("1단계 : 기업 코드를 찾습니다.")
        parameters = {"crtfc_key" : self.api_key}
        response_data = self.send_request(URLS[0], parameters)

        for target in self.targets:
            for data in response_data:
                corp_name = data.find("corp_name").text.strip()
                target_name = target["company_name"]
                
                if corp_name == target_name:
                    corp_code = data.find("corp_code").text.strip()
                    target.update({"corp_code" : corp_code})
                    break
        
            else:
                print(f"{target_name}에 대한 기업 코드를 찾지 못했습니다.")
        self.show_targets()

    def get_fs_subjects(self, fs_document, name, subjects):
        results = {}
        if subjects != None:
            for subject in subjects:
                for pages in fs_document.findall("list"):
                    is_founded = False
                    for idx, data in enumerate(pages):
                        try:
                            if subject in data.text:
                                is_founded = True
                                key = data.text
                                value = pages[idx + 3].text

                                if len(value) > 12 and value[-6:] == '000000':
                                    value = value[:-6]
                                results.update({key : format(int(value), ",")})
                                break
                        except:
                            pass
                        
                    if is_founded:
                        break
                else:
                    print(f"{name} - {subject} not found.")
            return results
        else:
            return None

    def search_financial_statements(self):
        print("2단계 : 보고서 코드와 연결재무제표 과목에 대한 값을 찾습니다.")
        for target in self.targets:
            rcept_numbers = []
            name = target["company_name"]
            corp_code = target["corp_code"]
            years = target["years"]
            reports = target["report_types"]
            bs_types = target["bs_types"]
            fs_subjects = target["fs_subjects"]

            result = []
            for year in years:
                for report in reports:
                    for bs_type in bs_types:
                        parameters = {"crtfc_key" : self.api_key,
                                      "corp_code" : corp_code,
                                      "bsns_year" : year,
                                      "fs_div" : bs_type.upper(),
                                      "reprt_code" : REPORT_TYPES[report]}
                        
                        fs = self.send_request(URLS[1], parameters)
                        subject_values = self.get_fs_subjects(fs, name, fs_subjects)
                        result.append(subject_values)

                        rcept_number = fs[2].find("rcept_no").text
                        rcept_numbers.append(rcept_number)

            target.update({"report_numbers" : rcept_numbers, "fs_subjects" : result})
        
        self.show_targets()


    def get_comment_subjects(self, fs, name, subjects):
        results = {}
        td_list = []
        if subjects != None:
            total_td = fs.select("tbody tr td")
            for idx, td in enumerate(total_td):
                td_list.append(td)

            for subject in subjects:
                is_founded = False
                for idx, td in enumerate(td_list):
                    if subject in td.text:
                        key = td.text
                        value = td_list[idx + 1].text
                        is_founded = True

                        results.update({key : value})
                        break

                if is_founded:
                    break
            
            else:
                print(f"{name} - {subject} not found.")
            return results
        else:
            return None
                

    def search_comment_subjects(self):
        print("3단계 : 연결재무제표 주석 과목에 대한 값을 찾습니다.")
        for target in self.targets:
            name = target["company_name"]
            subjects = target["comment_subjects"]

            result = []
            for rcept_no in target["report_numbers"]:
                parameters = {"crtfc_key" : self.api_key, "rcept_no" : rcept_no}
                data = self.send_request(URLS[2], parameters)
                fs = BeautifulSoup(data, features="html.parser")
                subject_values = self.get_comment_subjects(fs, name, subjects)
                if subject_values != None:
                    result.append(subject_values)
            target.update({"comment_subjects" : result})
        
        self.show_targets()

    def record(self):
        writer = pd.ExcelWriter(OUTPUT_DIR)

        for entry in self.targets:
            company_name = entry['company_name']
            years = entry['years']
            fs_subjects = entry['fs_subjects']
            comment_subjects = entry['comment_subjects']
            
            data = {"company" : company_name}
            for idx, year in enumerate(years):
                if len(fs_subjects) == 0 or len(comment_subjects) == 0:
                    pass
                else:
                    subjects = fs_subjects[idx].update(comment_subjects[idx])

                    for 
