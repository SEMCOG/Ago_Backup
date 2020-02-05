# ArcGIS Online (AGO) Backup Process

## Overview
The process was established to ensure that data stored on AGO could be retrieved in the event that staff accidentally deletes content or if a critical error occurs.  The process was designed to scan all of the content on SEMCOG’s account and download/extract the data to a location on SEMCOG’s network. It organizes the content based on the following structure:

content\user\ago_folder\content_type\item_folder\item

Each item folder also contains a timestamp.txt which is used to determine if the data has changed on AGO. Each time the process is ran it checks the data on AGO and downloads any data that is new, or data that has been modified. It also deletes from our archive any data that has been deleted. 


### Requirements
+ Python3.x (comes with ArcGIS Pro)
+ [ArcGIS API for Python](https://developers.arcgis.com/python/guide/install-and-set-up/) (comes with ArcGIS Pro)
+ [git](https://git-scm.com/download/win)


## Setup

Once you extract the files from here, create a `Content` folder in the script directory and initialize a git repository (in command prompt, run `git init`) to store the changes to your AGO content. Then create a passwords.py file in the script directory and store your AGO user name and password like:

```python
user_name= "..."
password = "..."
# if you are using Healthchecks.io
hc_ping = "https://hc-ping.com/..."
```

Now you are setup and you can run the ago_backup.py script with the version of Python that has the ArcGIS API for Python installed. We found ours at: `C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe`


## General Notes:

### git
The process uses git to keep track of historical changes and “commits” to a git repository every time it is ran. Any content that is backed up using this process will be saved in the git repository. This means that even if a file is deleted or has incorrect edits made can be restored by looking back in the git history.

### Healthchecks.io
[Healthchecks.io](https://www.Healthchecks.io) is a service to email you if the script fails to run. Especially helpful if you set this script up to run automatically.

### Feature Services 
Use a tag of `ago_view` on any content that you wish this script to ignore. This is particularly useful for when the size of a dataset is too big to be exported. 

### Code Attachments
By default, some content like Web App Builder apps, will have empty Code Attachments alongside them. The download method fails when it gets to this item. In order for the script to run without failing, we need to ignore Code Attachments. 
