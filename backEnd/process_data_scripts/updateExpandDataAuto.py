from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pathlib import Path
from datetime import datetime
import time, json, re
import sys, os, getopt
import splitting

splitters = splitting.splitters
secondary_splitters = splitting.secondary_splitters
splitting_exception = splitting.splitting_exception


# Call Listener to get expand data and store it in a new element that selenium is waiting for
getExpandScript = """
function getPromiseExpand() {
    return new Promise((resolve) => {
        new Listener("expandLibrary questions", (payload) => {
            hiddenInput = document.createElement("div");
            hiddenInput.setAttribute("type", "hidden");
            hiddenInput.setAttribute("id", "hiddenExpand")
            hiddenInput.variable = payload
            document.getElementById("mainPage").appendChild(hiddenInput)
            resolve();
        }).bindListener()
        socket.sendCommand({
            type: "library",
            command: "expandLibrary questions"
        })
    })
}

async function waitForExpandLoaded() {
    await getPromiseExpand()
}
waitForExpandLoaded().then((result) => {
    console.log("Promise done adding new element")
})
"""


def help():
    print(
        """Usage: python updateExpandDataAuto.py [-h|--update]
            -h: show this panel
            --update: scrap AMQ expand data to update"""
    )


def main(argv):

    update = False

    try:
        opts, args = getopt.getopt(argv, "h", ["update"])
    except getopt.GetoptError:
        help()
        sys.exit(2)
    for opt, arg in opts:
        if opt == "-h":
            help()
            sys.exit()
        elif opt == "--update":
            update = True

    return update


def add_log(log):
    print(log)
    """Append given text as a new line at the end of file"""
    # Open the file in append & read mode ('a+')
    with open("updateLogs.txt", "a+", encoding="utf-8") as file_object:
        # Move read cursor to the start of file.
        file_object.seek(0)
        # If file is not empty then append '\n'
        data = file_object.read(100)
        if len(data) > 0:
            file_object.write("\n")
        # Append text at the end of file
        file_object.write(log)


def selenium_retrieve_data(amq_url, amq_username, amq_password):
    # create driver and open amq
    option = webdriver.ChromeOptions()
    option.add_argument("headless")
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=option)
    driver.get(amq_url)
    expand = None

    try:

        # Login
        driver.find_element(By.ID, "loginUsername").send_keys(amq_username)
        driver.find_element(By.ID, "loginPassword").send_keys(amq_password)
        driver.find_element(By.ID, "loginButton").click()

        # Wait few seconds to make sure page is loaded (need to find a better way)
        time.sleep(7)
        add_log("Connected to AMQ")

    finally:
        try:

            # Execute script
            driver.execute_script(getExpandScript)
            add_log("script executed, waiting for promise")

            # Wait for new element to be created and get data
            element = WebDriverWait(driver, 120).until(
                EC.presence_of_element_located((By.ID, "hiddenExpand"))
            )
            expand = element.get_property("variable")
        finally:
            driver.quit()
            return expand


def similar_song_exist(source_anime, new_song):

    for song in source_anime["songs"]:
        if song["annSongId"] == -1 and (
            song["songName"] == new_song["songName"]
            or song["songArtist"] == new_song["songArtist"]
        ):
            return True
    return False


def format_new_song(artist_database, song):
    new_song = {
        "annSongId": song["annSongId"],
        "songType": song["type"],
        "songNumber": song["number"],
        "songName": song["name"],
        "songArtist": song["artist"],
        "links": {
            "HQ": song["examples"]["720"] if "720" in song["examples"] else None,
            "MQ": song["examples"]["480"] if "480" in song["examples"] else None,
            "audio": song["examples"]["mp3"] if "mp3" in song["examples"] else None,
        },
    }
    splitted_artist = split_artist(new_song["songArtist"])
    new_song["artist_ids"] = [
        [artist_id, -1]
        for artist_id in get_artist_id_list(artist_database, splitted_artist)
    ]
    new_song["composer_ids"] = []
    new_song["arranger_ids"] = []
    return new_song


