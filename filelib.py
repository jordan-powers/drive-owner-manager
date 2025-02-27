from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from pathlib import Path

FOLDER_TYPE = "application/vnd.google-apps.folder"

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
    FIELDS = 'id, owners, name, mimeType, ownedByMe, parents'

    def __init__(self, id: str, name: str, mimeType: str, owner: User, ownedByMe: bool, parentId: str):
        self.id = id
        self.name = name
        self.mimeType = mimeType
        self.owner = owner
        self.ownedByMe = ownedByMe
        self.parentId = parentId

    def __str__(self):
        return f'{self.name} ({self.mimeType})'

    def __repr__(self):
        return f'File(id="{self.id}", name="{self.name}", mimeType="{self.mimeType}", owner={repr(self.owner)}, ownedByMe={self.ownedByMe}, parentId={self.parentId})'

    @staticmethod
    def from_dict(data) -> 'File':
        return File(data['id'], data['name'], data['mimeType'], User.from_dict(data['owners'][0]), data['ownedByMe'], data['parents'][0])

class FileOps:
    def __init__(self, service):
        self.service = service
        self.files = self.service.files()

    @staticmethod
    def from_creds(creds):
        return FileOps(build('drive', 'v3', credentials=creds))

    def listFiles(self, folderId: str) -> 'list[File]':
        out = []
        pageToken = None
        while True:
            query = {
                'fields': f'nextPageToken, files({File.FIELDS})',
                'pageSize': '10',
                'q': f"'{folderId}' in parents",
                'orderBy': 'name'
            }
            if pageToken is not None:
                query['pageToken'] = pageToken
            result = self.files.list(**query).execute()
            out.extend(File.from_dict(f) for f in result['files'])
            if 'nextPageToken' in result:
                pageToken = result['nextPageToken']
            else:
                pageToken = None
            if not pageToken:
                break
        return out

    def mkdir(self, parentId: str, name: str) -> 'File':
        response = self.files.create(body={
            "name": name,
            "parents": [parentId],
            "mimeType": FOLDER_TYPE,
        }, fields=File.FIELDS).execute()

        return File.from_dict(response)

    def getFile(self, fileId: str) -> 'File':
        response = self.files.get(fileId=fileId, fields=File.FIELDS).execute()
        return File.from_dict(response)

    def move(self, file: File, newParentId: str) -> 'File':
        response = self.files.update(
            fileId=file.id,
            addParents=newParentId,
            removeParents=file.parentId,
            fields=File.FIELDS
        ).execute()
        return File.from_dict(response)

    def copy(self, file: File, newParentId: str) -> 'File':
        response = self.files.copy(
            fileId=file.id,
            body={
                'parents': [newParentId],
                'name': file.name
            }, fields=File.FIELDS
        ).execute()
        return File.from_dict(response)

    def upload(self, parentId: str, upload: Path) -> 'File':
        media = MediaFileUpload(str(upload), 'text/csv')
        file = self.files.create(body={
            'name': upload.name,
            'parents': [parentId]
        }, media_body=media, fields=File.FIELDS).execute()

        return file
