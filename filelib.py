from googleapiclient.discovery import build

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

class FileLister:
    def __init__(self, creds):
        self.service = build('drive', 'v3', credentials=creds)
        self.files = self.service.files()

    def list_files(self, folderId: str) -> 'list[File]':
        out = []
        pageToken = None
        while True:
            query = {
                'fields': 'nextPageToken, files(id, owners, name, mimeType)',
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
