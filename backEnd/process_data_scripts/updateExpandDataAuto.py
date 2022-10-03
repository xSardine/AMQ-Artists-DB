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
from updatersWrapper import utils

splitters = splitting.splitters
secondary_splitters = splitting.secondary_splitters
splitting_exception = splitting.splitting_exception


def check_validity(song_database, splitting_exception):

    is_valid = True

    splitexcep = [exception[0] for exception in splitting.splitting_exception_list]
    for i, exception in enumerate(splitexcep):
        for exception2 in splitexcep[i + 1 :]:
            if exception == exception2:
                print(f"WARNING: duplicate for {exception}")
                is_valid = False
    print("Checking Duplicate Done\n")

    for exception in splitting_exception:
        flag_valid = False
        flag_maybe_valid = False
        for anime in song_database:
            for song in anime["songs"]:
                if song["songArtist"] == exception:
                    flag_valid = True
                elif exception in song["songArtist"]:
                    flag_maybe_valid = True
        if not flag_valid:
            if flag_maybe_valid:
                print("Split Exception", exception, "MIGHT NOT BE VALID")
            else:
                print(
                    "WARNING: Split Exception",
                    exception,
                    "IS NOT A VALID EXCEPTION: WARNING",
                )
                is_valid = False

    print("done checking")

    return is_valid


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
    """Append given text as a new line at the end of file"""
    print(log)
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
        time.sleep(2)
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


def format_new_song(song_database, artist_database, song):
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
    add_log(f"{new_song['songArtist']} -> {splitted_artist}")

    new_song["artist_ids"] = []
    for artist_id in get_artist_id_list(
        song_database, artist_database, splitted_artist
    ):
        line_up_id = -1
        if artist_database[artist_id]["members"]:
            line_up_id = 0
        new_song["artist_ids"].append([artist_id, line_up_id])
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


def get_artist_id_list(song_database, artist_database, artist_list):

    artist_id_list = []

    for artist in artist_list:
        artist_id_list.append(
            utils.get_artist_id(
                song_database,
                artist_database,
                artist,
                not_exist_ok=True,
                exact_match=True,
            )
        )

    return artist_id_list


def update_artist_names(song_database, artist_database, old_name, new_name):

    old_names = split_artist(old_name)
    new_names = split_artist(new_name)

    if len(old_names) != len(new_names):
        add_log(f"<TODO IMPORTANT> {old_name} → {new_name}  CANT PROCESS\n")
        return

    for old, new in zip(old_names, new_names):
        if old == new:
            continue

        artist_id = utils.get_artist_id(song_database, artist_database, old)

        if new not in artist_database[artist_id]["names"]:
            add_log(f"+{new} ← {artist_id}")
            artist_database[artist_id]["names"].append(new)

        nb_songs = 0
        for anime in song_database:
            for song in anime["songs"]:
                if artist_id not in [id[0] for id in song["artist_ids"]]:
                    continue
                if old in song["songArtist"]:
                    nb_songs += 1

        if nb_songs <= 1:
            add_log(f"-{old} ← {artist_id}")
            artist_database[artist_id]["names"].pop(
                artist_database[artist_id]["names"].index(old)
            )
        else:
            add_log(f"<CHECK> Keeping {old} in {artist_id}")

        add_log(", ".join(artist_database[artist_id]["names"]))
        add_log("")


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
                        source_song["songName"] = update_song["name"]

                    if source_song["songArtist"] != update_song["artist"]:
                        add_log(
                            f"UPDATE songArtist | {source_song['annSongId']} {source_song['songArtist']} -> {update_song['artist']}"
                        )
                        update_artist_names(
                            song_database,
                            artist_database,
                            source_song["songArtist"],
                            update_song["artist"],
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
                add_log(
                    f"\n{source_anime['animeExpandName']} : {update_song['name']} by {update_song['artist']}"
                )
                new_song = format_new_song(song_database, artist_database, update_song)
                source_anime["songs"].append(new_song)
                if similar_song_exist(source_anime, new_song):
                    add_log(f"\n<TODO> {new_song}\n\n")
                else:
                    add_log(f"{new_song}\n")
                break

            # if anime not found
            if not flag_anime_found:
                songs = []
                add_log(f"ADD ANIME | {update_anime['annId']} - {update_anime['name']}")
                for song in update_anime["songs"]:
                    add_log(f"{song['name']} by {song['artist']}")
                    new_song = format_new_song(song_database, artist_database, song)
                    add_log(f"{new_song}\n")
                    songs.append(new_song)
                song_database.append(
                    {
                        "annId": update_anime["annId"],
                        "animeExpandName": update_anime["name"],
                        "songs": songs,
                        "alt_names": [],
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

    is_valid = check_validity(song_database, splitting_exception)
    if not is_valid:
        print("WARNING - ERRORS IN THE DATABASE")
    print()

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

    validation_message = "Do you want to confirm this update ?\n"
    validation = utils.ask_validation(validation_message)

    if not validation:
        print("User Cancelled")
        return

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
