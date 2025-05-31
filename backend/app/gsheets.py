import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
# `load_dotenv` is called in main.py

def get_google_sheet_instance():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    creds_file_name = os.getenv("GOOGLE_CREDENTIALS_FILE")

    if not creds_file_name:
        raise ValueError("GOOGLE_CREDENTIALS_FILE environment variable not set.")
    
    # This assumes creds_file_name is just "google_credentials.json" and it's in the CWD (backend/)
    if not os.path.exists(creds_file_name):
        raise FileNotFoundError(
            f"Google credentials file '{creds_file_name}' not found. "
            f"Ensure GOOGLE_CREDENTIALS_FILE in .env is set correctly and the file exists in the `backend` directory (where uvicorn is run)."
        )
                                
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file_name, scope)
    client = gspread.authorize(creds)
    return client

def save_to_google_sheet(data: list[dict], sheet_id: str): # Expects list of dicts
    """
    Saves data to the specified Google Sheet.
    Expects data as a list of dictionaries.
    """
    try:
        client = get_google_sheet_instance()
        sheet = client.open_by_key(sheet_id).sheet1 

        sheet.clear() # Clear existing content

        if not data:
            # print("No data to save to Google Sheet.") # Logged in main.py
            # Write headers even if data is empty, so the sheet isn't totally blank
            # This requires knowing the expected headers. Let's assume ReviewItem fields.
            # Or, decide if an empty sheet is okay. For now, let's assume if data is empty, we write nothing.
            # If you want headers for an empty data case, you'd need to define them.
            # For simplicity, if no data, sheet remains cleared or headers are not written.
            # Let's ensure headers are written if data is empty, using a predefined list.
            # This is tricky if data can be truly empty vs. empty after filtering.
            # The current main.py logic ensures `data` passed here is not empty if reviews were processed.
            # If `processed_reviews_for_sheets` is empty, it won't call this with empty data.
            # Let's assume `data` will have at least one item if called, or this won't be called.
            # However, if it *could* be called with empty data and you want headers:
            # default_headers = ["product_name", "review_text", "rating", "sentiment_label", "sentiment_score"]
            # sheet.append_row(default_headers)
            return f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"


        headers = list(data[0].keys()) # Assumes all dicts in 'data' have same keys
        sheet.append_row(headers)

        rows_to_append = []
        for item_dict in data:
            row = [item_dict.get(header, "") for header in headers]
            rows_to_append.append(row)
        
        if rows_to_append:
            sheet.append_rows(rows_to_append, value_input_option='USER_ENTERED')
        
        # print(f"Data successfully saved to Google Sheet ID: {sheet_id}") # Logged in main.py
        return f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
    except gspread.exceptions.APIError as e:
        error_details = "Unknown API error"
        try:
            error_details = e.response.json().get('error', {}).get('message', str(e))
        except: # In case response is not JSON or structure is different
            error_details = str(e)
        raise Exception(f"Google Sheets API error: {error_details}")
    except Exception as e:
        # print(f"Error saving to Google Sheet: {e}") # Logged in main.py
        raise