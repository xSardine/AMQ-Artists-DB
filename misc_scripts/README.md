# Misc Scripts

These scripts will use the `.json` file you can download from my site to perform various actions such as creating a Party Rank Sheet automatically, or downloading every songs.

## 1.1 Requirements and dependencies

To use these scripts you will need python that you can download here: <https://www.python.org/downloads/>,
Make sure that it will make an environment variable for you when it will ask for it.

Here are the dependencies for each scripts:

- For `create_sheet_from_json.py`:

Type these in your terminal:
```
python -m pip install openpyxl
python -m pip install youtube-search-python
```

- For `download_song.py`:

You need to install ffmpeg: <https://www.ffmpeg.org/>, and set it up as an environment variable too, it is quickly explained here in the "Add ffmpeg to Windows 10 Path" section: <https://windowsloop.com/install-ffmpeg-windows-10/>

## 1.2 - Download the scripts files

To download these scripts, you need to click on the script, then `raw` on the top right, and then you can right click and `save as...`.
Place them in a folder and then place any `.json` file you downloaded in that same folder.


## 1.3 - Configuring the scripts

Once you have this, you can configure them to meet your needs. Each script start with a few lines corresponding to the configuration, which are in-between two `General Configuration` lines. If you're interested, you can also check `Advanced Settings` below that, but you probably won't need it for a basic use.

They will process any .json file that are in their folder. So make sure to move out/delete old .json file for which you have no use anymore.

The different parameters are documented within the scripts, so I won't talk about them here.