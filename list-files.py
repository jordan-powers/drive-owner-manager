from pathlib import Path
from auth import get_creds
from googleapiclient.discovery import build

import csv

creds = get_creds()

MOMENTUM_ROOT_FOLDER = '1jGY4sRF004Yu__BAOmk1by2Nt6MJ5zHB'

class User:
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email

    @staticmethod
    def from_dict(data) -> 'User':
        return User(data['displayName'], data.get('emailAddress', ''))

    def __str__(self):
        return self.name

    def __repr__(self):
        return f'User(name="{self.name}", email="{self.email}")'

class File:
    def __init__(self, id: str, name: str, mimeType: str, owner: User):
        self.id = id
        self.name = name
        self.mimeType = mimeType
        self.owner = owner

    def __str__(self):
        return f'{self.name} ({self.mimeType})'

    def __repr__(self):
        return f'File(id="{self.id}", name="{self.name}", mimeType="{self.mimeType}", owner={repr(self.owner)})'

    @staticmethod
    def from_dict(data) -> 'File':
        return File(data['id'], data['name'], data['mimeType'], User.from_dict(data['owners'][0]))

service = build('drive', 'v3', credentials=creds)
files = service.files()

def list_files(folderId: str) -> 'list[File]':
    result = files.list(fields='nextPageToken, files(id, owners, name, mimeType)', pageSize=10, q=f"'{folderId}' in parents", orderBy='name').execute()
    return [File.from_dict(f) for f in result['files']]

def log_folder(folderId: str, writer: csv.DictWriter, path_prefix: str):
    print(path_prefix)
    for file in list_files(folderId):
        path = path_prefix + '/' + file.name

        try:
            writer.writerow({
                'path': path,
                'id': file.id,
                'name': file.name,
                'type': file.mimeType,
                'owner name': file.owner.name,
                'owner email': file.owner.email
            })
        except UnicodeEncodeError:
            print('UnicodeEncodeError for file: ' + repr(file))
            continue

        if file.mimeType == 'application/vnd.google-apps.folder':
            log_folder(file.id, writer, path)

outfile = Path.cwd() / 'files.csv'
with outfile.open('w', newline='', encoding='utf8') as outf:
    writer = csv.DictWriter(outf, ['path', 'id', 'name', 'type', 'owner name', 'owner email'])
    writer.writeheader()

    log_folder(MOMENTUM_ROOT_FOLDER, writer, 'Team 4999')
