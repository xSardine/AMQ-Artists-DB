import json
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.styles.colors import Color
from openpyxl.styles.alignment import Alignment
from youtubesearchpython import VideosSearch

# ______ General Configuration ______

# Relative path of the .json file you downloaded,
# if it's in the same folder as this script, then it's just the file name.
song_list_path = "mouretsupira_SongList.json"

# Name of the created sheet
output_file_name = "Mouretsu Pirates Anime Songs Ranking Sheet.xlsx"

# Setting to True slow down the process
# but gives you full song link when available on youtube
add_youtube_link = False

# Sheet styling Configuration
sheet_name = "Sheet1"
link_color = "1155cc"
cell_background_color = "cccccc"
border_color = "949494"
font_police = "Arial"
first_line_font_size = 10
rest_font_size = 10
# Sheet styling Configuration

# ______ General Configuration ______


def format_song(song):

    HQlink = song["sept"] if "sept" in song else song["quatre"]
    mp3_link = song["mptrois"] if "mptrois" in song else None

    return {
        "anime_name": song["Anime"],
        "type": song["Type"],
        "info": '"' + song["SongName"] + '" by ' + song["Artist"],
        "link": HQlink,
        "mp3_link": mp3_link,
    }


def create_workbook(song_list_json):

    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name

    # First line value
    ws.cell(1, 1, "ID")
    ws.cell(1, 2, "Anime Name")
    ws.cell(1, 3, "Song Type")
    ws.cell(1, 4, "Song Info")
    ws.cell(1, 5, "mp3 Links")
    ws.cell(1, 6, "Full Versions")
    ws.cell(1, 7, "Rank")

    # Insert values
    row_iter = 2
    for i, song in enumerate(song_list_json):
        print("Song #" + str(i + 1) + "/" + str(len(song_list_json)))
        song = format_song(song)
        yt_link = None
        if add_youtube_link:
            ytsearch = song["info"].replace('"', "") + " full song"
            videosSearch = VideosSearch(ytsearch, limit=1)
            results = videosSearch.result()
            yt_link = "https://www.youtube.com/watch?v=" + results["result"][0]["id"]
        ws.cell(row_iter, 2, song["anime_name"])
        ws.cell(row_iter, 3, song["type"])
        ws.cell(row_iter, 4, song["info"]).hyperlink = song["link"]
        ws.cell(row_iter, 5, "Link").hyperlink = song["mp3_link"]
        ws.cell(row_iter, 6, "Link").hyperlink = yt_link
        row_iter += 1

    # Change width of column based on longest cell value
    dims = {}
    for row in ws.rows:
        for cell in row:
            if cell.value:
                dims[cell.column_letter] = max(
                    (dims.get(cell.column_letter, 0), len(str(cell.value)))
                )
    for col, value in dims.items():
        ws.column_dimensions[col].width = value + 7

    # general style
    gray_color = Color(rgb=cell_background_color)
    gray_background = PatternFill(patternType="solid", fgColor=gray_color)

    for line in ws["A1:G" + str(row_iter - 1)]:
        for cell in line:
            cell.fill = gray_background
            cell.font = Font(size=rest_font_size, name=font_police)
            cell.alignment = Alignment(vertical="center")

    # Style for first line
    for line in ws["A1:G1"]:
        for cell in line:
            cell.font = Font(size=first_line_font_size, bold=True, name=font_police)

    # Blue color for links
    for line in ws["D2:E" + str(row_iter - 1)]:
        for cell in line:
            cell.font = Font(color=link_color)

    # Sorting property
    ws.auto_filter.ref = "A1:G" + str(row_iter - 1)

    wb.save(output_file_name)


if __name__ == "__main__":

    with open(song_list_path, encoding="utf-8") as json_file:
        song_list_json = json.load(json_file)

    create_workbook(song_list_json)
