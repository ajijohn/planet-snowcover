from apiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
from httplib2 import Http

scopes = ['https://www.googleapis.com/auth/drive']

credentials = ServiceAccountCredentials.from_json_keyfile_name('uw-mino.json', scopes)

http_auth = credentials.authorize(Http())
drive = build('drive', 'v3', http=http_auth)

request = drive.files().list().execute()
files = request.get('items', [])
for f in files:
    print(f)
