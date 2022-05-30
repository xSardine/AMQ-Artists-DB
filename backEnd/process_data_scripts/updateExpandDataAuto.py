from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
from pathlib import Path
import time
import os

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

    try:

        # Login
        driver.find_element(By.ID, "loginUsername").send_keys(amq_username)
        driver.find_element(By.ID, "loginPassword").send_keys(amq_password)
        driver.find_element(By.ID, "loginButton").click()

        # Wait few seconds to make sure page is loaded (need to find a better way)
        time.sleep(8)
        print("Connected to AMQ")

    finally:
        try:

            # Execute script
            driver.execute_script(getExpandScript)
            print("script executed, waiting for promise")

            # Wait for new element to be created and get data
            element = WebDriverWait(driver, 120).until(
                EC.presence_of_element_located((By.ID, "hiddenExpand"))
            )
            expand = element.get_property("variable")
        finally:
            driver.quit()
            return expand


def similar_song_exist(source_anime, update_song):

    for song in source_anime["songs"]:
        if song["annSongId"] == -1 and (
            song["name"] == update_song["name"]
            or song["artist"] == update_song["artist"]
        ):
            return True
    return False


def update_data_with_expand(source_data, expand_data):

    for update_anime in expand_data:
        for update_song in update_anime["songs"]:
            flag_anime_found = False
            flag_song_found = False
            for source_anime in source_data:

                if source_anime["annId"] != update_anime["annId"]:
                    continue

                flag_anime_found = True

                if source_anime["name"] != update_anime["name"]:
                    print(
                        f"UPDATE ANIME NAME | {source_anime['name']} -> {update_anime['name']}"
                    )
                    source_anime["name"] = update_anime["name"]

                for i, source_song in enumerate(source_anime["songs"]):
                    if source_song["annSongId"] != update_song["annSongId"]:
                        continue
                    flag_song_found = True
                    if source_song["name"] != update_song["name"]:
                        print(
                            f"UPDATE SONG NAME | {source_song['annSongId']} {source_song['name']} -> {update_song['name']}"
                        )
                        source_song["name"] = update_song["name"]
                    if source_song["artist"] != update_song["artist"]:
                        print(
                            f"UPDATE SONG ARTIST | {source_song['annSongId']} {source_song['artist']} -> {update_song['artist']}"
                        )
                        source_song["artist"] = update_song["artist"]
                    if source_song["examples"] != update_song["examples"]:
                        print(
                            f"UPDATE SONG LINKS | {source_song['annSongId']} {source_song['examples']} -> {update_song['examples']}"
                        )
                        source_song["examples"] = update_song["examples"]
                    break

                if flag_song_found:
                    continue

                # If anime found but song not found
                update_song.pop("versions")
                source_anime["songs"].append(update_song)
                if similar_song_exist(source_anime, update_song):
                    print(f"ADD SONG - HIGH THREAT | {update_song}")
                elif -1 in [song["annSongId"] for song in source_anime["songs"]]:
                    print(f"ADD SONG - LOW THREAT | {update_song}")
                else:
                    print(f"ADD SONG | {update_song}")
                break

            # if anime not found
            if not flag_anime_found:
                songs = []
                print(f"ADD ANIME | {update_anime['annId']} - {update_anime['name']}")
                for song in update_anime["songs"]:
                    song.pop("versions")
                    print(f"ADD SONG TO NEW ANIME | {song}")
                    songs.append(song)
                source_data.append(
                    {
                        "annId": update_anime["annId"],
                        "name": update_anime["name"],
                        "songs": songs,
                    }
                )
    return source_data


if __name__ == "__main__":

    USERNAME = "purplepinapple9"
    PWD = "purplepinapple9"
    SOURCE_FILE_PATH = Path("../data/preprocessed/FusedExpand.json")

    expand_data = selenium_retrieve_data("https://animemusicquiz.com/", USERNAME, PWD)
    expand_data = expand_data["questions"]

    if not expand_data:
        exit("ERROR WARNING /!\ Couldn't Retrieve Expand: It is undefined")

    with open(SOURCE_FILE_PATH, encoding="utf-8") as json_file:
        source_data = json.load(json_file)

    updated_data = update_data_with_expand(source_data, expand_data)

    with open(SOURCE_FILE_PATH, "w", encoding="utf-8") as outfile:
        json.dump(updated_data, outfile)

    os.chdir("process_artists")
    os.system("map1_artist_id.py")
    os.system("map2_group_id.py")
    os.system("map3_alt_groups.py")
    os.system("map4_same_name.py")
    os.system("map5_member_of.py")
    os.system("map6_composers.py")
    os.system("convert_to_SQL.py")
    # os.system("./process_data.sh")
