from auth import get_creds
import filelib
from googleapiclient.discovery import build
from argparse import ArgumentParser
from datetime import datetime
from pathlib import PurePosixPath

ARCHIVE_ROOT = '1_RxmBpigXbY2cyI3rbO8KQBHmOg8-_Nu'

parser = ArgumentParser(description='create a backup of files owned by other users')
parser.add_argument('target_dir', help='the fileid of the directory to scan')
parser.add_argument('--strict', action='store_true', help='copy all files not owned by me instead of just lbschools users')

args = parser.parse_args()

creds = get_creds()
service = build('drive', 'v3', credentials=creds)
fileops = filelib.FileOps(service)

archive = fileops.mkdir(ARCHIVE_ROOT, datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "-backup-unowned")

def check_loose(file: filelib.File):
    return file.owner.email.endswith('@lbschools.net')

def check_strict(file: filelib.File):
    return not file.ownedByMe

if args.strict:
    check = check_strict
else:
    check = check_loose

dir_tree: 'dict[PurePosixPath, filelib.File]' = {
    PurePosixPath('/'): archive
}

def get_dest(path: PurePosixPath) -> filelib.File:
    if path in dir_tree:
        return dir_tree[path]

    assert path != PurePosixPath('/')

    dest_parent = get_dest(path.parent)
    file = fileops.mkdir(dest_parent.id, path.name)
    dir_tree[path] = file
    return file

def backup_recursive(source: filelib.File, path: PurePosixPath):
    print("> " + str(path))
    for file in fileops.listFiles(source):
        if file.mimeType != filelib.FOLDER_TYPE:
            if check(file):
                print("* " + str(path / file.name))
                dest = get_dest(path)
                fileops.copy(file, dest)
        else:
            backup_recursive(file, path / file.name)

target = fileops.getFile(args.target_dir)
print(f"Backing up {target.name}")
backup_recursive(target, PurePosixPath('/'))
