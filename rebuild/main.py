import pandas as pd
from Dart import Dart

def get_api_key():
    with open(API_FILE_PATH, "r") as f:
        api_key = f.read()

    return api_key

def preprocessing():
    df = pd.read_csv(INPUT_FILE_PATH)

    targets = []
    for idx, row in df.iterrows():
        info = {}
        for idx, data in enumerate(row):
            if pd.isna(data):
                row[idx] = None
            
            elif ',' in row[idx]:
                row[idx] = [x.strip() for x in data.split(',')]
            
            elif idx % 6 != 0:
                row[idx] = [data]

        info.update({"company_name" : row[0],
                     "years" : row[1],
                     "report_types" : row[2],
                     "bs_types" : row[3],
                     "fs_subjects" : row[4],
                     "comment_subjects" : row[5]})
        targets.append(info)

    return targets
    

if __name__ == "__main__":
    API_FILE_PATH = "./API_KEY.txt"
    INPUT_FILE_PATH = "./input.csv"
    
    api_key = get_api_key()
    targets = preprocessing()
    Dart(api_key, targets)
