from pathlib import Path
from auth import get_creds
import filelib
import csv

creds = get_creds()

ROOT_FOLDERS = [
    ('1jGY4sRF004Yu__BAOmk1by2Nt6MJ5zHB', 'Team 4999'),
    ('1xvTNdkxACOncaTtJZRQALwPmygVKFWT_', 'Team 4999 - Leadership')
]

lister = filelib.FileOps.from_creds(creds)

def log_folder(folderId: str, writer: csv.DictWriter, path_prefix: str):
    print(path_prefix)
    for file in lister.listFiles(folderId):
        path = path_prefix + '/' + file.name

        try:
            writer.writerow({
                'path': path,
                'id': file.id,
                'name': file.name,
                'type': file.mimeType,
                'size': file.size,
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
    writer = csv.DictWriter(outf, ['path', 'id', 'name', 'type', 'size', 'owner name', 'owner email'])
    writer.writeheader()

    for folder_id, path_prefix in ROOT_FOLDERS:
        log_folder(folder_id, writer, path_prefix)
