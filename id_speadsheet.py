import re


def choose_id_speadsheet(text):
    match = re.search(r"/d/([^/]+)/", text)
    if match:
        sheet_id = match.group(1)
        print("Sheet ID:", sheet_id)
    return sheet_id

