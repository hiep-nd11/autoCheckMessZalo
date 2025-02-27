import re
data_input = "129- A Nam 0947019588"
import requests

def split_zalo_name(name):
    timeout=30
    url = "http://127.0.0.1:5000/update_sheet"
    if name != []:
        lines = name.strip().split("\n")
        result = []
        for line in lines:
            match = re.match(r"^\d+", line.strip())
            if match:
                result.append(match.group())
        
        if result == []:
            #Truong hop gia tri truyen vao khong co chu so o dau
            data = lines
            print(data)
            response = requests.post(url, json=data, timeout=timeout)
            return 0
        else:
            #Truong hop gia tri truyen vao hop le
            
            return f"Sari đc {result[0].zfill(6)}"
    else:
        # truong hop o bi trong, khong co gia tri truyen vao
        return 0

a = split_zalo_name(data_input)

print(a) 


# def split_zalo_name(name):
#     lines = name.strip().split("\n")
#     result = []
#     for line in lines:
#         match = re.match(r"^\d+", line.strip())
#         if match:
#             result.append(match.group())
#     if result == []:
#         return 0
#     else:
#         return result[0]

# def get_zalo_name():
#     creds = None
#     if os.path.exists("token.json"):
#         creds = Credentials.from_authorized_user_file("token.json", SCOPES)
#     # Nếu chưa có thông tin đăng nhập hoặc token không hợp lệ
#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             creds.refresh(Request())
#         else:
#             flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
#             creds = flow.run_local_server(port=0)
#         # Lưu thông tin đăng nhập vào file token.json
#         with open("token.json", "w") as token:
#             token.write(creds.to_json())

#     try:
#         service = build("sheets", "v4", credentials=creds)
#         sheet = service.spreadsheets()
#         result = sheet.values().get(spreadsheetId=SHEET_THONG_TIN, range=RANGE_THONGTIN_TENZALO).execute()

#         values = result.get('values', []) 

#         for row in values:
#             if row != []:
#                 # print(split_zalo_name(row[0]))
#                 a = split_zalo_name(row[0])
#                 if a == 0:
#                     print("ten khong hop le")
#                     # return 444
#                 else:
#                     print(f"Sari đc {a.zfill(6)}")

#             else:
#                 print("Khong co ten nhom")

#     except TimeoutError:
#         return {"error": "Operation timed out after 10 seconds"}
#     except HttpError as err:
#         return {"error": f"An error occurred: {err}"}