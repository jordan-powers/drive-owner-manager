from auth import get_creds
from googleapiclient.discovery import build
from datetime import datetime
import filelib
from pathlib import Path
import csv
from argparse import ArgumentParser

ARCHIVE_ROOT = '1_RxmBpigXbY2cyI3rbO8KQBHmOg8-_Nu'

parser = ArgumentParser(description='replace files owned by other users with copies')
parser.add_argument('target_dir', help='the fileid of the directory to scan')
parser.add_argument('-d', '--dirs-only', action='store_true', help='only take ownership of directories')

args = parser.parse_args()

creds = get_creds()
service = build('drive', 'v3', credentials=creds)
fileops = filelib.FileOps(service)

archive = fileops.mkdir(ARCHIVE_ROOT, datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "-take-ownership")

def log_op(writer: 'csv.DictWriter', op: str, oldfile: 'filelib.File|None', newfile: 'filelib.File'):
    writer.writerow({
        'op': op,
        'file name': oldfile.name if oldfile else newfile.name,
        'original_id': oldfile.id if oldfile else '',
        'new_id': newfile.id,
        'original_parent': oldfile.parentId if oldfile else '',
        'new_parent': newfile.parentId
    })

def restore_recursive(writer: 'csv.DictWriter', archived: 'filelib.File', dest: 'filelib.File', path=''):
    for file in fileops.listFiles(archived.id):
        print(path + '/' + file.name)
        if file.mimeType != filelib.FOLDER_TYPE:
            if file.ownedByMe or args.dirs_only:
                moved = fileops.move(file, dest.id)
                log_op(writer, 'move', file, moved)
            else:
                copied = fileops.copy(file, dest.id)
                log_op(writer, 'copy', file, copied)
        else:
            new_dest = fileops.mkdir(dest.id, file.name)
            log_op(writer, 'create', None, new_dest)
            restore_recursive(writer, file, new_dest, path=path + '/' + file.name)

logfile = Path.cwd() / 'action_log.csv'

with logfile.open('w', newline='', encoding='utf8') as logf:
    writer = csv.DictWriter(logf, ['op', 'file name', 'original_id', 'new_id', 'original_parent', 'new_parent'])
    writer.writeheader()

    for file in fileops.listFiles(args.target_dir):
        if file.mimeType != filelib.FOLDER_TYPE:
            if not args.dirs_only and not file.ownedByMe:
                moved = fileops.move(file, archive.id)
                log_op(writer, 'move', file, moved)
                copied = fileops.copy(moved, args.target_dir)
                log_op(writer, 'copy', moved, copied)
        else:
            moved = fileops.move(file, archive.id)
            log_op(writer, 'move', file, moved)
            new_dest = fileops.mkdir(args.target_dir, moved.name)
            log_op(writer, 'create', None, new_dest)
            restore_recursive(writer, moved, new_dest, moved.name)

fileops.upload(archive, logfile)