def split_artist(artist):

    # if forced exception splitting do it:
    if artist in splitting_exception.keys():
        return splitting_exception[artist]

    # else
    new_list = []
    # split on initial splitter
    for art in re.split(splitters, artist):
        # for each splitted artist, if it's forced splitting exception, do it
        if art in splitting_exception.keys():
            new_list += splitting_exception[art]
        # else split on secondary splitters (splitters which often are contained in a single artist)
        else:
            new_list += re.split(secondary_splitters, art)
    return new_list


def add_new_artist_to_DB(artist_database, artist, id):
    if str(id) not in artist_database:
        artist_database[id] = {
            "names": [artist],
            "groups": [],
            "members": [],
            "vocalist": True,
            "composer": False,
        }


def get_artist_id(artist_database, artist):

    ids = []
    for id in artist_database.keys():
        if artist in artist_database[id]["names"]:
            ids.append(id)

    # if no IDs found, create new id
    if not ids:
        new_id = int(list(artist_database.keys())[-1]) + 1
        add_log(f"<CHECK> NEW ARTIST: {artist}")
        add_new_artist_to_DB(artist_database, artist, new_id)
        return new_id
    # else default to first ID and throw a TODO if multiple IDs found
    if len(ids) > 1:
        add_log(
            f"<TODO> '{artist}' has is linked to multiple IDs: {ids}, defaulting to {ids[0]}"
        )
    return ids[0]


def get_artist_id_list(artist_database, artist_list):

    artist_id_list = []

    for artist in artist_list:
        artist_id_list.append(int(get_artist_id(artist_database, artist)))

    return artist_id_list


def update_data_with_expand(song_database, artist_database, expand_data):

    for update_anime in expand_data:
        for update_song in update_anime["songs"]:
            flag_anime_found = False
            flag_song_found = False
            for source_anime in song_database:

                if source_anime["annId"] != update_anime["annId"]:
                    continue

                flag_anime_found = True

                if source_anime["animeExpandName"] != update_anime["name"]:
                    # add_log(f"UPDATE animeExpandName | {source_anime['animeExpandName']} -> {update_anime['name']}")
                    source_anime["animeExpandName"] = update_anime["name"]

                for i, source_song in enumerate(source_anime["songs"]):
                    if source_song["annSongId"] != update_song["annSongId"]:
                        continue
                    flag_song_found = True

                    if source_song["songType"] != update_song["type"]:
                        add_log(
                            f"UPDATE songType | {source_song['annSongId']} {source_song['songType']} -> {update_song['type']}"
                        )
                        source_song["songType"] = update_song["type"]

                    if source_song["songNumber"] != update_song["number"]:
                        add_log(
                            f"UPDATE songNumber | {source_song['annSongId']} {source_song['songNumber']} -> {update_song['number']}"
                        )
                        source_song["songNumber"] = update_song["number"]

                    if source_song["songName"] != update_song["name"]:
                        add_log(
                            f"UPDATE songName | {source_song['annSongId']} {source_song['songName']} -> {update_song['name']}"
                        )
                        source_song["songName"] = update_song["name"]

                    if source_song["songArtist"] != update_song["artist"]:
                        add_log(
                            f"UPDATE songArtist | {source_song['annSongId']} {source_song['songArtist']} -> {update_song['artist']}"
                        )
                        source_song["songArtist"] = update_song["artist"]
                    if (
                        "720" in update_song["examples"]
                        and "openings.moe" not in update_song["examples"]["720"]
                        and (
                            "HQ" not in source_song["links"]
                            or source_song["links"]["HQ"]
                            != update_song["examples"]["720"]
                        )
                    ):
                        # add_log(f"UPDATE 720 SONG LINKS | {source_song['annSongId']} {source_song['links']['HQ'] if 'HQ' in source_song['links'] else None} -> {update_song['examples']['720']}")
                        source_song["links"]["HQ"] = update_song["examples"]["720"]
                    if (
                        "480" in update_song["examples"]
                        and "openings.moe" not in update_song["examples"]["480"]
                        and (
                            "MQ" not in source_song["links"]
                            or source_song["links"]["MQ"]
                            != update_song["examples"]["480"]
                        )
                    ):
                        # add_log(f"UPDATE 480 SONG LINKS | {source_song['annSongId']} {source_song['links']['MQ'] if 'MQ' in source_song['links'] else None} -> {update_song['examples']['480']}")
                        source_song["links"]["MQ"] = update_song["examples"]["480"]
                    if "mp3" in update_song["examples"] and (
                        "audio" not in source_song["links"]
                        or source_song["links"]["audio"]
                        != update_song["examples"]["mp3"]
                    ):
                        # add_log(f"UPDATE mp3 SONG LINKS | {source_song['annSongId']} {source_song['links']['audio'] if 'audio' in source_song['links'] else None} -> {update_song['examples']['mp3']}")
                        source_song["links"]["audio"] = update_song["examples"]["mp3"]
                    break

                if flag_song_found:
                    continue

                # If anime found but song not found
                new_song = format_new_song(artist_database, update_song)
                source_anime["songs"].append(new_song)
                log = f"ADD SONG TO {source_anime['animeExpandName']}"
                if similar_song_exist(source_anime, new_song):
                    add_log(f"<TODO> {log} | {new_song}")
                else:
                    add_log(f"{log} | {new_song}")
                break

            # if anime not found
            if not flag_anime_found:
                songs = []
                add_log(f"ADD ANIME | {update_anime['annId']} - {update_anime['name']}")
                for song in update_anime["songs"]:
                    new_song = format_new_song(artist_database, song)
                    add_log(f"ADD SONG TO NEW ANIME | {new_song}")
                    songs.append(new_song)
                song_database.append(
                    {
                        "annId": update_anime["annId"],
                        "animeExpandName": update_anime["name"],
                        "songs": songs,
                    }
                )


