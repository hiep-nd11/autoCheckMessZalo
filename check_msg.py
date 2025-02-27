from flask import Flask, request, jsonify
import os.path
import time
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import openai
import json
from datetime import datetime
import re
from id_speadsheet import choose_id_speadsheet
from rapidfuzz import process, fuzz
from difflib import SequenceMatcher
from dotenv import load_dotenv
import os

from fuzzywuzzy import fuzz
from fuzzywuzzy import process

load_dotenv()

app = Flask(__name__)

KKK = 0.9
openai.api_key = "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"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SCOPES = [os.getenv("SCOPES")]  
SHEET_TRONG_THIEU = os.getenv("SHEET_TRONG_THIEU")
SHEET_TONG_TRONG = os.getenv("SHEET_TONG_TRONG")
SHEET_THONG_TIN = os.getenv("SHEET_THONG_TIN")
RANGE_THONGTIN_TENZALO = os.getenv("RANGE_THONGTIN_TENZALO")
RANGE_CDT = os.getenv("RANGE_CDT")
RANGE_THONGTIN_LINKZALO = os.getenv("RANGE_THONGTIN_LINKZALO")
RANGE_THONGTIN_LINKCAPNHAT = os.getenv("RANGE_THONGTIN_LINKCAPNHAT")
RANGE_ADDR = os.getenv("RANGE_ADDR")
RANGE_PHONGTRONGTHIEU = os.getenv("RANGE_PHONGTRONGTHIEU")
RANGE_PHONGKHONGDIACHI = os.getenv("RANGE_PHONGKHONGDIACHI")




def insert_sheet_tong(sheet, cdt, gpt_address, gpt_room, gpt_status, gpt_cost):
    print("Phòng thiếu, chèn vào bảng phòng thiếu")
    # print("aaaaaaaaaaaaaaa", gpt_address, gpt_room, gpt_status, gpt_cost)
    range_name = RANGE_PHONGTRONGTHIEU
    current_data = sheet.values().get(
        spreadsheetId = SHEET_TRONG_THIEU,
        range = range_name
    ).execute().get('values', [])
    start_index = len(current_data)
    current_time = datetime.now()
    formatted_date = get_date_string(current_time)
    # print("kkkkkkkkkkkkkk")
    if gpt_room != []:
        for p in gpt_room:
            # print(p)
            index_p = gpt_room.index(p)
            cost_value = gpt_cost[index_p]

            new_value = [[start_index, cdt, gpt_address, p, gpt_status, cost_value,formatted_date]]
            body = {'values': new_value}
            sheet.values().append(
                spreadsheetId=SHEET_TRONG_THIEU,
                range=range_name,
                valueInputOption="RAW",
                insertDataOption="INSERT_ROWS",
                body=body
            ).execute()
    else:
        # index_p = gpt_room.index(p)
        cost_value = gpt_cost[0]
        new_value = [[start_index, cdt, gpt_address, "", gpt_status, cost_value,formatted_date]]
        body = {'values': new_value}
        sheet.values().append(
            spreadsheetId=SHEET_TRONG_THIEU,
            range=range_name,
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body=body
        ).execute() 


def execute_with_timeout(func, timeout, *args, **kwargs):
   """
   Chạy một hàm với giới hạn timeout.
   """
   start_time = time.time()
   while True:
       try:
           return func(*args, **kwargs)
       except HttpError as e:
           if time.time() - start_time > timeout:
               print("Timeout reached!")
               raise TimeoutError("Operation timed out") from e
           else:
               print("Retrying due to error:", e)


def get_date_string(dt):
   if isinstance(dt, datetime):
       return dt.strftime('%Y-%m-%d')
   return dt  

def similarity_ratio(str1, str2):
   return SequenceMatcher(None, str1, str2).ratio()


