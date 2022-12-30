from pathlib import Path
import json
import re
import os

# ______ General Configuration ______

# Set what you want to download: mp3, webm, mp4, custom
# if custom, you need to set your custom parameters further down
download_type = "mp3"

# Relative output path where your downloaded files will go
output_path = "downloaded/"

# Set anime language for filename: EN, or JP
anime_language = "JP"

# If True: it will overwrite automatically if the downloaded file name already exist
# If not: it will throw an error and go to the next song
overwrite_already_existing_name = False

# ______ General Configuration ______


# ___________ Advanced Settings ____________
# Only if download_type set to custom
# Here it is an example if you wanted to make all webm 720p (upscale 480p if not available)
custom_parameters = '-c:a copy -crf 20 -c:v libvpx-vp9 -vf "scale=-1:720"'
custom_extension = ".webm"
# what it needs to take as source ("video" = 720 or 480, "audio" = mp3)
custom_input = "video"

# If your ffmpeg isn't in the environment variable path, set the right value you need here
# If you can do "ffmpeg -h" in your terminal, then don't touch this
ffmpeg = "ffmpeg"
# ___________ Advanced Settings ____________


default_mp3_parameters = "-c:a copy"
default_mp3_extension = ".mp3"

default_webm_parameters = "-c copy -map_metadata -1 -map_chapters -1"
default_webm_extension = ".webm"

default_mp4_parameters = "-c:a aac -c:v libx264 -map_metadata -1 -map_chapters -1"
default_mp4_extension = ".mp4"


def create_file_name_Windows(songTitle, path, extension, allowance=255):
    """
    Creates a windows-compliant filename by removing all bad characters
    and maintaining the windows path length limit (which by default is 255)
    """
    allowance -= (
        len(str(path)) + 1
    )  # by default, windows is sensitive to long total paths.
    bad_characters = re.compile(r"\\|/|<|>|:|\"|\||\?|\*|&|\^|\$|" + "\0")
    return create_file_name_common(
        songTitle, path, bad_characters, extension, allowance
    )


def create_file_name_common(fileName, path, bad_characters, extension, allowance=255):
    if allowance > 255:
        allowance = 255  # on most common filesystems, including NTFS a filename can not exceed 255 characters
    # assign allowance for things that must be in the file name
    allowance -= len(extension)  # accounting for separators (-_) for .webm
    if allowance < 0:
        raise ValueError(
            """It is not possible to give a reasonable file name, due to length limitations.
        Consider changing location to somewhere with a shorter path."""
        )

    # make sure that user input doesn't contain bad characters
    fileName = bad_characters.sub("", fileName)
    print("\n\n", fileName, "\n")
    ret = ""
    for string in [fileName]:
        length = len(string)
        if allowance - length < 0:
            string = string[:allowance]
            length = len(string)
        ret += string
        allowance -= length

    ret = path + ret + extension

    return ret


def execute_command(command):
    os.system(command)


def download_songs(song_list):

    for song in song_list:

        if overwrite_already_existing_name:
            ignore_parameter = "-y"
        else:
            ignore_parameter = "-n"
            
        if anime_language == "EN":
            anime_name = song['animeENName']
        else:
            anime_name = song['animeJPName']

        file_name = f"{song['annId']} {anime_name} {song['songType']} - {song['songName']} by {song['songArtist']}"

        try:

            if download_type == "mp3":

                link = song["audio"] if "audio" in song else None

                title_key = "title"
                artist_key = "artist"
                album_key = "album"
                composer_key = "TCOM"

                artists = [artist["names"][0] for artist in song["artists"]]
                artist_metadata = "; ".join(artists)

                metadata = f"-metadata {title_key}=\"{song['songName']}\" -metadata {artist_key}=\"{artist_metadata}\" -metadata {album_key}=\"{anime_name}\""

                if song["composers"]:
                    composers = [composer["names"][0] for composer in song["composers"]]
                    composer_value = "; ".join(composers)
                    metadata += f' -metadata {composer_key}="{composer_value}"'

                if link:

                    command = f'{ffmpeg} {ignore_parameter} -i {link} {metadata} {default_mp3_parameters} "{create_file_name_Windows(file_name, output_path, default_mp3_extension)}"'

                else:

                    link = (
                        song["HQ"]
                        if "HQ" in song and song["HQ"]
                        else song["MQ"]
                        if "MQ" in song
                        else None
                    )

                    if not link:
                        raise ValueError("Warning: {file_name} is not uploaded")

                    command = f'{ffmpeg} {ignore_parameter} -i {link} -codec:a libmp3lame -b:a 320k -compression_level 7 "{create_file_name_Windows(file_name, output_path, default_mp3_extension)}"'

            elif download_type == "webm":

                link = (
                    song["HQ"]
                    if "HQ" in song and song["HQ"]
                    else song["MQ"]
                    if "MQ" in song
                    else None
                )

                if not link:
                    raise ValueError(f"Warning: {file_name} have no video uploaded")

                command = f'{ffmpeg} {ignore_parameter} -i {link} {default_webm_parameters} "{create_file_name_Windows(file_name, output_path, default_webm_extension)}"'

            elif download_type == "mp4":

                link = (
                    song["HQ"]
                    if "HQ" in song and song["HQ"]
                    else song["MQ"]
                    if "MQ" in song
                    else None
                )

                if not link:
                    raise ValueError(f"Warning: {file_name} have no video uploaded")

                command = f'{ffmpeg} {ignore_parameter} -i {link} {default_mp4_parameters} "{create_file_name_Windows(file_name, output_path, default_mp4_extension)}"'

            elif download_type == "custom":

                if custom_input == "video":

                    link = (
                        song["HQ"]
                        if "HQ" in song and song["HQ"]
                        else song["MQ"]
                        if "MQ" in song
                        else None
                    )

                    if not link:
                        raise ValueError(f"Warning: {file_name} have no video uploaded")

                    command = f'{ffmpeg} {ignore_parameter} -i {link} {custom_parameters} "{create_file_name_Windows(file_name, output_path, custom_extension)}"'

                elif custom_input == "audio":

                    link = song["audio"] if "audio" in song else None

                    if not link:
                        raise ValueError(f"Warning: {file_name} have no mp3 uploaded")

                    command = f'{ffmpeg} {ignore_parameter} -i {link} {custom_parameters} "{create_file_name_Windows(file_name, output_path, custom_extension)}"'

                else:
                    raise ValueError(
                        f"Warning: {custom_input} is not a valid value for the custom input parameter"
                    )

            else:
                raise ValueError(
                    f"Warning: {download_type} is not a valid value for the download_type parameter"
                )

            print(command)
            execute_command(command)
            print()

        except Exception as e:
            print(e)
            print(f"Failed for {link} ({file_name})")
            print()


if __name__ == "__main__":

    Path(output_path).mkdir(exist_ok=True)

    json_path = Path(".")
    json_list = list(json_path.glob("*.json"))

    for json_ in json_list:
        with open(json_, encoding="utf-8") as json_file:
            download_songs(json.load(json_file))
            exit