def process(update):
    AMQ_USERNAME = "purplepinapple9"
    AMQ_PWD = "purplepinapple9"

    expand_data_path = Path("../app/data/expand_database.json")
    song_database_path = Path("../app/data/song_database.json")
    artist_database_path = Path("../app/data/artist_database.json")

    with open(song_database_path, encoding="utf-8") as json_file:
        song_database = json.load(json_file)
    with open(artist_database_path, encoding="utf-8") as json_file:
        artist_database = json.load(json_file)

    if update:

        expand_data = selenium_retrieve_data(
            "https://animemusicquiz.com/", AMQ_USERNAME, AMQ_PWD
        )
        expand_data = expand_data["questions"]

        with open(expand_data_path, "w", encoding="utf-8") as outfile:
            json.dump(expand_data, outfile)

    else:
        with open(expand_data_path, encoding="utf-8") as json_file:
            expand_data = json.load(json_file)

    update_data_with_expand(song_database, artist_database, expand_data)

    with open(song_database_path, "w", encoding="utf-8") as outfile:
        json.dump(song_database, outfile)
    with open(artist_database_path, "w", encoding="utf-8") as outfile:
        json.dump(artist_database, outfile)

    os.system("convert_to_SQL.py")

    now = datetime.now()

    add_log("Update Done - " + now.strftime("%d/%m/%Y %H:%M:%S"))
    # os.system(
    #    "scp ../app/data/Enhanced-AMQ-Database.db anthony@anisongdb.com:~/AMQ-Artists-DB/backEnd/app/data/Enhanced-AMQ-Database.db"
    # )
    print("Update sent")


if __name__ == "__main__":
    # schedule(process, interval=(1 / 10) * 60 * 60)
    # run_loop()
    update = main(sys.argv[1:])
    process(update)
