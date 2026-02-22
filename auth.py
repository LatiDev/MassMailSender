from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email import encoders
from email.mime.base import MIMEBase

import base64, mimetypes, os, pickle

SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
]

TOKEN = "token.pickle"

def get_credentials():
    creds = None
    if os.path.exists(TOKEN):
        with open(TOKEN, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)

        with open(TOKEN, 'wb') as token:
            pickle.dump(creds, token)

    return build('gmail', 'v1', credentials=creds)

def create_message(sender, to, subject, message_text, file_path):
    message = MIMEMultipart()
    message["to"] = to
    message["from"] = sender
    message["subject"] = subject

    message.attach(MIMEText(message_text, "plain"))

    content_type, encoding = mimetypes.guess_type(file_path)
    if content_type is None or encoding is not None:
        content_type = "application/octet-stream"

    main_type, sub_type = content_type.split("/", 1)

    with open(file_path, "rb") as f:
        file_data = f.read()

    attachment = MIMEBase(main_type, sub_type)
    attachment.set_payload(file_data)    
    encoders.encode_base64(attachment)
    filename = os.path.basename(file_path)
    attachment.add_header("Content-Disposition", "attachment", filename=filename)

    message.attach(attachment)

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {"raw": raw}

def send_message(service, user_id, message):
    return service.users().messages().send(userId=user_id, body=message).execute()