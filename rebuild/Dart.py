import io
import zipfile
import requests
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
        print("Start Crawling \n")
        self.search_unique_number()
        self.search_financial_statements()

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
        print("STEP1 : Searching corp code...")
        parameters = {"crtfc_key" : self.api_key}
        response_data = self.send_request(URLS[0], parameters)

        for target in self.targets:
            for data in response_data:
                corp_name = data.find("corp_name").text.strip()
                
                if corp_name == target["company_name"]:
                    corp_code = data.find("corp_code").text.strip()
                    target.update({"corp_code" : corp_code})
        
        print("Done!!!")
        self.show_targets()

    def get_fs_subjects(self, fs_document, subjects):
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

        return results

    def search_financial_statements(self):
        print("STEP2 : Searching FS Subjects...")
        for target in self.targets:
            rcept_numbers = []
            corp_code = target["corp_code"]
            years = target["years"]
            reports = target["report_types"]
            bs_types = target["bs_types"]
            fs_subjects = target["fs_subjects"]

            for year in years:
                for report in reports:
                    for bs_type in bs_types:
                        parameters = {"crtfc_key" : self.api_key,
                                      "corp_code" : corp_code,
                                      "bsns_year" : year,
                                      "fs_div" : bs_type.upper(),
                                      "reprt_code" : REPORT_TYPES[report]}
                        
                        fs = self.send_request(URLS[1], parameters)
                        subject_values = self.get_fs_subjects(fs, fs_subjects)
                        rcept_number = fs[2].find("rcept_no").text
                        rcept_numbers.append(rcept_number)

            target.update({"report_numbers" : rcept_numbers, "fs_subjects" : subject_values})
        
        print("Done!!!")
        self.show_targets()

    def search_subjects(self):
        pass