def filter_info(input_text):
    prompt = f"""
    Dưới đây là một văn bản chứa các đoạn tin nhắn. Văn bản có thể có lỗi chính tả và ký tự nhiễu (như emoticon /-heart/, /-strong/, :>:o:-((:-h), v.v.). Hãy:

    1. Trích xuất tất cả các đoạn tin nhắn, nhưng chỉ lấy từ **lần xuất hiện cuối cùng** của tin nhắn chứa cụm "Hoặc báo em cập nhật: \"trống, kín, giá mới\" lên link trên ghim giúp cho ạ" trở về sau. Nếu cụm này không xuất hiện chính xác, hãy tìm gần đúng dựa trên nội dung tương tự.
    2. Làm sạch chúng: bỏ toàn bộ emoticon và ký tự nhiễu (như /-heart1/, /-strong/, :>:o:-((:-h)), sửa lỗi chính tả đơn giản nếu có thể (ví dụ: "khôg" thành "không").
    3. Trả về một chuỗi string duy nhất, với các tin nhắn nối nhau bằng dấu xuống dòng (\n). Nếu không tìm thấy dòng mốc, trả về chuỗi rỗng (""). Bỏ qua các phần không phải tin nhắn hoặc tin nhắn trước lần cuối cùng của dòng mốc.

    Văn bản:
    {input_text}

    Trả về kết quả là một chuỗi string duy nhất.
    """

    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Bạn là một trợ lý thông minh, chuyên trích xuất và làm sạch tin nhắn từ văn bản."},
            {"role": "user", "content": prompt}
        ],
    )

    result = response.choices[0].message.content
    print("gpt1: ", result)
    return result


def extract_info(message):
    msg = filter_info(message)
    prompt = f"""
    Bạn là một mô hình AI chuyên trích xuất và phân loại tình trạng phòng trống, kín, thiếu từ tin nhắn người dùng.

    **Yêu cầu:**
    Từ đoạn tin nhắn sau, hãy phân loại và trích xuất thông tin một cách chính xác:
    **Tin nhắn:** "{msg}"


    **Trích xuất và trả về text với các trường sau:**


    - `"status"` (**bắt buộc**): Một trong sáu trạng thái sau:
        - `"full all"` → Nếu tin nhắn nói rằng **tất cả** các phòng tại địa chỉ đều kín/chật (kin/chat).
        - `"full except"` → Nếu tin nhắn nói rằng **tất cả** các phòng kín (kin) trừ **một hoặc nhiều** phòng; hoặc trừ **một hoặc nhiều** phòng trống (trong) còn lại kín (kin); hoặc chỉ trống (trong) **một hoặc nhiều** phòng; hoặc chỉ còn **một hoặc nhiều** phòng trống (trong) thôi.
        - `"full"` → Nếu tin nhắn nói rằng **một hoặc nhiều** phòng kín (kin), đầy (day) hoặc cọc (coc).
        - `"empty all"` → Nếu tin nhắn nói rằng **tất cả** các phòng tại địa chỉ đều trống (trong) hoặc tòa nhà mới (moi).
        - `"empty except"` → Nếu tin nhắn nói rằng **tất cả** các phòng trống (trong) trừ **một hoặc nhiều** phòng; hoặc trừ **một hoặc nhiều** phòng kín (kin), còn lại trống (trong); hoặc chỉ kín (kin) **một hoặc nhiều** phòng; hoặc chỉ phòng nào đó kín (kin) thôi.
        - `"empty"` → Nếu tin nhắn nói rằng **một hoặc nhiều** phòng đang trống (trong).
        - `"missing"` → Nếu tin nhắn thiếu thông tin về một số phòng.
        - `"no room"` → Nếu tin nhắn **không có địa chỉ hoặc không đề cập đến phòng**.


    - `"address"`: Địa chỉ của tòa nhà hoặc phòng trọ, ở dạng chuỗi. Nếu không có địa chỉ, trả về "".


    - `"room"`: Danh sách số phòng có trong tin nhắn, dưới dạng mảng string. Nếu không có số phòng cụ thể, trả về `[]`.
    - `"cost"`: Danh sách giá tiền có trong tin nhắn tương ứng với phòng ở trường room phía trên, dưới dạng mảng string. Nếu không có giá tiền cụ thể, trả về `0`. Giá sẽ trả về đơn vị triệu đồng ví dụ:
        - 5t: 5000000; 5 trịu: 5000000; 5 tẹo: 5000000; 5tr: 5000000 ; 5 củ: 5000000
    **Ví dụ output hợp lệ:**
    ```json
    [
        {{
            "status": "full",
            "address": "số 8 Phạm Hùng",
            "room": [406, 403],
            "cost": [4000000, 0]
        }},
        {{
            "status": "empty",
            "address": "số 3 Phạm Hùng",
            "room": [201, 202],
            "cost": [3500000, 3500000]
        }}
    ]
    Chỉ trả về dưới dạng mảng JSON, không thêm bất kỳ nội dung nào khác.
    """

    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Bạn là một trợ lý AI."},
            {"role": "user", "content": prompt}
        ]
    )


    output = response['choices'][0]['message']['content'].strip()

    print("gpt2: ",output)
    if output.startswith("```json"):
        output = output[7:-3].strip()


    try:
        json_output = json.loads(output)
        return json_output
    except json.JSONDecodeError:
        return {"error": "Không thể chuyển đổi sang JSON", "raw_output": output}



