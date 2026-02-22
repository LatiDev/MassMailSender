import auth

import time, json, typing, pathlib, dataclasses, sys

@dataclasses.dataclass
class DraftEmail:
    service: typing.Any
    name: str
    title: str
    message: str
    file: str

class Mail(DraftEmail):
    def __init__(self, draft: DraftEmail, to: str):
        super().__init__(
            draft.service, 
            draft.name, 
            draft.title, 
            draft.message, 
            draft.file
        )
        self.to = to

    def __hash__(self):
        return hash(self.to)

@dataclasses.dataclass
class SendConfiguration:
    wait_time: int

def send_mail(mail: Mail):
    send_one(
        mail.service, 
        mail.name, 
        mail.to, 
        mail.title, 
        mail.message, 
        mail.file
    )

def send_one(service, name, to, title, message, file):
    message = auth.create_message(name, to, title, message, file)
    auth.send_message(service, 'me', message)

def send_all(emails: list[Mail], config: SendConfiguration, history: list[str]):
    mail_send, mail_error = [], []
    
    for index, mail in enumerate(emails):            
        if mail.to == "":
            print(f"Skip {mail.to}. Invalid sender email")
            continue

        if mail.to in history:
            print(f"Already sended an email to {mail.to}. Skipping...")
            continue

        time.sleep(config.wait_time)

        try:
            print(f"{index + 1}/{len(emails)} ({round((index + 1)/len(emails), 2)*100}%) - Sending to {mail.to}")
            send_mail(mail)

            mail_send.append(mail.to)
        except Exception as error:
            mail_error.append(mail.to)
            print(f"> Error sending message to {mail.to} : {error}")

    return mail_send, mail_error

def is_good_file(filename: str):
    try:
        path = pathlib.Path(filename)
        if not path.exists():
            raise Exception(f"'{path}' doenst exists")

        data = path.read_text(encoding="latin-1")
        if len(data) == 0:
            raise Exception(f"no data found in '{path}'. Is it empty ?")

        return data
    except Exception as error:
        return error

if __name__ == "__main__":
    SUCCESS, ERROR = 0, 1

    SENDED_PATH = pathlib.Path(".history")
    SENDED_PATH.touch(exist_ok=True)
    past_history: str = SENDED_PATH.read_text()
    past_history: list[str] = set([email.strip() for email in past_history.split('\n')])

    all = ["name", "email", "subject", "message_file", "emails_file", "cv_file"]

    ME_PATH = pathlib.Path("me.json")
    if not ME_PATH.exists():
        print(f"No {ME_PATH} found. Please fill it")
        ME_PATH.write_text(json.dumps(dict([(key, "to fill") for key in all]), indent=4))
        sys.exit(ERROR)

    me: dict = json.loads(ME_PATH.read_text())

    print(f"Verifying {ME_PATH}...")
    for key in all:
        if not me.get(key, None):
            print(f"{key} key not found in {ME_PATH}. Please include and fill it")
            sys.exit(ERROR)

    name, email, subject, message_file, emails_file, cv_file = [me[key] for key in all]

    print(f"Verifying message_file: '{message_file}'...")
    message = is_good_file(message_file)
    if isinstance(message, Exception):
        print(message)
        sys.exit(ERROR)

    print(f"Verifying cv_file: '{cv_file}'...")
    cv = is_good_file(cv_file)
    if isinstance(cv, Exception):
        print(cv)
        sys.exit(ERROR)

    CONFIG = SendConfiguration(1)
    SERVICE = auth.get_credentials()

    draft = DraftEmail(SERVICE, name, subject, message, cv_file)    

    want_test = input("Do you want to send a test email ? (y/n) ")
    if want_test == 'y':
        want_email = input("Test email: ")
        print(f"Sending an email to: {want_email}...")
        send_all([Mail(draft, want_email)], CONFIG, [])

    want_launch = input(f"Do you want to send all emails (in {emails_file}) ? (y/n) ")
    if want_launch == 'y':
        emails = is_good_file(emails_file)
        if isinstance(emails, Exception):
            print(emails)
            sys.exit(ERROR)

        filtered = set([email.strip() for email in emails.split('\n')])
        mails = set([Mail(draft, email) for email in filtered])

        want_send = input(f"Do you want send {len(mails)} emails ? (y/n) ")
        if want_send == 'y':
            sends, errors = send_all(mails, CONFIG, past_history)

            for send in sends:
                with open(SENDED_PATH, "a") as file:
                    file.write(f"{send}\n")

    sys.exit(SUCCESS)