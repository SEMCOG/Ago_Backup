from arcgis.gis import GIS
import os
import shutil
import passwords
import subprocess
import urllib.request
import time


def commit():
    subprocess.call(['git', 'add', '.'], cwd="Content")
    subprocess.call(['git', 'commit', '-m', 'automatic commit'], cwd="Content")


def del_unused(location, new_names):
    try:
        old_names = set(os.listdir(location))
    except (FileNotFoundError, OSError):
        return
    for name in (old_names - set(new_names)):
        print("deleting:", os.path.join(location, name))
        shutil.rmtree(os.path.join(location, name))


def download_item(location, item):
    try:
        os.makedirs(location, exist_ok=True)
    except (FileNotFoundError, OSError):
        print(os.path.join(location, item.title))
        print("bad PATH !!!!!!!!!!!!!!!!!!!!!")
        return
    try:
        with open(os.path.join(location, "timestamp.txt"), "r+") as timestamp:
            old_timestamp = timestamp.read()
    except FileNotFoundError:
        old_timestamp = ""

    item_modified = str(item.modified)

    if item.type == 'Feature Service' and hasattr(item, 'layers') and item.layers is not None:
            for layer in item.layers:
                if hasattr(layer, 'properties'):
                    if hasattr(layer.properties, 'editingInfo'):
                        item_modified += "," + str(layer.properties.editingInfo.lastEditDate)

    if old_timestamp != item_modified:
        print(os.path.join(location, item.title))
        try:
            if item.type == 'Feature Service':
                print("exporting:" + item.title)
                try:
                    export_type = 'File Geodatabase'
                    if len(item.layers) == 0:
                        export_type = 'CSV'

                    if 'ago_view' not in item.tags:
                        export = item.export(item.title + suffix_of_backup_content, export_type)
                        export.download(location)
                        export.delete()
                    else:
                        print(item.title + " - Cannot be exported")
                except (KeyError) as e:
                    print(item.title + " - Cannot be exported")
                    print(e)

            item.download(location)
            item.download_metadata(location)
            with open(os.path.join(location, "timestamp.txt"), "w") as timestamp:
                timestamp.write(item_modified)
        except (FileNotFoundError, OSError, Exception) as e:
            print("bad PATH !!!!!!!!!!!!!!!!!!!!!")
            print(e)


def download_items(location, items):
    del_unused(location, {item.title for item in items})
    for item in items:
        download_item(os.path.join(location, item.title), item)


def download_type(location, types):
    del_unused(location, types)
    for itemtype, content in types.items():
        if itemtype != 'Code Attachment':
            download_items(os.path.join(location, itemtype), content)


def download_user(location, user_content):
    del_unused(location, user_content)
    for folder, content in user_content.items():
        types = {}
        for item in content:
            types.setdefault(item.type, []).append(item)
        download_type(os.path.join(location, folder), types)

starttime = time.clock()

suffix_of_backup_content = '_SourceData_ForBackup'
gis = GIS("https://www.arcgis.com", passwords.user_name, passwords.password)

for item in gis.users.get(passwords.user_name).items():
    if item.title.endswith(suffix_of_backup_content):
        item.delete()

source_users = gis.users.search()

for user in source_users:
    print("Collecting item ids for {}".format(user.username))
    user_content = {}
    user_content["None"] = user.items()

    for folder in user.folders:
        user_content[folder['title']] = user.items(folder=folder['title'])

    download_user(os.path.join("Content", "Users", user.username), user_content)

commit()

urllib.request.urlopen(passwords.hc_ping)

print('process completed in ' + str(time.clock() - starttime))