# def find_most_similar_address(target_address, address_list):
#    best_match = process.extractOne(target_address, address_list, scorer=fuzz.ratio)
#    return best_match
def find_most_similar_address(target_address, address_list):
    best_match = process.extractOne(target_address, address_list, scorer=fuzz.partial_ratio)
    return best_match

def status_room(extracted_info, address_list, room_list):

   results = []
   for info in extracted_info:
        gpt_status = info.get("status", "")
        gpt_address = info.get("address", "")
        gpt_room = info.get("room", [])
        gpt_cost = info.get("cost", [])

        if gpt_address:
            best_match = find_most_similar_address(gpt_address, address_list)
            print("best_match", best_match)
            print("gpt_address: ", gpt_address)
            print("gpt_room:", gpt_room)
            print("gpt_cost", gpt_cost)
            if best_match[1] >= 95:
                if gpt_status in ["full all", "full", "empty all", "empty", "empty except", "full except"]:
                    results.append((gpt_status, best_match[0], gpt_room, gpt_cost))
                elif gpt_status == "missing":
                    results.append((gpt_status, gpt_address, gpt_room, gpt_cost))
                elif gpt_status == "no room":
                    results.append((gpt_status, 1, 1, 1))
                else:
                    print("Dữ liệu không hợp lệ")
                    results.append((0, 0, 0, 0))

            else:
                print("Không có phòng trong danh sách")
                results.append(("missing", gpt_address, gpt_room, gpt_cost))

   return results

def get_date_string(dt):
   if isinstance(dt, datetime):
       return dt.strftime('%Y-%m-%d')
   return dt  


