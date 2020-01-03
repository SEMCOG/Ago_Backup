from arcgis.gis import GIS
import os
import shutil
import datetime
import passwords
import subprocess
import urllib.request
import time
import logging
import sys


logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger()
logger.addHandler(logging.FileHandler(os.path.join('Content', 'last_run.log'), 'w'))
logging.raiseExceptions = True

fail_count = 0

def my_excepthook(excType, excValue, traceback, logger=logger):
    logger.error("Logging an uncaught exception",
                 exc_info=(excType, excValue, traceback))

sys.excepthook = my_excepthook

def clean_location(location):
    return location.replace('/','-').replace('$','-').replace(':','-').strip()

def commit():
    subprocess.call(['git', 'add', '.'], cwd="Content")
    subprocess.call(['git', 'commit', '-m', 'automatic commit'], cwd="Content")


def del_unused(location, new_names):
    try:
        old_names = set(os.listdir(location))
    except (FileNotFoundError, OSError):
        return
    for name in (old_names - {clean_location(name) for name in new_names}):
        print("deleting:", os.path.join(location, name))
        logger.info('deleting: ' + os.path.join(location, name))
        shutil.rmtree(os.path.join(location, name))


def download_item(location, item):
    global fail_count
    try:
        os.makedirs(location, exist_ok=True)
    except (FileNotFoundError, OSError):
        logger.warning('Bad Path !!!!: ' + location)
        item.share(['Failed to back up'])
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
        logger.info('This item changed: ' + os.path.join(location, clean_location(item.title)))

        try:
            skip_if_failed = (datetime.datetime.today().weekday() < 5) #weekday
            failed_backup = skip_if_failed and "Failed to back up" in {i.title for i in item.shared_with['groups']}
            if failed_backup:
                logger.info(item.title + " - Skipped export")
                raise Exception("Failed to back up")
            if item.type == 'Feature Service':
                logger.info("exporting:" + item.title)
                try:
                    export_type = 'File Geodatabase'
                    if len(item.layers) == 0:
                        export_type = 'CSV'
                    is_view = len(item.layers) >= 1 and hasattr(item.layers[0].properties, 'isView') and item.layers[0].properties.isView
                    dont_backup = "Don't back up" in {i.title for i in item.shared_with['groups']}

                    if (not dont_backup) and (not is_view):
                        export = item.export(item.title + suffix_of_backup_content, export_type)
                        export.download(location)
                        export.delete()
                        item.unshare(['Failed to back up'])
                    else:
                        logger.info(item.title + " - Skipped export")
                except (KeyError) as e:
                    fail_count += 1
                    if fail_count >= 10:
                        quit()
                    logger.warning(item.title + " - Cannot be exported, failed backup")
                    item.share(['Failed to back up'])
                    print(e)

            item.download(location)
            item.download_metadata(location)
            with open(os.path.join(location, "timestamp.txt"), "w") as timestamp:
                timestamp.write(item_modified)
        except (FileNotFoundError, OSError, Exception) as e:
            logger.warning('Bad Path!!!!')
            item.share(['Failed to back up'])
            print(e)


def download_items(location, items):
    del_unused(location, {item.title for item in items})
    for item in items:
        download_item(os.path.join(location, clean_location(item.title)), item)


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
        download_type(os.path.join(location, clean_location(folder)), types)

starttime = time.clock()

suffix_of_backup_content = '_SourceData_ForBackup'
gis = GIS("https://www.arcgis.com", passwords.user_name, passwords.password)

for item in gis.users.get(passwords.user_name).items():
    if item.title.endswith(suffix_of_backup_content):
        item.delete()

source_users = gis.users.search()

for user in source_users:
    logger.info("Collecting item ids for {}".format(user.username))
    user_content = {}

    try:
        user_content["None"] = user.items()

        for folder in user.folders:
            user_content[folder['title']] = user.items(folder=folder['title'])

        download_user(os.path.join("Content", "Users", clean_location(user.username)), user_content)

    except RuntimeError as e:
        print(e)

commit()

if  hasattr(passwords, 'hc_ping'):
    urllib.request.urlopen(passwords.hc_ping)

logger.info('process completed in ' + str(time.clock() - starttime))
