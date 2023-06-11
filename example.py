import io
import zipfile
import requests
import pandas as pd
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

def get_api_key():
    with open(API_FILE_PATH, "r") as f:
        api_key = f.read()

    return api_key

def input_processing():
    df = pd.read_csv(INPUT_FILE_PATH)
    remove_unfilled = list(df.notnull().all(axis=1))

    targets = []
    for idx, row in df.iterrows():
        if remove_unfilled[idx] != False:
            targets.append({"compnay_name" : str(row[0]),
                            "years" : str(row[1]),
                            "report_types" : str(row[2]),
                            "bs_types" : str(row[3]),
                            "subjects" : str(row[4])})
    for target in targets:
        for idx, (key, value) in enumerate(target.items()):
            if idx > 0:
                value = value.split(",")
                value = [s.strip() for s in value]
                target[key] = value
    return targets


if __name__ == "__main__":
    API_FILE_PATH = "./API_KEY.txt"
    INPUT_FILE_PATH = "./input.csv"
    OUTPUT_FILE_PATH = "./output.csv"
    URLS = ["https://opendart.fss.or.kr/api/corpCode.xml",
            "https://opendart.fss.or.kr/api/document.xml"]

    REPORT_TYPES = {"1분기보고서" : "11013",
                    "반기보고서" : "11012",
                    "3분기보고서" : "11014",
                    "사업보고서" : "11011"}
    
    api_key = get_api_key()
    inputs = input_processing()
    print(inputs)