def process_message(message, cdt):
   print("đang chạy server")
   creds = None
   extracted_info = extract_info(message)
   if not extracted_info:
       return {"error": "GPT không trả về dữ liệu hợp lệ"}

   if os.path.exists("D:\\BlankProcess\\token.json"):
       creds = Credentials.from_authorized_user_file("D:\\BlankProcess\\token.json", SCOPES)

   if not creds or not creds.valid:
       if creds and creds.expired and creds.refresh_token:
           creds.refresh(Request())
       else:
           flow = InstalledAppFlow.from_client_secrets_file("D:\\BlankProcess\\credentials.json", SCOPES)
           creds = flow.run_local_server(port=0)

       with open("D:\\BlankProcess\\token.json", "w") as token:
           token.write(creds.to_json())


   try:
       service = build("sheets", "v4", credentials=creds)
       sheet = service.spreadsheets()



       tenzalo = sheet.values().get(spreadsheetId=SHEET_THONG_TIN, range=RANGE_THONGTIN_TENZALO).execute()
       values = tenzalo.get('values', [])
       # print(values)

       # processed_values = [[cell if cell else "" for cell in row] for row in values]
       # print("cdt: ", cdt)
       for r in values:
           # print("dang chay den day")
           # print(r)

           if r[0] == cdt and len(r) < 3:

               print("Không có link google sheet")

               for info in extracted_info:
                   gpt_status = info.get("status", "")
                   gpt_address = info.get("address", "")
                   gpt_room = info.get("room", [])
                   gpt_cost = info.get("cost", [])
                #    print("GPTTTTTTTTTTTTTTTT", gpt_status, gpt_address, gpt_room, gpt_cost)

                   if gpt_status == "full":
                       print("Phòng kín, thoát")


                    ###################################################################
                    ######### Chen phong thieu vao bang phong thieu o sheet tong
                    ###################################################################


                   elif gpt_status == "missing":
                        print("Phòng thiếu, chèn vào bảng phòng thiếu")
                        insert_sheet_tong(sheet, cdt, gpt_address, gpt_room, gpt_status, gpt_cost)


                    ###################################################################
                    ######### Chen phong trong vao bang phong trong o sheet tong
                    ###################################################################


                   elif gpt_status == "empty":
                         print("Phòng trống, chèn vào bảng phòng trống")
                         insert_sheet_tong(sheet, cdt, gpt_address, gpt_room, gpt_status, gpt_cost)

                   elif gpt_status == "empty_except":
                         print("Phòng trống, chèn vào bảng phòng trống")
                         insert_sheet_tong(sheet, cdt, gpt_address, gpt_room, gpt_status, gpt_cost)
                
                   elif gpt_status == "full_except":
                         print("Phòng trống, chèn vào bảng phòng trống")
                         insert_sheet_tong(sheet, cdt, gpt_address, gpt_room, gpt_status, gpt_cost)
                    ################################################################
                    ###### Co mot hoac nhieu phong kin, sua stt cac phong trong sheet rieng
                    ################################################################


           elif r[0] == cdt and len(r) >= 3:
               # print(r)
               print("Đang chạy đến đây")
               id = choose_id_speadsheet(r[2])

               list_addr = sheet.values().get(spreadsheetId=id, range="A:E").execute()

               addr_values = list_addr.get('values', [])
               # filtered_addr_values = [f"{row[0]} {row[1]}" for row in addr_values if len(row) > 1]
               filtered_addr_values = [f"{row[1]}" for row in addr_values if len(row) > 1]
               filtered_room_values = [f"{row[2]}" for row in addr_values if len(row) > 1]

               data = list_addr.get('values', [])

               # print("filtered_addr_values", filtered_addr_values)
               results = status_room(extracted_info, filtered_addr_values, filtered_room_values)

               for stt, gpt_address, gpt_room, gpt_cost in results: 
                   if stt == "full all":
                       print("tất cả các phòng trong tòa kín phòng, chèn vào sheet các tòa này đều kín")

                       for row_idx, row in enumerate(data, start=1):
                               dia_chi = row[1]
                               if similarity_ratio(dia_chi, gpt_address) >=KKK:
                                   trang_thai_cell = f"E{row_idx}"
                                   print("chèn vào đây")
                                   sheet.values().update(
                                       spreadsheetId=id,   
                                       range=trang_thai_cell,    
                                       valueInputOption="RAW",    
                                       body={"values": [["kín"]]}  
                                   ).execute()
                               else:
                                   continue
    
                   elif stt == "full":
                       print("Phòng kín, chèn vào sheet")
                       check_list = gpt_room
                       cost_list = gpt_cost
                       for row_idx, row in enumerate(data, start=1):
                           if len(row) > 4:  
                               dia_chi = row[1]  
                               phong = row[2]    
                               trang_thai_cell = f"E{row_idx}"  
                               # print(gpt_room)
                               cost_cell = f"F{row_idx}"
                               if similarity_ratio(dia_chi, gpt_address) >= KKK:
                                   for p in gpt_room:
                                       if similarity_ratio(phong, p) > KKK:
                                           index_p = gpt_room.index(p)
                                           cost_value = gpt_cost[index_p]
                                           try:
                                               sheet.values().update(
                                                   spreadsheetId=id,
                                                   range=trang_thai_cell,
                                                   valueInputOption="RAW",
                                                   body={"values": [["kín"]]}
                                               ).execute()
                                               print("Cập nhật thành công phòng kín!")
                                               check_list.remove(p)
                                               if cost_value:
                                                   sheet.values().update(
                                                       spreadsheetId=id,
                                                       range=cost_cell,
                                                       valueInputOption="RAW",
                                                       body={"values": [[cost_value]]}
                                                   ).execute()
                                                   print("Cập nhật thành công giá tiền!")
                                                   cost_list.remove(cost_value)
    
    
                                           except Exception as e:
                                               print(f"Lỗi cập nhật: {e}")
                       if check_list != []:
                           insert_sheet_tong(sheet, cdt, gpt_address, gpt_room, stt, gpt_cost)

                   elif stt == "empty":
                       print("Phòng trống, chèn vào sheet")
                       check_list = gpt_room
                       cost_list = gpt_cost
                       for row_idx, row in enumerate(data, start=1):
                           if len(row) > 4:  
    
                               dia_chi = row[1]  
                               phong = row[2]    
                               trang_thai_cell = f"E{row_idx}"  
                               cost_cell = f"F{row_idx}"
    
    
                               if similarity_ratio(dia_chi, gpt_address) >= KKK:
                                   for p in gpt_room:
                                       if similarity_ratio(phong, p) > KKK:
                                           index_p = gpt_room.index(p)
                                           cost_value = gpt_cost[index_p]
                                           try:
                                               sheet.values().update(
                                                   spreadsheetId=id,
                                                   range=trang_thai_cell,
                                                   valueInputOption="RAW",
                                                   body={"values": [["trống"]]}
                                               ).execute()
                                               print("Cập nhật thành công phòng trống!")
                                               check_list.remove(p)
                                               if cost_value:
                                                   sheet.values().update(
                                                       spreadsheetId=id,
                                                       range=cost_cell,
                                                       valueInputOption="RAW",
                                                       body={"values": [[cost_value]]}
                                                   ).execute()
                                                   print("Cập nhật thành công giá tiền!")
                                                   cost_list.remove(cost_value)
                                           except Exception as e:
                                               print(f"Lỗi cập nhật: {e}")
                       if check_list != []:
                           insert_sheet_tong(sheet, cdt, gpt_address, gpt_room, stt, gpt_cost)
    
    
                   elif stt == "empty all":
                       print("tất cả các phòng trong tòa đều trống, chèn vào sheet cac tòa này đều trống")
                       # new_value = [["trống"]]
                       # body = {'values': new_value}
    
    
                       for row_idx, row in enumerate(data, start=1):
                               dia_chi = row[1]
                               if similarity_ratio(dia_chi, gpt_address) >=KKK:
                                   trang_thai_cell = f"E{row_idx}"
                                   print("chèn vào đây")
                                   sheet.values().update(
                                       spreadsheetId=id,    
                                       range=trang_thai_cell,     
                                       valueInputOption="RAW",    
                                       body={"values": [["trống"]]}  
                                   ).execute()    
    
                   elif stt == "empty except":
                       print("Cả tòa trống chỉ có một số phòng kín")
                       check_list = gpt_room
                       for row_idx, row in enumerate(data, start=1):
                           dia_chi = row[1]  
                           phong = row[2]    
                           trang_thai_cell = f"E{row_idx}"  
    
    
                           if similarity_ratio(dia_chi, gpt_address) >= KKK:
                               for p in gpt_room:
                                   # print("aaaa", p, phong)
                                   if similarity_ratio(phong, p) >= KKK:
                                       check_list.remove(p)
                                       # print("cho nay phong trong", trang_thai_cell)
                                       sheet.values().update(
                                           spreadsheetId=id,    
                                           range=trang_thai_cell,     
                                           valueInputOption="RAW",   
                                           body={"values": [["kín"]]}  
                                       ).execute()
                                       break
    
    
                                   else:
                                       sheet.values().update(
                                           spreadsheetId=id,   
                                           range=trang_thai_cell,     
                                           valueInputOption="RAW",    
                                           body={"values": [["trống"]]}  
                                       ).execute()

    
                       if check_list != []:
                           insert_sheet_tong(sheet, cdt, gpt_address, check_list, stt, gpt_cost)
                   elif stt == "full except":
                       print("Cả tòa kín chỉ còn một số phòng trống")
                       check_list = gpt_room
                       for row_idx, row in enumerate(data, start=1):
                           dia_chi = row[1]  # Cột D - Địa chỉ
                           phong = row[2]    # Cột B - Phòng
                           trang_thai_cell = f"E{row_idx}"  # Xác định ô cột E cần cập nhật
    
    
                           if similarity_ratio(dia_chi, gpt_address) >= KKK:
                               for p in gpt_room:
                                   # print("aaaa", p, phong)
                                   if similarity_ratio(phong, p) >= KKK:
                                       check_list.remove(p)
                                       # print("cho nay phong trong", trang_thai_cell)
                                       sheet.values().update(
                                           spreadsheetId=id,    # ID của Google Sheet
                                           range=trang_thai_cell,     # Ô cần cập nhật, ví dụ: "E5"
                                           valueInputOption="RAW",    # Cách nhập dữ liệu
                                           body={"values": [["trống"]]}  # Dữ liệu cần chèn vào ô
                                       ).execute()
                                       break
    
    
                                   else:
                                       sheet.values().update(
                                           spreadsheetId=id,    # ID của Google Sheet
                                           range=trang_thai_cell,     # Ô cần cập nhật, ví dụ: "E5"
                                           valueInputOption="RAW",    # Cách nhập dữ liệu
                                           body={"values": [["kín"]]}  # Dữ liệu cần chèn vào ô
                                       ).execute()
                           else:
                               continue
                       if check_list != []:
                           insert_sheet_tong(sheet, cdt, gpt_address, check_list, stt, gpt_cost)
    
    
                   elif stt == "missing":
                       print("Phòng thiếu, chèn vào bảng phòng thiếu")
                       insert_sheet_tong(sheet, cdt, gpt_address, gpt_room, stt, gpt_cost)
    
    
                   elif stt == "no room":
                       print("Không có phòng hoặc địa chỉ, không chèn")
           # else:
               # print("Khong co ten chu dau tu")


   except TimeoutError:
       return {"error": "Operation timed out after 10 seconds"}
   except HttpError as err:
       return {"error": f"An error occurred: {err}"}


@app.route('/update_sheet', methods=['POST'])


##############
# Ham update_sheet lay du lieu data tu request va truyen vao process
##############


def update_sheet():
   try:
       data = request.json
       if not data or 'value' not in data or 'cdt' not in data:
           return jsonify({"error": "Missing 'value' or 'cdt' in request body"}), 400

       value = data['value'] 
       cdt = data['cdt']      
       print(value)

       print(f"Received value: {value}, CDT: {cdt}")

       k = process_message(value, cdt)
       print("Output from process_message:", k)

       if k is None:
           return jsonify({"error": "Processing failed, no output generated"}), 500

       return jsonify({"status": "success", "output": k}), 200
   except Exception as e:
       print(f"Exception occurred: {e}")
       return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
   app.run(debug=True, port=5000)
