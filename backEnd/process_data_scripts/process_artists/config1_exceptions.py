# Splitting Config

"""
exception collected over the time so that I can re-build it from scratch
"""

splitters = " VS | vs | & | , |, | featuring\. | Featuring\. | featuring | Featuring | feat\. | feat\.|feat\. |feat\.| ft\. | ft\.|ft\. |ft\.| x | × | with |＆| / |/"
secondary_splitters = "・|& | &|&| ,|,| ×|× |×"

splitting_exception_list = [
    (
        "Me to Humbert Humbert",
        (
            "Me",
            "Humbert Humbert",
        ),
    ),
    (
        "POLYSICS with Seiya Yamasaki (Kyuuso Nekokami)",
        (
            "POLYSICS",
            "Seiya Yamasaki",
        ),
    ),
    (
        "Tenshou Gakuen Seito・Kyoushi Ichidou",
        (
            "Tenshou Gakuen Seito Ichidou",
            "Tenshou Gakuen Kyoushi Ichidou",
        ),
    ),
    ("JO☆STARS~TOMMY, Coda, JIN~", ("JO☆STARS",)),
    (
        "HoneyWorks meets YURiCa/Hanatan",
        (
            "HoneyWorks",
            "YURiCa/Hanatan",
        ),
    ),
    (
        "ReyMagtoto-NonoyTan",
        (
            "RAY MAGTOTO",
            "NONOY TAN",
        ),
    ),
    ("OxT", ("OxT",)),
    ("Hironobu Kageyama & BROADWAY", ("Hironobu Kageyama & BROADWAY",)),
    ("Fear, and Loathing in Las Vegas", ("Fear, and Loathing in Las Vegas",)),
    (
        "Kishida Kyoudan &THE Akeboshi Rockets",
        ("Kishida Kyoudan &THE Akeboshi Rockets",),
    ),
    (
        "angela Presents/Shoko Nakagawa",
        (
            "angela",
            "Shoko Nkagawa",
        ),
    ),
    ("G・GRIP", ("G・GRIP",)),
    (
        "Aozu + Cap to Bin",
        (
            "Aozu",
            "Cap to Bin",
        ),
    ),
    ("Hello, Happy World!", ("Hello, Happy World!",)),
    (" G・GRIP", ("G・GRIP",)),
    ("HIKAKIN & SEIKIN", ("HIKAKIN & SEIKIN",)),
    ("Swing・Cats", ("Swing・Cats",)),
    ("F・MAP", ("F・MAP",)),
    ("a・chi-a・chi", ("a・chi-a・chi",)),
    ("hide with Spread Beaver", ("hide with Spread Beaver",)),
    ("A・Times", ("A・Times",)),
    (
        "SAY・S & Nintama Family",
        (
            "SAY・S",
            "Nintama Family",
        ),
    ),
    (
        "SAY・S and Nintama Family",
        (
            "SAY・S",
            "Nintama Family",
        ),
    ),
    ("R・O・N", ("R・O・N",)),
    ("Ja・Ja", ("Ja・Ja",)),
    ("B・B Girls", ("B・B Girls",)),
    ("G・P・S", ("G・P・S",)),
    ("M・A・O", ("M・A・O",)),
    ("Clover×Clover", ("Clover×Clover",)),
    ("LIP×LIP", ("LIP×LIP",)),
    ("Gothic×Luck", ("Gothic×Luck",)),
    ("High×Joker", ("High×Joker",)),
    ("RhymeTube×Odori Foot Works", ("RhymeTube×Odori Foot Works",)),
    ("salyu × salyu", ("salyu × salyu",)),
    ("Daisy×Daisy", ("Daisy×Daisy",)),
    ("SKET×Sketch", ("SKET×Sketch",)),
    ("kanon×kanon", ("kanon×kanon",)),
    ("DIVA×DIVA", ("DIVA×DIVA",)),
    ("sister×sisters", ("sister×sisters",)),
    ("Teikoku Kageki-dan・Hana-gumi", ("Teikoku Kageki-dan・Hana-gumi",)),
    ("nana×nana", ("nana×nana",)),
    ("U×Mishi", ("U×Mishi",)),
    ("r.o.r/s", ("r.o.r/s",)),
    ("can/goo", ("can/goo",)),
    ("Petit Rabbit's with beans", ("Petit Rabbit's with beans",)),
    (
        "NAMI with Shige×2＆S/N",
        (
            "NAMI",
            "Shige×2",
            "S/N",
        ),
    ),
    ("DISH//", ("DISH//",)),
    ("ON/OFF", ("ON/OFF",)),
    ("S/mileage", ("S/mileage",)),
    ("Konnichiwa\(^o^)/Kirarinbo☆Harry!!!", ("Konnichiwa\(^o^)/Kirarinbo☆Harry!!!",)),
    ("Sol/Lull BOB", ("Sol/Lull BOB",)),
    ("Kisu Koide (PANDA 1/2)", ("Kisu Koide (PANDA 1/2)",)),
    ("+α/Alfakyun.", ("+α/Alfakyun.",)),
    ("H-el-ical//", ("H-el-ical//",)),
    ("22/7", ("22/7",)),
    (
        "Becky (& PokePark KIDS Gasshou-dan)",
        (
            "Becky",
            "PokePark KIDS Gasshou-dan",
        ),
    ),
    (
        "Masayoshi Ooishi (feat.Riria.)",
        (
            "Masayoshi Ooishi",
            "Riria.",
        ),
    ),
    (
        "Basement Jaxx (feat. Lisa Kekaula)",
        (
            "Basement Jaxx",
            "Lisa Kekaula",
        ),
    ),
    (
        "Moe Shop (feat.TORIENA)",
        (
            "Moe Shop",
            "TORIENA",
        ),
    ),
    (
        "TO-MAS feat. M・A・O and Minami Takahashi",
        (
            "TO-MAS",
            "M・A・O",
            "Minami Takahashi",
        ),
    ),
    (
        "Unsho Ishizuka to Pokemon Kids",
        (
            "Unsho Ishizuka",
            "Pokemon Kids",
        ),
    ),
    (
        "Mori no Ki Jidou Gasshou-dan to Sono Otomodachi",
        (
            "Mori no Ki Jidou Gasshou-dan",
            "Sono Otomodachi",
        ),
    ),
    (
        "Sogeking to Shounen Shoujo Gasshou-dan",
        (
            "Sogeking",
            "Shounen Shoujo Gasshou-dan",
        ),
    ),
    (
        "Pupa Mucha to Muchachiita to Etsuko Kozakura to Mayuko Omimura to Akiko Suzuki to Rie Kugimiya",
        (
            "Pupa Mucha",
            "Muchachiita",
            "Etsuko Kozakura",
            "Mayuko Omimura",
            "Akiko Suzuki",
            "Rie Kugimiya",
        ),
    ),
    ("PSY・S", ("PSY・S",)),
    (
        "Kenji Ohtsuki to Emmanuel 5",
        (
            "Kenji Ohtsuki",
            "Emmanuel 5",
        ),
    ),
    (
        "Eri Itou to Mori no Ki Jidou Gasshou-dan",
        (
            "Eri Itou",
            "Mori no Ki Jidou Gasshou-dan",
        ),
    ),
    (
        "CHEMISTRY meets m-flo",
        (
            "CHEMISTRY",
            "m-flo",
        ),
    ),
    (
        "m-flo\u2665DOPING PANDA",
        (
            "m-flo",
            "DOPING PANDA",
        ),
    ),
    ("Milan Himemiya to Chocolate Rockers", ("Milan Himemiya to Chocolate Rockers",)),
    (
        "Naomi Tamura to Himawari Gasshou-dan",
        (
            "Naomi Tamura",
            "Himawari Gasshou-dan",
        ),
    ),
    (
        "Ushio to Ichiro",
        (
            "Ushio",
            "Ichiro",
        ),
    ),
    (
        "Osamu Yamada to Hello Nights",
        (
            "Osamu Yamada",
            "Hello Nights",
        ),
    ),
    (
        "LaSalle Ishii to Kochikame Win Gashou-dan",
        ("LaSalle Ishii", "Kochikame Win Gashou-dan"),
    ),
    (
        "Mitsuko Horie to Angel '03",
        (
            "Mitsuko Horie",
            "Angel '03",
        ),
    ),
    (
        "SawanoHiroyuki[nZk]:Junki Kono & Sho Yonashiro (JO1)",
        ("SawanoHiroyuki[nZk]", "Junki Kono", "Sho Yonashiro"),
    ),
    (
        "Haruna Ikezawa to Kouki Miyata",
        (
            "Haruna Ikezawa",
            "Kouki Miyata",
        ),
    ),
    (
        "Osamu Minagawa to Hibari Jidou Gasshou-dan",
        ("Osamu Minagawa", "Hibari Jidou Gasshou-dan"),
    ),
    (
        "Seiichi Yamamoto to Fushigi Robot",
        (
            "Seiichi Yamamoto",
            "Fushigi Robot",
        ),
    ),
    (
        "Akiko Kanazawa to Soichi Terada",
        (
            "Akiko Kanazawa",
            "Soichi Terada",
        ),
    ),
    (
        "Masaaki Endoh to Three G's 2005",
        (
            "Masaaki Endoh",
            "Three G's 2005",
        ),
    ),
    (
        "My Melodies to Maryland no Nakama-tachi",
        (
            "My Melodies",
            "Maryland no Nakama-tachi",
        ),
    ),
    (
        "Yasushi Nakanishi and Chikako Sawada",
        (
            "Yasushi Nakanishi",
            "Chikako Sawada",
        ),
    ),
    (
        "Kenji Ohtsuki to Fumihiko Kitsutaka",
        (
            "Kenji Ohtsuki",
            "Fumihiko Kitsutaka",
        ),
    ),
    (
        "Kana Ueda to Yukai na Nakama-tachi",
        (
            "Kana Ueda",
            "Yukai na Nakama-tachi",
        ),
    ),
    (
        "Kenji Ohtsuki to Zetsubou Shoujo-tachi",
        (
            "Kenji Ohtsuki",
            "Zetsubou Shoujo-tachi",
        ),
    ),
    (
        "ROLLY to Zetsubou Shoujo-tachi",
        (
            "ROLLY",
            "Zetsubou Shoujo-tachi",
        ),
    ),
    (
        "Ayano Tsuji to BEAT CRUSADERS",
        (
            "Ayano Tsuji",
            "BEAT CRUSADERS",
        ),
    ),
    (
        "Ayumi Tsunematsu to Kodomo-tachi",
        (
            "Ayumi Tsunematsu",
            "Kodomo-tachi",
        ),
    ),
    (
        "Kenji Ohtsuki to Zetsubou Shoujo-tachi feat. Rap-bit",
        (
            "Kenji Ohtsuki",
            "Zetsubou Shoujo-tachi",
            "Rap-bit",
        ),
    ),
    ("Athena & Robikerottsu", ("Athena & Robikerottsu",)),
    (
        "Saori Hayami to SeiVi-tai",
        (
            "Saori Hayami",
            "SeiVi-tai",
        ),
    ),
    ("Tamiya Terashima (Rentrak Japan)", ("Tamiya Terashima",)),
    (
        "Mikako Komatsu to Kana Hanazawa",
        (
            "Mikako Komatsu",
            "Kana Hanazawa",
        ),
    ),
    (
        "Masaaki Endoh to Moon Riders",
        (
            "Masaaki Endoh",
            "Moon Riders",
        ),
    ),
    (
        "Hajime Hana to Crazy Cats",
        (
            "Hajime Hana",
            "Crazy Cats",
        ),
    ),
    (
        "Ichirou Mizuki to Tokusatsu",
        (
            "Ichirou Mizuki",
            "Tokusatsu",
        ),
    ),
    (
        "FROGMAN to Red Chili Gasshou-dan",
        (
            "FROGMAN",
            "Red Chili Gasshou-dan",
        ),
    ),
    (
        "Yumiko Kobayashi to F-shigi na Nakama-tachi",
        (
            "Yumiko Kobayashi",
            "F-shigi na Nakama-tachi",
        ),
    ),
    (
        "Kanako Miyamoto to Young Fresh",
        (
            "Kanako Miyamoto",
            "Young Fresh",
        ),
    ),
    (
        "Kana Asumi to Sakebu Jigoku-tai",
        (
            "Kana Asumi",
            "Sakebu Jigoku-tai",
        ),
    ),
    (
        "Asuka Nishi to Yukai na Nakama-tachi",
        (
            "Asuka Nishi",
            "Yukai na Nakama-tachi",
        ),
    ),
    (
        "Misato Fukuen, Asami Tano, Hisako Kanemoto, Marina Inoue and Chinami Nishimura",
        (
            "Misato Fukuen",
            "Asami Tano",
            "Hisako Kanemoto",
            "Marina Inoue",
            "Chinami Nishimura",
        ),
    ),
    (
        "Velvet.kodhy to Velvet.kodhy to μ to μ",
        (
            "Velvet.kodhy",
            "μ",
        ),
    ),
    (
        "Melori to Cocotama Five",
        (
            "Melori",
            "Cocotama Five",
        ),
    ),
    (
        "Junji Majima to Youkai Taiji Sentai",
        (
            "Junji Majima",
            "Youkai Taiji Sentai",
        ),
    ),
    (
        "Hajime Akira to Tsukumo-chan",
        (
            "Hajime Akira",
            "Tsukumo-chan",
        ),
    ),
    (
        "Hyoutei Eternity to Rikkai Young Kan",
        (
            "Hyoutei Eternity",
            "Rikkai Young Kan",
        ),
    ),
    (
        "Hyoutei Setsunati to Rikkai Kai Shihan",
        (
            "Hyoutei Setsunati",
            "Rikkai Kai Shihan",
        ),
    ),
    (
        "Junichi Suwabe to Sachiko Nagai",
        (
            "Junichi Suwabe",
            "Sachiko Nagai",
        ),
    ),
    (
        "15-sai to Seiko Oomori",
        (
            "15-sai",
            "Seiko Oomori",
        ),
    ),
    (
        "Kaede+Cheek Fairy",
        (
            "Kaede",
            "Cheek Fairy",
        ),
    ),
    (
        "Kiyoshirou Imawano+CHAR",
        (
            "Kiyoshirou Imawano",
            "CHAR",
        ),
    ),
    (
        'Hiroshi Kakizaki + "r" Project',
        (
            "Hiroshi Kakizaki",
            '"r" Project',
        ),
    ),
    (
        "Pokemon Kids & Unshou Ishizuka (+Ikue Ootani)",
        (
            "Pokemon Kids",
            "Unshou Ishizuka",
            "Ikue Ootani",
        ),
    ),
    (
        "refio + Haruka Shimotsuki",
        (
            "refio",
            "Haruka Shimotsuki",
        ),
    ),
    (
        "Pokemon Kids (+Ikue Ootani)",
        (
            "Pokemon Kids",
            "Ikue Ootani",
        ),
    ),
    (
        "Ichiro Mizuki & Apple Pie + The 4-B's",
        (
            "Ichiro Mizuki",
            "Apple Pie",
            "The 4-B's",
        ),
    ),
    (
        "Gokujou Seitokai Yuugeki+Sharyoubu",
        (
            "Gokujou Seitokai Yuugeki",
            "Sharyoubu",
        ),
    ),
    (
        "Mahora Gakuen Chuutoubu 3-A + Rina Satou",
        (
            "Mahora Gakuen Chuutoubu 3-A",
            "Rina Satou",
        ),
    ),
    ("SERENON with K", ("SERENON with K",)),
    (
        "Koji Yusa+Yuuichi Nakamura+Kishou Taniyama",
        ("Koji Yusa", "Yuuichi Nakamura", "Kishou Taniyama"),
    ),
    (
        "T-Pistonz+KMC",
        (
            "T-Pistonz",
            "KMC",
        ),
    ),
    (
        "Kanae Itou+Rie Kugimiya+Yuuko Gotou",
        (
            "Kanae Itou",
            "Rie Kugimiya",
            "Yuuko Gotou",
        ),
    ),
    (
        "Rie Kugimiya+Yuuko Gotou+Kanae Itou",
        (
            "Rie Kugimiya",
            "Yuuko Gotou",
            "Kanae Itou",
        ),
    ),
    (
        "Yuuko Gotou+Rie Kugimiya+Kanae Itou",
        (
            "Yuuko Gotou",
            "Rie Kugimiya",
            "Kanae Itou",
        ),
    ),
    (
        "Junji Ishiwatari & Yoshinori Sunahara + Etsuko Yakushimaru",
        (
            "Junji Ishiwatari",
            "Yoshinori Sunahara",
            "Etsuko Yakushimaru",
        ),
    ),
    (
        "Masayoshi Minoshima+REDALiCE feat.ayami",
        (
            "Masayoshi Minoshima",
            "REDALiCE",
            "ayami",
        ),
    ),
    (
        "Melissa Hutchison and Alicyn Packard",
        (
            "Melissa Hutchison",
            "Alicyn Packard",
        ),
    ),
    (
        "DJ mash + Rinku with VJ Only",
        ("DJ mash", "Rinku", "VJ Only"),
    ),
    (
        "Dream5+Burii Taichou",
        (
            "Dream5",
            "Burii Taichou",
        ),
    ),
    (
        "T-Pistonz+KMZ with Little Blue boX",
        (
            "T-Pistonz",
            "KMZ",
            "Little Blue boX",
        ),
    ),
    (
        "m-flo+daoko",
        (
            "m-flo",
            "daoko",
        ),
    ),
    (
        "SoLaMiDressing+Falulu",
        (
            "SoLaMiDressing",
            "Falulu",
        ),
    ),
    (
        "SAINTS+SoLaMiDressing",
        (
            "SAINTS",
            "SoLaMiDressing",
        ),
    ),
    (
        "Kaede Hondo with Cocotama9 + Ayaka Nanase",
        (
            "Kaede Hondo",
            "Cocotama9",
            "Ayaka Nanase",
        ),
    ),
    (
        "HoneyWorks meets Sayuringo Gundan + Manatsu-san Respect Gundan from Nogizaka46",
        (
            "HoneyWorks",
            "Sayuringo Gundan",
            "Manatsu-san Respect Gundan",
            "Nogizaka46",
        ),
    ),
    (
        "Etsuko Yakushimaru + Yoshinori Sunahara",
        (
            "Etsuko Yakushimaru",
            "Yoshinori Sunahara",
        ),
    ),
    ("QUANGO & SPARKY", ("QUANGO & SPARKY",)),
    ("TAKAO & THE VIEW", ("TAKAO & THE VIEW",)),
    (
        "MAHO-dou + Kodomo-tachi",
        (
            "MAHO-dou",
            "Kodomo-tachi",
        ),
    ),
    (
        "Takanori Nishikawa+ASCA",
        (
            "Takanori Nishikawa",
            "ASCA",
        ),
    ),
    (
        "Dai 501 Tougou Sentou Koukuu-dan + Aya Uchida",
        (
            "Dai 501 Tougou Sentou Koukuu-dan",
            "Aya Uchida",
        ),
    ),
    (
        "livetune adding Fukase from SEKAI NO OWARI",
        (
            "livetune",
            "Fukase",
        ),
    ),
    (
        "livetune adding Rin Oikawa (from Q;Indivi)",
        (
            "livetune",
            "Rin Oikawa",
        ),
    ),
    (
        "livetune adding Anna Yano",
        (
            "livetune",
            "Anna Yano",
        ),
    ),
    (
        "Schrödinger's Cat adding kotringo",
        (
            "Schrödinger's Cat",
            "kotringo",
        ),
    ),
    (
        "livetune adding Yun*chi",
        (
            "livetune",
            "Yun*chi",
        ),
    ),
    (
        "Dimitri From Paris Voice Chiwa Saito",
        (
            "Dimitri From Paris",
            "Chiwa Saito",
        ),
    ),
    ("Mix Speaker's,Inc.", ("Mix Speaker's,Inc.",)),
    ("Kamisama, Boku wa Kizuite Shimatta", ("Kamisama, Boku wa Kizuite Shimatta",)),
    (
        "SawanoHiroyuki[nZk]:Uru",
        (
            "SawanoHiroyuki[nZk]",
            "Uru",
        ),
    ),
    (
        "SawanoHiroyuki[nZk]:Honoka Takahashi",
        (
            "SawanoHiroyuki[nZk]",
            "Honoka Takahashi",
        ),
    ),
    (
        "SawanoHiroyuki[nZk]:Anly",
        (
            "SawanoHiroyuki[nZk]",
            "Anly",
        ),
    ),
    (
        "SawanoHiroyuki[nZk]:LiSA",
        (
            "SawanoHiroyuki[nZk]",
            "LiSA",
        ),
    ),
    (
        "livetune adding Yuuki Ozaki",
        (
            "livetune",
            "Yuuki Ozaki",
        ),
    ),
    (
        "SawanoHiroyuki[nZk]:Jean-Ken Johnny",
        (
            "SawanoHiroyuki[nZk]",
            "Jean-Ken Johnny",
        ),
    ),
    (
        "SawanoHiroyuki[nZk]:Laco",
        (
            "SawanoHiroyuki[nZk]",
            "Laco",
        ),
    ),
    (
        "SawanoHiroyuki[nZk]:ReoNa",
        (
            "SawanoHiroyuki[nZk]",
            "ReoNa",
        ),
    ),
    (
        "SawanoHiroyuki[nZk]:mizuki",
        (
            "SawanoHiroyuki[nZk]",
            "mizuki",
        ),
    ),
    (
        "SawanoHiroyuki[nZk]:Gemie",
        (
            "SawanoHiroyuki[nZk]",
            "Gemie",
        ),
    ),
    (
        "SawanoHiroyuki[nZk]:Yosh",
        (
            "SawanoHiroyuki[nZk]",
            "Yosh",
        ),
    ),
    (
        "SawanoHiroyuki[nZk]:Tielle",
        (
            "SawanoHiroyuki[nZk]",
            "Tielle",
        ),
    ),
    (
        "SawanoHiroyuki[nZk]:naNami",
        (
            "SawanoHiroyuki[nZk]",
            "naNami",
        ),
    ),
    (
        "SawanoHiroyuki[nZk]:Aimer",
        (
            "SawanoHiroyuki[nZk]",
            "Aimer",
        ),
    ),
    (
        "ave;new project feat Saori Sakura×Dorechu",
        (
            "ave;new project",
            "Saori Sakura",
            "Dorechu",
        ),
    ),
    ("KING & QUEEN", ("KING & QUEEN",)),
    ("C&K", ("C&K",)),
    ("P&P", ("P&P",)),
    ("P4 with T", ("P4 with T",)),
    ("MAYA & Z", ("MAYA & Z",)),
    ("Icchi & Naru", ("Icchi & Naru",)),
    (
        "Licca & Noa",
        (
            "Licca",
            "Noa",
        ),
    ),
    ("Cotori with Stitchbird", ("Cotori with Stitchbird",)),
    (
        'SOIL&"PIMP"SESSIONS feat. Maaya Sakamoto',
        (
            'SOIL&"PIMP"SESSIONS',
            "Maaya Sakamoto",
        ),
    ),
    ("Kaako & Papa", ("Kaako & Papa",)),
    (
        "Yuji Ohno & Lupintic Six with Friends feat. Miyuki Sawashiro",
        (
            "Yuji Ohno",
            "Lupintic Six with Friends",
            "Miyuki Sawashiro",
        ),
    ),
    (
        "Yuji Ohno & Lupintic Six with Friends feat. Lyn Inaizumi",
        (
            "Yuji Ohno",
            "Lupintic Six with Friends",
            "Lyn Inaizumi",
        ),
    ),
    (
        "Yuji Ohno & Lupintic Six with Friends feat. Sakura Fujiwara",
        (
            "Yuji Ohno",
            "Lupintic Six with Friends",
            "Sakura Fujiwara",
        ),
    ),
    (
        "Yuji Ohno & Lupintic Six with Friends feat. Shigeru Matsuzaki",
        (
            "Yuji Ohno",
            "Lupintic Six with Friends",
            "Shigeru Matsuzaki",
        ),
    ),
    (
        "Yuji Ohno & Lupintic Six with Friends",
        (
            "Yuji Ohno",
            "Lupintic Six with Friends",
        ),
    ),
    (
        "Yuji Ohno & Lupintic Six with Friends feat. Akari Dritschler",
        (
            "Yuji Ohno",
            "Lupintic Six with Friends",
            "Akari Dritschler",
        ),
    ),
    (
        "Yuji Ohno&Lupintic Five with Friends feat. Yoshie Nakano (EGO-WRAPPIN')",
        (
            "Yuji Ohno",
            "Lupintic Five with Friends",
            "Yoshie Nakano (EGO-WRAPPIN')",
        ),
    ),
    (
        "Yuji Ohno & Lupintic Six",
        (
            "Yuji Ohno",
            "Lupintic Six",
        ),
    ),
    (
        "Yuji Ohno & Lupintic Five with Friends Feat. DOUBLE",
        (
            "Yuji Ohno",
            "Lupintic Five with Friends",
            "DOUBLE",
        ),
    ),
    ("New man Co.,Ltd.", ("New man Co.,Ltd.",)),
    (
        "Hamatora - Ryota Osaka & Wataru Hatano",
        (
            "Ryota Osaka",
            "Wataru Hatano",
        ),
    ),
    ("Adiamond -Amy & Bibian-", ("Adiamond -Amy & Bibian-",)),
    ("MAYUKO & Luminous", ("MAYUKO & Luminous",)),
    ("Bars & Melody", ("Bars & Melody",)),
    (
        "Rekka Katakiri meets Desen\u2606Rizotto",
        (
            "Rekka Katakiri",
            "Desen\u2606Rizotto",
        ),
    ),
    ("MON & STER", ("MON & STER",)),
    ("MYTH & ROID", ("MYTH & ROID",)),
    ("DEJO & BON", ("DEJO & BON",)),
    ("Kakki & Ash Potato", ("Kakki & Ash Potato",)),
    ("Anamu & Maki", ("Anamu & Maki",)),
    (
        "G-Eazy (featuring Bente Violet McPherson)",
        (
            "G-Eazy",
            "Bente Violet McPherson",
        ),
    ),
    ("SUEMITSU & THE SUEMITH", ("SUEMITSU & THE SUEMITH",)),
    ("TAKAKO&THE CRAZY BOYS", ("TAKAKO&THE CRAZY BOYS",)),
    ("TAKAKO & THE CRAZY BOYS", ("TAKAKO & THE CRAZY BOYS",)),
    ("Oosugi & Hiiko", ("Oosugi & Hiiko",)),
    ("Christy&Clinton", ("Christy&Clinton",)),
    ("Irene & Erika", ("Irene & Erika",)),
    (
        "Kazaki Morinaka meets \u25bd\u25b2TRiNITY\u25b2\u25bd",
        (
            "Kazaki Morinaka",
            "\u25bd\u25b2TRiNITY\u25b2\u25bd",
        ),
    ),
    ("Dylan & Catherine", ("Dylan & Catherine",)),
    ("Junich & JJr", ("Junich & JJr",)),
    ("Bread & Butter", ("Bread & Butter",)),
    ("Betsy & Chris", ("Betsy & Chris",)),
    ("RUN&GUN", ("RUN&GUN",)),
    ("Macolin & Pythagoras", ("Macolin & Pythagoras",)),
    ("Rats & Star", ("Rats & Star",)),
    ("Aki & Isao", ("Aki & Isao",)),
    ("Let's Go BOYS & GIRLS", ("Let's Go BOYS & GIRLS",)),
    ("Shirai Takako &CRAZY BOYS", ("Shirai Takako &CRAZY BOYS",)),
    ("TOSS & TURN", ("TOSS & TURN",)),
    ("Chage & Aska", ("Chage & Aska",)),
    ("CHAGE&ASKA", ("CHAGE&ASKA",)),
    ("Earth, Wind & Fire", ("Earth, Wind & Fire",)),
    ("Oranges & Lemons", ("Oranges & Lemons",)),
    ("Rough & Ready", ("Rough & Ready",)),
    ("LOREN&MASH", ("LOREN&MASH",)),
    ("Jack & Betty", ("Jack & Betty",)),
    ("Tackey & Tsubasa", ("Tackey & Tsubasa",)),
    ("AKIMA & NEOS", ("AKIMA & NEOS",)),
    ("Okino, Shuntaro", ("Okino, Shuntaro",)),
    (
        "Masayoshi Ooishi (feat. Yukari Tamura)",
        (
            "Masayoshi Ooishi",
            "Yukari Tamura",
        ),
    ),
    (
        "Masayoshi Ooishi (feat. Hiroki Yasumoto)",
        ("Masayoshi Ooishi", "Hiroki Yasumoto"),
    ),
    (
        "HoneyWorks meets Sphere",
        (
            "HoneyWorks",
            "Sphere",
        ),
    ),
    (
        "CHiCO with HoneyWorks meets Mafumafu",
        (
            "CHiCO",
            "HoneyWorks",
            "Mafumafu",
        ),
    ),
    (
        "HoneyWorks meets CHiCO & sana",
        ("HoneyWorks", "CHiCO", "sana"),
    ),
    (
        "HoneyWorks meets TrySail",
        (
            "HoneyWorks",
            "TrySail",
        ),
    ),
    (
        "HoneyWorks meets Mafumafu",
        (
            "HoneyWorks",
            "Mafumafu",
        ),
    ),
    (
        "HoneyWorks meets Amatsuki",
        (
            "HoneyWorks",
            "Amatsuki",
        ),
    ),
    ("Akebonoyama Chuugaku Band with T", ("Akebonoyama Chuugaku Band with T",)),
    ("Duel Hero Yuu & Atsuto", ("Duel Hero Yuu & Atsuto",)),
    (
        "Amane + Beat Mario (COOL&CREATE)",
        (
            "Amane",
            "Beat Mario (COOL&CREATE)",
        ),
    ),
    (
        "Naruyoshi Kikuchi y Pepe Tormento Azcarar feat. Ichiko Hashimoto",
        (
            "Naruyoshi Kikuchi",
            "Pepe Tormento Azcarar",
            "Ichiko Hashimoto",
        ),
    ),
    (
        "GENERATIONS from EXILE TRIBE",
        ("GENERATIONS",),
    ),
    (
        "THE RAMPAGE from EXILE TRIBE",
        ("THE RAMPAGE",),
    ),
    (
        "FANTASTICS from EXILE TRIBE",
        ("FANTASTICS",),
    ),
    (
        "Sandaime J SOUL BROTHERS from EXILE TRIBE",
        ("Sandaime J SOUL BROTHERS",),
    ),
    (
        "Sukima Switch produced by Tamio Okuda",
        (
            "Sukima Switch",
            "Tamio Okuda",
        ),
    ),
    (
        "Yui Makino Hikiiru Uchuu Shoujo Vanaren-tai",
        (
            "Yui Makino",
            "Uchuu Shoujo Vanaren-tai",
        ),
    ),
    (
        "Momoko Saitou Hikiiru Uchuu Shoujo Vanaren-tai",
        (
            "Momoko Saitou",
            "Uchuu Shoujo Vanaren-tai",
        ),
    ),
    (
        "Uchuu Shoujo Vanaren-tai wants Aya Hirano",
        (
            "Uchuu Shoujo Vanaren-tai",
            "Aya Hirano",
        ),
    ),
    ("Bach/Gounod", ("Johann Sebastian Bach/Charles Gounod",)),
    ("Run Girls, Run!", ("Run Girls, Run!",)),
    ("Wake Up, Girls!", ("Wake Up, Girls!",)),
    ("Wake Up, May'n!", ("Wake Up, May'n!",)),
    (
        "Waka・Fuuri・Sunao・Risuko from STAR☆ANIS",
        (
            "Waka from STAR☆ANIS",
            "Fuuri from STAR☆ANIS",
            "Sunao from STAR☆ANIS",
            "Risuko from STAR☆ANIS",
        ),
    ),
    (
        "yama (feat. Nakimushi)",
        (
            "yama",
            "Nakimushi",
        ),
    ),
    (
        "Waka・Fuuri・Sunao from STAR☆ANIS",
        (
            "Waka from STAR☆ANIS",
            "Fuuri from STAR☆ANIS",
            "Sunao from STAR☆ANIS",
        ),
    ),
    (
        "Waka・Fuuri・Sunao・Remi・Moe・Eri・Yuna・Risuko from STAR☆ANIS",
        (
            "Waka from STAR☆ANIS",
            "Fuuri from STAR☆ANIS",
            "Sunao from STAR☆ANIS",
            "Remi from STAR☆ANIS",
            "Moe from STAR☆ANIS",
            "Eri from STAR☆ANIS",
            "Yuna from STAR☆ANIS",
            "Risuko from STAR☆ANIS",
        ),
    ),
    (
        "Waka・Remi from STAR☆ANIS",
        (
            "Waka from STAR☆ANIS",
            "Remi from STAR☆ANIS",
        ),
    ),
    (
        "Waka・Fuuri・Sunao・Remi・Moe from STAR☆ANIS",
        (
            "Waka from STAR☆ANIS",
            "Fuuri from STAR☆ANIS",
            "Sunao from STAR☆ANIS",
            "Remi from STAR☆ANIS",
            "Moe from STAR☆ANIS",
        ),
    ),
    (
        "Waka・Fuuri・Sunao・Remi・Moe・Eri・Risuko from STAR☆ANIS",
        (
            "Waka from STAR☆ANIS",
            "Fuuri from STAR☆ANIS",
            "Sunao from STAR☆ANIS",
            "Remi from STAR☆ANIS",
            "Moe from STAR☆ANIS",
            "Eri from STAR☆ANIS",
            "Risuko from STAR☆ANIS",
        ),
    ),
    (
        "Waka・Moe from STAR☆ANIS",
        (
            "Waka from STAR☆ANIS",
            "Moe from STAR☆ANIS",
        ),
    ),
    ("Waka from STAR☆ANIS", ("Waka from STAR☆ANIS",)),
    ("Remi from STAR☆ANIS", ("Remi from STAR☆ANIS",)),
    ("Risuko from STAR☆ANIS", ("Risuko from STAR☆ANIS",)),
    (
        "Risuko・Waka from STAR☆ANIS",
        (
            "Risuko from STAR☆ANIS",
            "Waka from STAR☆ANIS",
        ),
    ),
    ("Eri from STAR☆ANIS", ("Eri from STAR☆ANIS",)),
    ("Fuuri from STAR☆ANIS", ("Fuuri from STAR☆ANIS",)),
    (
        "Risuko・Moe・Yuna from STAR☆ANIS",
        (
            "Risuko from STAR☆ANIS",
            "Moe from STAR☆ANIS",
            "Yuna from STAR☆ANIS",
        ),
    ),
    (
        "Sunao・Risuko from STAR☆ANIS",
        (
            "Sunao from STAR☆ANIS",
            "Risuko from STAR☆ANIS",
        ),
    ),
    (
        "Sunao・Waka・Fuuri from STAR☆ANIS",
        (
            "Sunao from STAR☆ANIS",
            "Waka from STAR☆ANIS",
            "Fuuri from STAR☆ANIS",
        ),
    ),
    (
        "Waka・Fuuri from STAR☆ANIS",
        (
            "Waka from STAR☆ANIS",
            "Fuuri from STAR☆ANIS",
        ),
    ),
    ("Sunao from STAR☆ANIS", ("Sunao from STAR☆ANIS",)),
    (
        "Waka・Risuko from STAR☆ANIS",
        (
            "Waka from STAR☆ANIS",
            "Risuko from STAR☆ANIS",
        ),
    ),
    (
        "Sunao・Yuniko from STAR☆ANIS",
        (
            "Sunao from STAR☆ANIS",
            "Yuniko from STAR☆ANIS",
        ),
    ),
    (
        "Waka・Fuuri・Sunao・Remi・Moe・Eri from STAR☆ANIS",
        (
            "Waka from STAR☆ANIS",
            "Fuuri from STAR☆ANIS",
            "Sunao from STAR☆ANIS",
            "Remi from STAR☆ANIS",
            "Moe from STAR☆ANIS",
            "Eri from STAR☆ANIS",
        ),
    ),
    (
        "Sayuri meets Desen Risotto",
        (
            "Sayuri",
            "Desen Risotto",
        ),
    ),
    ("Moe from STAR☆ANIS", ("Moe from STAR☆ANIS",)),
    (
        "Waka・Fuuri・Sunao・Yuna from STAR☆ANIS",
        (
            "Waka from STAR☆ANIS",
            "Fuuri from STAR☆ANIS",
            "Sunao from STAR☆ANIS",
            "Yuna from STAR☆ANIS",
        ),
    ),
    (
        "Risuko・Sunao・Yuna from STAR☆ANIS",
        (
            "Risuko from STAR☆ANIS",
            "Sunao from STAR☆ANIS",
            "Yuna from STAR☆ANIS",
        ),
    ),
    (
        "Waka・Sunao from STAR☆ANIS",
        (
            "Waka from STAR☆ANIS",
            "Sunao from STAR☆ANIS",
        ),
    ),
    (
        "Waka・Fuuri・Yuna from STAR☆ANIS",
        (
            "Waka from STAR☆ANIS",
            "Fuuri from STAR☆ANIS",
            "Yuna from STAR☆ANIS",
        ),
    ),
    (
        "Risuko・Waka・Fuuri・Mona from STAR☆ANIS",
        (
            "Risuko from STAR☆ANIS",
            "Waka from STAR☆ANIS",
            "Fuuri from STAR☆ANIS",
            "Mona from STAR☆ANIS",
        ),
    ),
    (
        "Eri・Waka from STAR☆ANIS",
        (
            "Eri from STAR☆ANIS",
            "Waka from STAR☆ANIS",
        ),
    ),
    ("Yuna from STAR☆ANIS", ("Yuna from STAR☆ANIS",)),
    (
        "Risuko・Mona from STAR☆ANIS",
        (
            "Risuko from STAR☆ANIS",
            "Mona from STAR☆ANIS",
        ),
    ),
    (
        "Fuuri・Yuna・Sunao・Eri from STAR☆ANIS",
        (
            "Fuuri from STAR☆ANIS",
            "Yuna from STAR☆ANIS",
            "Sunao from STAR☆ANIS",
            "Eri from STAR☆ANIS",
        ),
    ),
    (
        "Waka・Fuuri・Sunao・Remi from STAR☆ANIS",
        (
            "Waka from STAR☆ANIS",
            "Fuuri from STAR☆ANIS",
            "Sunao from STAR☆ANIS",
            "Remi from STAR☆ANIS",
        ),
    ),
    ("Ruka from STAR☆ANIS", ("Ruka from STAR☆ANIS",)),
    (
        "Waka・Ruka from STAR☆ANIS",
        (
            "Waka from STAR☆ANIS",
            "Ruka from STAR☆ANIS",
        ),
    ),
    ("Mona from STAR☆ANIS", ("Mona from STAR☆ANIS",)),
    (
        "Waka・Fuuri・Yuna・Ruka from STAR☆ANIS",
        (
            "Waka from STAR☆ANIS",
            "Fuuri from STAR☆ANIS",
            "Yuna from STAR☆ANIS",
            "Ruka from STAR☆ANIS",
        ),
    ),
    (
        "Waka・Remi・Risuko・Mona・Fuuri・Eri from STAR☆ANIS",
        (
            "Waka from STAR☆ANIS",
            "Remi from STAR☆ANIS",
            "Risuko from STAR☆ANIS",
            "Mona from STAR☆ANIS",
            "Fuuri from STAR☆ANIS",
            "Eri from STAR☆ANIS",
        ),
    ),
    (
        "Fuuri・Waka from STAR☆ANIS",
        (
            "Fuuri from STAR☆ANIS",
            "Waka from STAR☆ANIS",
        ),
    ),
    (
        "Yuna・Remi from STAR☆ANIS",
        (
            "Yuna from STAR☆ANIS",
            "Remi from STAR☆ANIS",
        ),
    ),
    (
        "Remi・Eri from STAR☆ANIS",
        (
            "Remi from STAR☆ANIS",
            "Eri from STAR☆ANIS",
        ),
    ),
    (
        "Waka・Fuuri・Remi・Eri・Ruka from STAR☆ANIS",
        (
            "Waka from STAR☆ANIS",
            "Fuuri from STAR☆ANIS",
            "Remi from STAR☆ANIS",
            "Eri from STAR☆ANIS",
            "Ruka from STAR☆ANIS",
        ),
    ),
    (
        "Waka・Risuko・Ruka from STAR☆ANIS",
        (
            "Waka from STAR☆ANIS",
            "Risuko from STAR☆ANIS",
            "Ruka from STAR☆ANIS",
        ),
    ),
    (
        "Yuna・Remi・Eri from STAR☆ANIS",
        (
            "Yuna from STAR☆ANIS",
            "Remi from STAR☆ANIS",
            "Eri from STAR☆ANIS",
        ),
    ),
    (
        "Eri・Remi from STAR☆ANIS",
        (
            "Eri from STAR☆ANIS",
            "Remi from STAR☆ANIS",
        ),
    ),
    (
        "Aya&chika from D&D",
        (
            "Aya Uehara",
            "Chikano Higa",
        ),
    ),
    (
        "Ruka・Mona・Miki from AIKATSU☆STARS!",
        (
            "Ruka from AIKATSU☆STARS!",
            "Mona from AIKATSU☆STARS!",
            "Miki from AIKATSU☆STARS!",
        ),
    ),
    ("Ruka from AIKATSU☆STARS!", ("Ruka from AIKATSU☆STARS!",)),
    (
        "Miho・Miki from AIKATSU☆STARS!",
        (
            "Miho from AIKATSU☆STARS!",
            "Miki from AIKATSU☆STARS!",
        ),
    ),
    (
        "Miho・Nanase・Kana from AIKATSU☆STARS!",
        (
            "Miho from AIKATSU☆STARS!",
            "Nanase from AIKATSU☆STARS!",
            "Kana from AIKATSU☆STARS!",
        ),
    ),
    ("Mona from AIKATSU☆STARS!", ("Mona from AIKATSU☆STARS!",)),
    ("Kana from AIKATSU☆STARS!", ("Kana from AIKATSU☆STARS!",)),
    (
        "Kana・Ruka from AIKATSU☆STARS!",
        (
            "Kana from AIKATSU☆STARS!",
            "Ruka from AIKATSU☆STARS!",
        ),
    ),
    (
        "Miki・Ruka・Mona from AIKATSU☆STARS!",
        (
            "Miki from AIKATSU☆STARS!",
            "Ruka from AIKATSU☆STARS!",
            "Mona from AIKATSU☆STARS!",
        ),
    ),
    (
        "Ruka・Mona from AIKATSU☆STARS!",
        (
            "Ruka from AIKATSU☆STARS!",
            "Mona from AIKATSU☆STARS!",
        ),
    ),
    (
        "Ruka・Miki from AIKATSU☆STARS!",
        (
            "Ruka from AIKATSU☆STARS!",
            "Miki from AIKATSU☆STARS!",
        ),
    ),
    ("Miho from AIKATSU☆STARS!", ("Miho from AIKATSU☆STARS!",)),
    (
        "Mona・Ruka from AIKATSU☆STARS!",
        (
            "Mona from AIKATSU☆STARS!",
            "Ruka from AIKATSU☆STARS!",
        ),
    ),
    ("Nanase from AIKATSU☆STARS!", ("Nanase from AIKATSU☆STARS!",)),
    (
        "Miki・Miho from AIKATSU☆STARS!",
        (
            "Miki from AIKATSU☆STARS!",
            "Miho from AIKATSU☆STARS!",
        ),
    ),
    ("Miki from AIKATSU☆STARS!", ("Miki from AIKATSU☆STARS!",)),
    (
        "Mona・Nanase from AIKATSU☆STARS!",
        (
            "Mona from AIKATSU☆STARS!",
            "Nanase from AIKATSU☆STARS!",
        ),
    ),
    (
        "Ruka・Mona・Miki・Miho・Nanase・Kana from AIKATSU☆STARS!",
        (
            "Ruka from AIKATSU☆STARS!",
            "Mona from AIKATSU☆STARS!",
            "Miki from AIKATSU☆STARS!",
            "Miho from AIKATSU☆STARS!",
            "Nanase from AIKATSU☆STARS!",
            "Kana from AIKATSU☆STARS!",
        ),
    ),
    (
        "Nanase・Kana from AIKATSU☆STARS!",
        (
            "Nanase from AIKATSU☆STARS!",
            "Kana from AIKATSU☆STARS!",
        ),
    ),
    (
        "Ruka・Nanase from AIKATSU☆STARS!",
        (
            "Ruka from AIKATSU☆STARS!",
            "Nanase from AIKATSU☆STARS!",
        ),
    ),
    (
        "Ruka・Kana from AIKATSU☆STARS!",
        (
            "Ruka from AIKATSU☆STARS!",
            "Kana from AIKATSU☆STARS!",
        ),
    ),
    (
        "Miho・Nanase from AIKATSU☆STARS!",
        (
            "Miho from AIKATSU☆STARS!",
            "Nanase from AIKATSU☆STARS!",
        ),
    ),
    (
        "Sena・Rie from AIKATSU☆STARS!",
        (
            "Sena from AIKATSU☆STARS!",
            "Rie from AIKATSU☆STARS!",
        ),
    ),
    (
        "Sena・Rie・Miki・Kana from AIKATSU☆STARS!",
        (
            "Sena from AIKATSU☆STARS!",
            "Rie from AIKATSU☆STARS!",
            "Miki from AIKATSU☆STARS!",
            "Kana from AIKATSU☆STARS!",
        ),
    ),
    ("SUN&LUNAR", ("SUN&LUNAR",)),
    (
        "Ruka・Nanase・Kana・Miho from AIKATSU☆STARS!",
        (
            "Ruka from AIKATSU☆STARS!",
            "Nanase from AIKATSU☆STARS!",
            "Kana from AIKATSU☆STARS!",
            "Miho from AIKATSU☆STARS!",
        ),
    ),
    (
        "Ruka・Sena from AIKATSU☆STARS!",
        (
            "Ruka from AIKATSU☆STARS!",
            "Sena from AIKATSU☆STARS!",
        ),
    ),
    (
        "Risa/Miho from AIKATSU☆STARS!",
        (
            "Risa Aizawa",
            "Miho from AIKATSU☆STARS!",
        ),
    ),
    (
        "Sena・Ruka from AIKATSU☆STARS!",
        (
            "Sena from AIKATSU☆STARS!",
            "Ruka from AIKATSU☆STARS!",
        ),
    ),
    (
        "Ayahi Takagaki meets Sphere",
        (
            "Ayahi Takagaki",
            "Sphere",
        ),
    ),
    ("Rie from AIKATSU☆STARS!", ("Rie from AIKATSU☆STARS!",)),
    ("Sena from AIKATSU☆STARS!", ("Sena from AIKATSU☆STARS!",)),
    (
        "Ruka・Miho from AIKATSU☆STARS!",
        (
            "Ruka from AIKATSU☆STARS!",
            "Miho from AIKATSU☆STARS!",
        ),
    ),
    (
        "Sena・Miki・Kana from AIKATSU☆STARS!",
        (
            "Sena from AIKATSU☆STARS!",
            "Miki from AIKATSU☆STARS!",
            "Kana from AIKATSU☆STARS!",
        ),
    ),
    (
        "Risa/Miho・Rie・Ruka from AIKATSU☆STARS!",
        (
            "Risa Aizawa",
            "Miho from AIKATSU☆STARS!",
            "Rie from AIKATSU☆STARS!",
            "Ruka from AIKATSU☆STARS!",
        ),
    ),
    (
        "Sena・Rie・Miki・Kana・Nanase from AIKATSU☆STARS!",
        (
            "Sena from AIKATSU☆STARS!",
            "Rie from AIKATSU☆STARS!",
            "Miki from AIKATSU☆STARS!",
            "Kana from AIKATSU☆STARS!",
            "Nanase from AIKATSU☆STARS!",
        ),
    ),
    (
        "Rie・Kana from AIKATSU☆STARS!",
        (
            "Rie from AIKATSU☆STARS!",
            "Kana from AIKATSU☆STARS!",
        ),
    ),
    (
        "Miho・Kana from AIKATSU☆STARS!",
        (
            "Miho from AIKATSU☆STARS!",
            "Kana from AIKATSU☆STARS!",
        ),
    ),
    (
        "Nanase・Miho・Kana from AIKATSU☆STARS!",
        (
            "Nanase from AIKATSU☆STARS!",
            "Miho from AIKATSU☆STARS!",
            "Kana from AIKATSU☆STARS!",
        ),
    ),
    (
        "Kana・Sena・Miki from AIKATSU☆STARS!",
        (
            "Kana from AIKATSU☆STARS!",
            "Sena from AIKATSU☆STARS!",
            "Miki from AIKATSU☆STARS!",
        ),
    ),
    (
        "Kuni Kawachi and Takako Ishiguro",
        (
            "Kuni Kawachi",
            "Takako Ishiguro",
        ),
    ),
    (
        "Kana・Nanase from AIKATSU☆STARS!",
        (
            "Kana from AIKATSU☆STARS!",
            "Nanase from AIKATSU☆STARS!",
        ),
    ),
    (
        "Nanase・Rie from AIKATSU☆STARS!",
        (
            "Nanase from AIKATSU☆STARS!",
            "Rie from AIKATSU☆STARS!",
        ),
    ),
    (
        "Miki・Nanase from AIKATSU☆STARS!",
        (
            "Miki from AIKATSU☆STARS!",
            "Nanase from AIKATSU☆STARS!",
        ),
    ),
    (
        "Sena・Miki from AIKATSU☆STARS!",
        (
            "Sena from AIKATSU☆STARS!",
            "Miki from AIKATSU☆STARS!",
        ),
    ),
    (
        "Sena・Nanase from AIKATSU☆STARS!",
        (
            "Sena from AIKATSU☆STARS!",
            "Nanase from AIKATSU☆STARS!",
        ),
    ),
    (
        "Rie・Nanase from AIKATSU☆STARS!",
        (
            "Rie from AIKATSU☆STARS!",
            "Nanase from AIKATSU☆STARS!",
        ),
    ),
    (
        "Aine・Mio from BEST FRIENDS!",
        (
            "Aine from BEST FRIENDS!",
            "Mio from BEST FRIENDS!",
        ),
    ),
    (
        "Karen・Mirai from BEST FRIENDS!",
        (
            "Karen from BEST FRIENDS!",
            "Mirai from BEST FRIENDS!",
        ),
    ),
    ("Mio from BEST FRIENDS!", ("Mio from BEST FRIENDS!",)),
    ("Aine from BEST FRIENDS!", ("Aine from BEST FRIENDS!",)),
    ("Mirai from BEST FRIENDS!", ("Mirai from BEST FRIENDS!",)),
    ("Maika from BEST FRIENDS!", ("Maika from BEST FRIENDS!",)),
    ("Karen from BEST FRIENDS!", ("Karen from BEST FRIENDS!",)),
    (
        "Maika・Ema from BEST FRIENDS!",
        (
            "Maika from BEST FRIENDS!",
            "Ema from BEST FRIENDS!",
        ),
    ),
    ("Sakuya from BEST FRIENDS!", ("Sakuya from BEST FRIENDS!",)),
    ("Ema from BEST FRIENDS!", ("Ema from BEST FRIENDS!",)),
    (
        "Sakuya・Kaguya from BEST FRIENDS!",
        (
            "Sakuya from BEST FRIENDS!",
            "Kaguya from BEST FRIENDS!",
        ),
    ),
    (
        "Aine・Mirai from BEST FRIENDS!",
        (
            "Aine from BEST FRIENDS!",
            "Mirai from BEST FRIENDS!",
        ),
    ),
    ("Kaguya from BEST FRIENDS!", ("Kaguya from BEST FRIENDS!",)),
    (
        "Aine・Mio・Maika・Ema from BEST FRIENDS!",
        (
            "Aine from BEST FRIENDS!",
            "Mio from BEST FRIENDS!",
            "Maika from BEST FRIENDS!",
            "Ema from BEST FRIENDS!",
        ),
    ),
    (
        "Aine・Mio・Ema・Maika from BEST FRIENDS!",
        (
            "Aine from BEST FRIENDS!",
            "Mio from BEST FRIENDS!",
            "Ema from BEST FRIENDS!",
            "Maika from BEST FRIENDS!",
        ),
    ),
    ("Hibiki from BEST FRIENDS!", ("Hibiki from BEST FRIENDS!",)),
    (
        "Mio・Wakaba from BEST FRIENDS!",
        (
            "Mio from BEST FRIENDS!",
            "Wakaba from BEST FRIENDS!",
        ),
    ),
    ("Wakaba from BEST FRIENDS!", ("Wakaba from BEST FRIENDS!",)),
    (
        "Hibiki・Alicia from BEST FRIENDS!",
        (
            "Hibiki from BEST FRIENDS!",
            "Alicia from BEST FRIENDS!",
        ),
    ),
    (
        "Ondo\u2606Girl meets Keroro Shoutai",
        (
            "Ondo\u2606Girl",
            "Keroro Shoutai",
        ),
    ),
    (
        "Nicole Price and Bynne Price",
        (
            "Nicole Price",
            "Bynne Price",
        ),
    ),
    (
        "Raki・Aine・Mio from BEST FRIENDS!",
        (
            "Raki from BEST FRIENDS!",
            "Aine from BEST FRIENDS!",
            "Mio from BEST FRIENDS!",
        ),
    ),
    (
        "Raki・Aine・Mio from BEST FRIENDS!/Waka・Ruka・Sena",
        (
            "Raki from BEST FRIENDS!",
            "Aine from BEST FRIENDS!",
            "Mio from BEST FRIENDS!",
            "Waka from STAR☆ANIS",
            "Ruka from AIKATSU☆STARS!",
            "Sena from AIKATSU☆STARS!",
        ),
    ),
    (
        "Raki from BEST FRIENDS!",
        (
            "Raki from BEST FRIENDS!",
            "Sena from AIKATSU☆STARS",
        ),
    ),
    ("Mio from BEST FRIENDS!/Sena", ("Mio from BEST FRIENDS!",)),
    (
        "Mirai from BEST FRIENDS!/Ruka",
        (
            "Mirai from BEST FRIENDS!",
            "Ruka from AIKATSU☆STARS!",
        ),
    ),
    (
        "Raki from BEST FRIENDS!/Waka",
        (
            "Raki from BEST FRIENDS!",
            "Waka from STAR☆ANIS",
        ),
    ),
    (
        "Hibiki from BEST FRIENDS!/Risuko/Risa",
        ("Hibiki from BEST FRIENDS!", "Risuko from STAR☆ANIS", "Risa Aizawa"),
    ),
    (
        "Sunao/Sena・Rie・Miki・Kana・Nanase/Aine・Mio・Maika・Ema from BEST FRIENDS!",
        (
            "Sunao from STAR☆ANIS",
            "Sena from AIKATSU☆STARS!",
            "Rie from AIKATSU☆STARS!",
            "Miki from AIKATSU☆STARS!",
            "Kana from AIKATSU☆STARS!",
            "Nanase from AIKATSU☆STARS",
            "Aine from BEST FRIENDS!",
            "Mio from BEST FRIENDS!",
            "Maika from BEST FRIENDS!",
            "Ema from BEST FRIENDS!",
        ),
    ),
    (
        "Aine・Mio from BEST FRIENDS!/Sena",
        (
            "Aine from BEST FRIENDS!",
            "Mio from BEST FRIENDS!",
            "Sena from AIKATSU☆STARS!",
        ),
    ),
    ("Alicia from BEST FRIENDS!", ("Alicia from BEST FRIENDS!",)),
    (
        "Aine・Mio from BEST FRIENDS!/Waka",
        (
            "Aine from BEST FRIENDS!",
            "Mio from BEST FRIENDS!",
            "Waka from STAR☆ANIS",
        ),
    ),
    (
        "Ayane・Ruka・Rie/Karen from BEST FRIENDS!",
        (
            "Ayane Fujisaki",
            "Ruka from AIKATSU☆STARS!",
            "Rie from AIKATSU☆STARS!",
            "Karen from BEST FRIENDS!",
        ),
    ),
    (
        "Mao・Ruli from STARRY PLANET☆",
        (
            "Mao from STARRY PLANET☆",
            "Ruli from STARRY PLANET☆",
        ),
    ),
    (
        "Mao・Ayumi from STARRY PLANET☆",
        (
            "Mao from STARRY PLANET☆",
            "Ayumi from STARRY PLANET☆",
        ),
    ),
    (
        "Mao・Kyouko from STARRY PLANET☆",
        (
            "Mao from STARRY PLANET☆",
            "Kyouko from STARRY PLANET☆",
        ),
    ),
    (
        "Mao・Ruli・Kyouko・Shiori from STARRY PLANET☆",
        (
            "Mao from STARRY PLANET☆",
            "Ruli from STARRY PLANET☆",
            "Kyouko from STARRY PLANET☆",
            "Shiori from STARRY PLANET☆",
        ),
    ),
    ("Ayumi from STARRY PLANET☆", ("Ayumi from STARRY PLANET☆",)),
    (
        "Ayumi・Ruli from STARRY PLANET☆",
        (
            "Ayumi from STARRY PLANET☆",
            "Ruli from STARRY PLANET☆",
        ),
    ),
    ("Meisa from STARRY PLANET☆", ("Meisa from STARRY PLANET☆",)),
    (
        "Shiori・Ruli from STARRY PLANET☆",
        (
            "Shiori from STARRY PLANET☆",
            "Ruli from STARRY PLANET☆",
        ),
    ),
    (
        "Miyuki Ichijou and the Howmei Girls",
        (
            "Miyuki Ichijou",
            "the Howmei Girls",
        ),
    ),
    (
        "Dominic Nolfi, Heidi Weyhmueller and the Cast of Pokémon Live",
        (
            "Dominic Nolfi",
            "Heidi Weyhmueller",
            "the Cast of Pokémon Live",
        ),
    ),
    (
        "Jeffrey Pescetto and the Jets",
        (
            "Jeffrey Pescetto",
            "the Jets",
        ),
    ),
    (
        "Tadashi Suzuki and CA Pops",
        (
            "Tadashi Suzuki",
            "CA Pops",
        ),
    ),
    (
        "Youko Kuri and The Viking",
        (
            "Youko Kuri",
            "The Viking",
        ),
    ),
    (
        "Jeremy Sweet and Ian Nickus",
        (
            "Jeremy Sweet",
            "Ian Nickus",
        ),
    ),
    (
        "Élan Rivera and PJ Lequerica",
        (
            "Élan Rivera",
            "PJ Lequerica",
        ),
    ),
    (
        "Aida Bunzou and Tokyo Shounen Shoujo Gasshoutai",
        (
            "Aida Bunzou",
            "Tokyo Shounen Shoujo Gasshoutai",
        ),
    ),
    (
        "Mints and Rei Sekimori",
        (
            "Mints",
            "Rei Sekimori",
        ),
    ),
    (
        "Yoko Nakamura and Young Fresh",
        (
            "Yoko Nakamura",
            "Young Fresh",
        ),
    ),
    (
        "Yoshimi Nakajima and Young Fresh",
        (
            "Yoshimi Nakajima",
            "Young Fresh",
        ),
    ),
    (
        "Makiko Morita, Shiho Mannaka and Young Fresh",
        (
            "Makiko Morita",
            "Shiho Mannaka",
            "Young Fresh",
        ),
    ),
    (
        "Masato Hidaka and Okama Club",
        (
            "Masato Hidaka",
            "Okama Club",
        ),
    ),
    (
        "Erin Bowman and Joe Philips",
        (
            "Erin Bowman",
            "Joe Philips",
        ),
    ),
    (
        "Alex Nackman and Kathryn Raio",
        (
            "Alex Nackman",
            "Kathryn Raio",
        ),
    ),
    (
        "Neal Coomer and Kathryn Raio",
        (
            "Neal Coomer",
            "Kathryn Raio",
        ),
    ),
    (
        "Ben Dixon and The Sad Truth",
        (
            "Ben Dixon",
            "The Sad Truth",
        ),
    ),
    (
        "Misaki Komatsu feat. Decktonic and Anthony Seeha",
        ("Misaki Komatsu", "Decktonic", "Anthony Seeha"),
    ),
    (
        "Jannel Candrice and The Sad Truth",
        (
            "Jannel Candrice",
            "The Sad Truth",
        ),
    ),
    (
        "Skrillex and Nik Roos",
        (
            "Skrillex",
            "Nik Roos",
        ),
    ),
    (
        "Elspeth Bawden and Amelia Jones",
        (
            "Elspeth Bawden",
            "Amelia Jones",
        ),
    ),
    (
        "DJ Milky and b-nCHANt-d featuring Rachel Pollack",
        (
            "DJ Milky",
            "b-nCHANt-d",
            "Rachel Pollack",
        ),
    ),
    (
        "Mao・Shiori from STARRY PLANET☆",
        (
            "Mao from STARRY PLANET☆",
            "Shiori from STARRY PLANET☆",
        ),
    ),
    (
        "Shiori・Ann from STARRY PLANET☆",
        (
            "Shiori from STARRY PLANET☆",
            "Ann from STARRY PLANET☆",
        ),
    ),
    (
        "Mao・Ann from STARRY PLANET☆",
        (
            "Mao from STARRY PLANET☆",
            "Ann from STARRY PLANET☆",
        ),
    ),
    (
        "Kyouko・Ayumi from STARRY PLANET☆",
        (
            "Kyouko from STARRY PLANET☆",
            "Ayumi from STARRY PLANET☆",
        ),
    ),
    (
        "Ruli・Meisa from STARRY PLANET☆",
        (
            "Ruli from STARRY PLANET☆",
            "Meisa from STARRY PLANET☆",
        ),
    ),
    (
        "Mao・Meisa from STARRY PLANET☆",
        (
            "Mao from STARRY PLANET☆",
            "Meisa from STARRY PLANET☆",
        ),
    ),
    (
        "Ann・Sala from STARRY PLANET☆",
        (
            "Ann from STARRY PLANET☆",
            "Sala from STARRY PLANET☆",
        ),
    ),
    (
        "Shiori・Sala from STARRY PLANET☆",
        (
            "Shiori from STARRY PLANET☆",
            "Sala from STARRY PLANET☆",
        ),
    ),
    (
        "Ruli・Kyouko from STARRY PLANET☆",
        (
            "Ruli from STARRY PLANET☆",
            "Kyouko from STARRY PLANET☆",
        ),
    ),
    (
        "Ayumi・Meisa from STARRY PLANET☆",
        (
            "Ayumi from STARRY PLANET☆",
            "Meisa from STARRY PLANET☆",
        ),
    ),
    (
        "Ruka・Mona・Miki from AIKATSU☆STARS! & Waka from STAR☆ANIS",
        (
            "Ruka from AIKATSU☆STARS!",
            "Mona from AIKATSU☆STARS!",
            "Miki from AIKATSU☆STARS!",
            "Waka from STAR☆ANIS",
        ),
    ),
    (
        "Eri from STAR☆ANIS & Miho from AIKATSU☆STARS!",
        (
            "Eri from STAR☆ANIS",
            "Miho from AIKATSU☆STARS!",
        ),
    ),
    (
        "Ruka・Mona・Miki・Miho from AIKATSU☆STARS! & Waka・Risuko from STAR☆ANIS",
        (
            "Ruka from AIKATSU☆STARS!",
            "Mona from AIKATSU☆STARS!",
            "Miki from AIKATSU☆STARS!",
            "Miho from AIKATSU☆STARS!",
            "Waka from STAR☆ANIS",
            "Risuko from STAR☆ANIS",
        ),
    ),
    (
        "Waka・Fuuri・Sunao from STAR☆ANIS & Ruka・Mona・Miki from AIKATSU☆STARS!",
        (
            "Waka from STAR☆ANIS",
            "Fuuri from STAR☆ANIS",
            "Sunao from STAR☆ANIS",
            "Ruka from AIKATSU☆STARS!",
            "Mona from AIKATSU☆STARS!",
            "Miki from AIKATSU☆STARS!",
        ),
    ),
    (
        "Ruka・Mona・Miki・Miho・Nanase・Kana from AIKATSU☆STARS! & Waka from STAR☆ANIS",
        (
            "Ruka from AIKATSU☆STARS!",
            "Mona from AIKATSU☆STARS!",
            "Miki from AIKATSU☆STARS!",
            "Miho from AIKATSU☆STARS!",
            "Nanase from AIKATSU☆STARS!",
            "Kana from AIKATSU☆STARS!",
            "Waka from STAR☆ANIS",
        ),
    ),
    (
        "Waka・Fuuri・Yuna・Remi・Eri・Risuko・Mona・Ruka from STAR☆ANIS & Mona・Miki・Miho・Nanase・Kana from AIKATSU☆STARS!",
        (
            "Waka from STAR☆ANIS",
            "Fuuri from STAR☆ANIS",
            "Yuna from STAR☆ANIS",
            "Remi from STAR☆ANIS",
            "Eri from STAR☆ANIS",
            "Risuko from STAR☆ANIS",
            "Mona from STAR☆ANIS",
            "Ruka from STAR☆ANIS",
            "Miki from AIKATSU☆STARS!",
            "Miho from AIKATSU☆STARS!",
            "Nanase from AIKATSU☆STARS!",
            "Kana from AIKATSU☆STARS!",
        ),
    ),
    (
        "Waka・Eimi",
        (
            "Waka Kirishima",
            "Eimi Naruse",
        ),
    ),
    ("Risa・Eimi", ("Risa Aizawa", "Eimi Naruse")),
    (
        "Ayane・Eri",
        (
            "Ayane Fujisaki",
            "Eri Aino",
        ),
    ),
    ("You & Explosion Band", ("You & Explosion Band",)),
    (
        "You & Explosion Band feat. Lyn Inaizumi",
        (
            "You & Explosion Band",
            "Lyn Inaizumi",
        ),
    ),
    (
        "You & Explosion Band featuring Lileth",
        (
            "You & Explosion Band",
            "Lileth",
        ),
    ),
    (
        "Akiko & Naoko Kobayashi",
        (
            "Akiko Kobayashi",
            "Naoko Kobayashi",
        ),
    ),
    (
        "(K)NoW_NAME:Ayaka Tachibana",
        (
            "(K)NoW_NAME",
            "Ayaka Tachibana",
        ),
    ),
    (
        "(K)NoW_NAME:Ayaka Tachibana & NIKIIE",
        (
            "(K)NoW_NAME",
            "Ayaka Tachibana",
            "NIKIIE",
        ),
    ),
    (
        "(K)NoW_NAME:NIKIIE",
        (
            "(K)NoW_NAME",
            "NIKIIE",
        ),
    ),
    (
        "(K)NoW_NAME:AIJ",
        (
            "(K)NoW_NAME",
            "AIJ",
        ),
    ),
    (
        "(K)NoW_NAME:eNu",
        (
            "(K)NoW_NAME",
            "eNu",
        ),
    ),
    (
        "Kevin Penkin [feat. Emi Evans]",
        (
            "Kevin Penkin",
            "Emi Evans",
        ),
    ),
    ("kanon x kanon", ("kanon x kanon",)),
    (
        "Shirahamazaka Koukou Gasshou-bu & Seigaku-bu",
        (
            "Shirahamazaka Koukou Gasshou-bu",
            "Shirahamazaka Koukou Seigaku-bu",
        ),
    ),
    ("Saori Hayami (from Eclipse)", ("Saori Hayami",)),
    ("Megumi Nakajima (from Eclipse)", ("Megumi Nakajima",)),
    ("Haruka Tomatsu (from Eclipse)", ("Haruka Tomatsu",)),
    (
        "AKINO & AIKI from bless4",
        (
            "AKINO",
            "AIKI",
        ),
    ),
    ("AKINO from bless4", ("AKINO",)),
    ("AIKI from bless4", ("AIKI",)),
    (
        "AKINO arai×AKINO from bless4",
        (
            "AKINO arai",
            "AKINO",
        ),
    ),
    ("AIKI & AKINO from bless4", ("AIKI", "AKINO")),
    ("TK from Ling Tosite Sigure", ("TK",)),
    ("Yuuki Ozaki(from Galileo Galilei)", ("Yuuki Ozaki",)),
    (
        "Kotaro Oshio with Yuuki Ozaki (from Galileo Galilei)",
        (
            "Kotaro Oshio",
            "Yuuki Ozaki",
        ),
    ),
    ("Aya Hirano from Springs", ("Aya Hirano",)),
    (
        "Yuki Kaji, Kishou Taniyama, Yui Ishikawa from attackers",
        (
            "Yuki Kaji",
            "Kishou Taniyama",
            "Yui Ishikawa",
        ),
    ),
    ("Hiroshi Kamiya from No Name", ("Hiroshi Kamiya",)),
    (
        "Jin ft. MARIA from GARNiDELiA",
        (
            "Jin",
            "MARiA",
        ),
    ),
    (
        "Shinya & Tarantula (From Hi-Timez)",
        (
            "Shinya",
            "Tarantula",
        ),
    ),
    (
        "Argonavis feat. Jin Ogasawara from GYROAXIA",
        (
            "Argonavis",
            "Jin Ogasawara",
        ),
    ),
    ("Misaki Kurea from Girls²", ("Misaki Kurea",)),
    (
        "livetune adding Takuro Sugawara from 9mm Parabellum Bullet",
        (
            "livetune",
            "Takuro Sugawara",
        ),
    ),
    ("Anna (BON-BON BLANCO)", ("ANNA",)),
    (
        "Jin ft. Takumi Yoshida from phatmans after school",
        (
            "Jin",
            "Takumi Yoshida",
        ),
    ),
    ("Shifo from UNIVERS\u2605L D", ("Shifo",)),
    ("Ham-chans • Himawari-gumi", ("Ham-chans • Himawari-gumi",)),
    (
        "HARU＆SAYAKA from UNIVERS★LD",
        (
            "HARU",
            "SAYAKA",
        ),
    ),
    ("UL-SAYS [from T.P.D]", ("UL-SAYS",)),
    (
        "BACK-ON & Lil' Fang (from FAKY)",
        (
            "BACK-ON",
            "Lil' Fang",
        ),
    ),
    (
        "Charisma.com & RYO-Z Oni-san of RIP SLYME",
        (
            "Charisma.com",
            "RYO-Z",
        ),
    ),
    (
        "Naoki Sagawa feat. JOE from PSYCHIC LOVER",
        (
            "Naoki Sagawa",
            "JOE",
        ),
    ),
    (
        "Jin ft. Kouta Matsuyama from Byee the Round",
        (
            "Jin",
            "Kouta Matsuyama",
        ),
    ),
    (
        "Jin ft. Shouichi Taguchi from Sentimental Vector",
        (
            "Jin",
            "Shouichi Taguchi",
        ),
    ),
    ("2&", ("2&",)),
    ("Aztech from Hybrid Thoughts", ("Aztech",)),
    (
        "Aztech, Paranom & Kasper from Hybrid Thoughts",
        (
            "Aztech",
            "Paranom",
            "Kasper",
        ),
    ),
    ("Tomoyo Mitani (LieN)", ("Tomoyo Mitani",)),
    (
        "Demon Kakka×Arika Takarano (ALI PROJECT)",
        (
            "Demon Kakka",
            "Arika Takarano",
        ),
    ),
    ("I.C.I. a.k.a. Ai Ichikawa", ("I.C.I.",)),
    ("Takayuki Hattori Presents GUNDAM THE ORIGIN", ("Takayuki Hattori",)),
    ("Motohiro Hata meets Sakamichi no Apollon", ("Motohiro Hata",)),
    ("Tortoise Matsumoto (Ulfuls)", ("Tortoise Matsumoto",)),
    ("Yasutaka Nakata (CAPSULE)", ("Yasutaka Nakata",)),
    (
        "Triomatic and Minawa",
        (
            "Triomatic",
            "Minawa",
        ),
    ),
    ("ichigo from Kishida Kyoudan &THE Akeboshi Rockets", ("ichigo",)),
    (
        "GHOST ORACLE DRIVE feat. Sen to Chihiro Chicchi (BiSH)",
        (
            "GHOST ORACLE DRIVE",
            "CENT CHiHiRO CHiTTiii",
        ),
    ),
    (
        "TeddyLoid feat. Aina The End (BiSH)",
        (
            "TeddyLoid",
            "AiNA THE END",
        ),
    ),
    (
        "SUGIZO feat. Aina The End (BiSH)",
        (
            "SUGIZO",
            "AiNA THE END",
        ),
    ),
    ("Risa Aizawa (Dempagumi.inc)", ("Risa Aizawa",)),
    (
        "Azusa Enoki to Yume Bouei Shoujo-tai",
        (
            "Azusa Enoki",
            "Yume Bouei Shoujo-tai",
        ),
    ),
    ("KinKi Kids (Koichi Domoto)", ("KinKi Kids",)),
    ("KinKi Kids (Tsuyoshi Domoto)", ("KinKi Kids",)),
    ("MATCHY with QUESTION?", ("MATCHY with QUESTION?",)),
    ("Suu (SILENT SIREN)", ("Sumire Yoshida",)),
    (
        "ZONE&Run Time All Stars",
        (
            "ZONE",
            "Run Time All Stars",
        ),
    ),
    ("☆Taku Takahashi of m-flo", ("Taku Takahashi",)),
    (
        "Q-MHz feat. Mitsuhiro Hidaka a.k.a. SKY-HI",
        (
            "Q-MHz",
            "SKY-HI",
        ),
    ),
    (
        "hitomi & Yukiji",
        (
            "hitomi",
            "Yukiji",
        ),
    ),
    ("aki a.k.a Aki Deguchi", ("aki",)),
    ("ELISA connect EFP", ("ELISA",)),
    (
        "VOICE by Iyami feat. Kenichi Suzumura, Takahiro Sakurai, Yuichi Nakamura, Hiroshi Kamiya, Jun Fukuyama, Daisuke Ono, Miyu Irino",
        (
            "Kenichi Suzumura",
            "Takahiro Sakurai",
            "Yuichi Nakamura",
            "Hiroshi Kamiya",
            "Jun Fukuyama",
            "Daisuke Ono",
            "Miyu Irino",
        ),
    ),
    (
        "VOICE by Iyami feat. Aya Endo, Kenichi Suzumura, Takahiro Sakurai, Yuichi Nakamura, Hiroshi Kamiya, Jun Fukuyama, Daisuke Ono, Miyu Irino",
        (
            "Aya Endo",
            "Kenichi Suzumura",
            "Takahiro Sakurai",
            "Yuichi Nakamura",
            "Hiroshi Kamiya",
            "Jun Fukuyama",
            "Daisuke Ono",
            "Miyu Irino",
        ),
    ),
    ("VOICE by Iyami feat. Osomatsu-san All Stars", ("Osomatsu-san All Stars",)),
    (
        "Hashiguchikanaderiya hugs The Super Ball",
        (
            "Hashiguchikanaderiya",
            "The Super Ball",
        ),
    ),
    ("Yumi Yoshimura (PUFFY)", ("Yumi Yoshimura",)),
    ("Ami Onuki (PUFFY)", ("Ami Onuki",)),
    ("A・ZU・NA", ("A・ZU・NA",)),
]
# 0000

splitting_exception = {}
for split_exception in splitting_exception_list:
    splitting_exception[split_exception[0]] = split_exception[1]
# Splitting Config

# Alternative Artists names
alternative_names = [
    # Spaces
    ["Midori Karashima", "Midori Karashima "],
    ["Akira Sudou", "Akira Sudou "],
    ["Shabana", "Shabana "],
    ["G・GRIP", " G・GRIP"],
    ["Yoshihiro Ike", "Yoshihiro Ike "],
    ["Kaori Nazuka", "Kaori Nazuka "],
    ["Yuka Iguchi", "Yuka Iguchi "],
    ["Kouji Yamamoto", "Koji Yamamoto", "Kouji Yamamoto "],
    ["Toshio Furukawa", "Toshio Furukawa "],
    ["Maiko Hashimoto", "Maiko Hashimoto "],
    # Most likely typo
    ["Seria Fukagawa", "Seria Fukugawa"],
    ["Mina Katahira", "Mina Kitahara"],
    ["Miho Arakawa", "Miho Arikawa"],
    ["Makoto Furukawa", "Makoto Furukara"],
    ["Merumo Hisaoka", "Meruo Hisaoka"],
    ["Yuuko Sanpei", "Yuuko Senpei"],
    ["Sadastic Mika Band", "Sadistic Mika Band"],
    ["Tomoko Nakajima", "Toyoko Nakajima"],
    ["Tamurapan", "Taurapan"],
    ["Kazue Ikura", "Kazu Ikura"],
    ["Takeshi Ike", "Takashi Ike"],
    ["Moyu Arishima", "Moyu Arashima"],
    ["Columbia Yurikago-kai", "Columbia Yurikago Kai", "Columubia Yurikago-kai"],
    ["Masako Iwanaga", "Masako Iwanga"],
    # :weird: english/latin letters = might be credits fault
    ["Maddie Blaustein", "Madeline Blaustein"],
    ["Norman J. Grossfield", "Norman J. Grossfeld"],
    ["Kristen Price", "Kirsten Price"],
    ["skankfunk", "shankfunk"],
    ["Micheal Brody", "Michael Brady"],
    ['Chris "Breeze" Barczynski', 'Chris "Breeze" Barczynsk'],
    ["'Weird Al' Yankovic", '"WEIRD AL" YANKOVIC'],
    ["FENCE OF DEFENSE", "FENCE OF DEFENCE"],
    ["Derek Jackson", "Darek Jackson"],
    # romanization / transcribe, some of them are probably right
    ["Shining Stars", "Golden Stars"],
    ["CHAGE&ASKA", "Chage & Aska"],
    ["alice nine.", "Alice Nine"],
    ["Hana*Hana", "HANA HANA"],
    ["ROOT FIVE", "\u221a5"],
    ["m.o.v.e", "move"],
    ["TAKAKO & THE CRAZY BOYS", "TAKAKO&THE CRAZY BOYS", "Shirai Takako &CRAZY BOYS"],
    ["OKINO.SHUNTARO", "Okino, Shuntaro"],
    ["Kaede", "Kaede☆"],
    ["Larissa Tago Takeda", "Rarisa Tago Takeda"],
    ["Miracle☆StAr", "Miracle StAr"],
    ["Osomatsu-san All Stars", "Osomatsu-san Allstars"],
    ["tofubeats", "tofubeat"],
    ["ZEN-LA ROCK", "ZEN-LA-ROCK"],
    ["SPARK!! SOUND!! SHOW!!", "SPARK!!SOUND!!SHOW!!"],
    ["Dark Cherries", "Dark Cherry"],
    ["FT ISLAND", "FTISLAND"],
    ["Team.Nekokan [Neko]", "Team Nekokan [Neko]"],
    ["Milky Way", "MilkyWay"],
    ["Dainiki LemonAngel", "Dai-II-Ki Lemon Angel", "Niki LemonAngel"],
    ["First Lemon Angels", "Ikki LemonAngel"],
    ["The 5 TEARDROPS", "The5 TEARDROPS"],
    ["Aimee Blackschleger", "Aimee B", "Aimee B."],
    ["Coalamode.", "Coala mode."],
    ["Bakufu Slump", "Bakufu-Slump"],
    ["GagagaSP", "Gagaga SP"],
    ["Escargot", "Escargo"],
    ["Kabuki Rocks", "Kabukibu Rocks"],
    ["Bonny Jacks", "Bonnie Jacks"],
    ["Kaguyahime", "Kaguya-hime"],
    ["Children's Chorus", "Children Chorus"],
    ["The Blessin' Four", "The Blessen Four"],
    ["FURIL", "FURIL'"],
    ["Becky♪#", "Becky"],
    ["Dance Man", "Dance☆Man"],
    ["mihimaru GT", "mihimaruGT"],
    ["Platinum Peppers Family", "Platinum Pepper Family"],
    ["※-mai-", "※-mai"],
    ["SHINES", "SHINE'S"],
    ["Russell Velázquez", "Russell Velazquez"],
    ['Minako"mooki"Obata', 'Minako "mooki" Obata'],
    ["Pink Piggies", "Pink Piggys"],
    ["WIZ-KISS", "WIZ•KISS"],
    ["T's WORKSHOP", "T's WORK SHOP"],
    ["RINK(Mistera Feo)", "RINKU (Mistera Feo)"],
    # capitalization, some of them are probably right, especially the english one/those written in latin letters
    ["The S.H.E", "The s.h.e"],
    ["Passepied", "PASSEPIED"],
    ["Ya-Ya-Yah", "YA-YA-yah"],
    ["PERSONZ", "Personz"],
    ["Yuuka Nishio", "Rinku", "RINKU"],
    ["Yoko Kanno", "Gabriela Robin", "gabriela robin"],
    ["Steve Conte", "steve conte"],
    ["millio", "Millio"],
    ["Maximum The Hormone", "Maximum the Hormone", "MAXIMUM THE HORMONE"],
    ["Maaya Sakamoto", "maaya sakamoto"],
    ["hitomi", "Hitomi", "Hitomi Kuroishi"],
    ["Raj Ramayya", "raj ramayya"],
    ["Hillbilly Bops", "HillBilly Bops"],
    ["Gackt", "GACKT"],
    ["Luna Goami", "LUNA GOAMI"],
    ["Scha Dara Parr", "SCHA DARA PARR"],
    ["Soraru", "soraru"],
    ["Rumania Montevideo", "rumania montevideo"],
    ["Sweet Velvet", "sweet velvet"],
    ["The ROOTLESS", "THE ROOTLESS"],
    ["Peek-a-Boo", "Peek-A-Boo"],
    ["Salia", "SALIA"],
    ["Tarako", "TARAKO"],
    ["The Collectors", "the collectors", "THE COLLECTORS"],
    ["Faylan", "faylan"],
    ["Sunbrain", "sunbrain"],
    ["Brenda Vaughn", "BRENDA VAUGHN"],
    ["Nomico", "nomico"],
    ["ko-saku", "Ko-saku"],
    ["pigstar", "Pigstar"],
    ["moumoon", "Moumoon"],
    ["Karen GUY'S", "Karen GUY's"],
    ["Kimaguren", "kimaguren"],
    ["kasarinchu", "Kasarinchu"],
    ["singman", "Singman"],
    ["Nothing's Carved In Stone", "Nothing's Carved in Stone"],
    ["Official HIGE DANdism", "Official HiGE DANdism"],
    ["KíRíSáMé UNDERTAKER", "KIRISAME UNDERTAKER", "Kirisame Undertaker"],
    ["Flower", "FLOWER"],
    ["smileY inc.", "SmileY inc."],
    ["team Hiiragi", "Team Hiiragi"],
    ["hitorie", "Hitorie"],
    ["AOZU", "Aozu"],
    ["Ushiro kara Haiyori-tai B", "Ushiro Kara Haiyori-tai B"],
    ["yosh", "Yosh", "yosh(Survive Said The Prophet)"],
    ["CHINO", "Chino"],
    ["DAOKO", "daoko"],
    ["Wakana", "WAKANA"],
    ["Fire Bomber", "FIRE BOMBER"],
    ["EMILY BINDIGER", "Emily Bindiger"],
    ["Hound Dog", "HOUND DOG"],
    ["ORIGA", "Origa"],
    ["dream", "Dream"],
    ["SV Tribe", "SV TRIBE"],
    ["LAMA", "Lama"],
    ["AKINO", "Akino"],
    ["UNDER GRAPH", "Under Graph"],
    ["Chatmonchy", "chatmonchy"],
    ["Uyontana", "Wu yon ta na"],
    ["UNICORN", "Unicorn"],
    ["Shounen Shoujo Gasshou-dan Mizuumi", "Mizuumi Boys & Girls Chorus"],
    # -bu -tai & co
    [
        "Nishirokugou Shounen Gasshou-dan",
        "Nishirokugo Shounen Gasshou-dan",
    ],
    # ou/o/oh/oo (no ô)
    ["Akemi Satou", "Akemi Sato"],
    ["Yoko Yamauchi", "Youko Yamauchi"],
    ["Tokiko Katou", "Tokiko Kato"],
    ["Akari Kitou", "Akari Kito"],
    ["Shounan no Kaze", "Shonan no Kaze"],
    ["Haruka Tojo", "Haruka Toujou"],
    ["Doubutsu Biscuit", "Doubutsu Biscuits"],
    ["Haruna Ooshima", "Haruna Oshima"],
    ["Shuka Saito", "Shuka Saitou"],
    ["Shintaro Asanuma", "Shintarou Asanuma"],
    ["Otome Shintou", "Otome Shinto"],
    ["Hoshi no Shoujo-tai", "Hoshi no Shoujo-tai☆"],
    ["Tomohisa Sakou", "Tomohisa Sako"],
    ["Ayuru Oohashi", "Ayuru Ohashi"],
    ["Kanae Itou", "Kanae Ito"],
    ["Yurika Ooyama", "Yurika Ohyama"],
    ["Aya Endou", "Aya Endo"],
    ["Momoko Saitou", "Momoko Saito"],
    ["Chiaki Osawa", "Chiaki Oosawa"],
    ["Kouji Yusa", "Koji Yusa"],
    ["Ryouko Sano", "Ryoko Sano"],
    ["Takurou Yoshida", "Takuro Yoshida"],
    ["Kouhei Doujima", "Kohei Dojima"],
    ["Ayaka Saitou", "Ayaka Saito"],
    ["Hitomi Tohyama", "Hitomi Toyama"],
    ["Youko Honna", "Yoko Honna"],
    ["Kyouko Hikami", "Kyoko Hikami", "Hikami Kyoko"],
    ["Miwako Saitou", "Miwako Saito"],
    ["Kouichi Yamadera", "Koichi Yamadera", "Kouchi Yamadera"],
    ["Shouko Suzuki", "Shoko Suzuki"],
    ["Youko Nagayama", "Yoko Nagayama"],
    ["Miki Itou", "Miki Ito"],
    ["Tesshou Genda", "Tessho Kenda"],
    ["Shou Hayami", "Sho Hayami"],
    ["Kousei Asami", "Kosei Asami"],
    ["Shizuru Ootaka", "Shizuru Otaka"],
    ["YUKA", "Yuka Sato", "Yuka Satou"],
    ["Shouko Minami", "Shoko Minami"],
    ["Shirou Sagisu", "Shiro Sagisu"],
    ["Ryoutarou Okiayu", "Ryotaro Okiayu"],
    [
        "Ichiro Mizuki",
        "Ichirou Mizuki",
        "Ichrio Mizuki",
        "Ichiro",
        "Mizuking",
    ],
    ["Unshou Ishizuka", "Unsho Ishizuka"],
    ["Yoko Hikasa", "Hibiki from BEST FRIENDS!"],
    ["Saori Goto", "Saori Gotou"],
    ["Shoujobyo", "Shoujobyou"],
    ["Natsuki Kato", "Natsuki Katou"],
    ["Reina Kondo", "Reina Kondou"],
    ["Kyoko Tsuruno", "Kyouko Tsuruno"],
    ["Shou Nogami", "Sho Nogami"],
    ["Minyou Girls", "Minyo Girls"],
    ["Yui Kondou", "Yui Kondo"],
    ["Souma Saito", "Souma Saitou", "Soma Saito"],
    ["Azusa Satou", "Asuza Satou"],
    ["Kenjiro Tsuda", "Kenjirou Tsuda"],
    ["Satomi Satou", "Satomi Sato"],
    ["Satoru Kousaki", "Satoru Kosaki", "Satoru Kosaki (MONACA)"],
    ["Yo Hitoto", "You Hitoto"],
    ["Ryou Horikawa", "Ryo Horikawa"],
    ["Yougo Kouno", "Yogo Kono"],
    ["Youko Seri", "Yoko Seri"],
    ["Kyoko Okada", "Kyouko Okada"],
    ["Midori Kato", "Midori Katou"],
    ["Tsunehiko Kamijou", "Tsunehiko Kamijo"],
    ["Kyoko Koizumi", "Kyouko Koizumi"],
    ["Souichiro Hoshi", "Soichiro Hoshi", "Souichirou Hoshi"],
    ["Yoko Ueno", "Youko Ueno", "Yoko", "yoko"],
    ["Kota Shinzato", "Kouta Shinzato"],
    ["Sayuri Saitou", "Sayuri Saito"],
    ["Watarirouka Hashiritai 7", "Watarirouka Hashiritai"],
    ["Hideki Saijou", "Hideki Saijo"],
    ["Kumiko Endou", "Kumiko Endo"],
    ["Koji Tsujitani", "Kouji Tsujitani"],
    ["Shinichirou Miki", "Shinichiro Miki"],
    ["Koh Ikeda", "Kou Ikeda"],
    ["Youki Kudoh", "Yuuki Kudo"],
    ["Reiko Omori", "Reiko Oomori"],
    ["Choo", "Cho", "Yuuichi Nagashima"],
    ["Fumio Otsuka", "Fumio Ootsuka"],
    ["Nobuyo Oyama", "Nobuyo Ooyama"],
    ["Sayaka Ohara", "Sayaka Oohara"],
    ["Akio Ootsuka", "Akio Ohtsuka"],
    ["Akane Oomae", "Akane Omae"],
    ["Toshiyuki Omori", "Toshiyuki Oomori"],
    ["Toru Ohkawa", "Tooru Ookawa"],
    ["Ryota Osaka", "Ryota Ohsaka"],
    ["Taeko Onuki", "Taeko Ohnuki"],
    ["Toshiyuki Ohsawa", "Yoshiyuki Ohsawa"],
    # uu/u
    ["Ikuko", "KUKO", "KŪKO"],
    ["Yuji Mitsuya", "Yuuji Mitsuya"],
    ["Yuko Imada", "Yuuko Imada"],
    ["Yuuka Morishima", "Yuka Morishima"],
    ["Yuusuke Shirai", "Yusuke Shirai"],
    ["Yuka Aisaka", "Yuuka Aisaka"],
    ["Yuu Ayase", "Yu Ayase"],
    ["Yu Shimamura", "Yuu Shimamura"],
    ["Yuuto Suzuki", "Yuto Suzuki"],
    ["Yuki Hayashi", "Yuuki Hayashi"],
    ["Yuuki Ono", "Yuki Ono"],
    ["Kyuu Sakamoto", "Kyu Sakamoto"],
    ["Yuuko Kaida", "Yuko Kaida"],
    ["Yuko Gibu", "Yuuko Gibu"],
    ["Yuuya Matsushita", "Yuya Matsushita"],
    ["Shuuhei Kita", "Shuhei Kita"],
    ["Yuuki Kanno", "Yuki Kanno"],
    ["Yuuichi Nakamura", "Yuichi Nakamura"],
    ["Fudanjuku", "Fuudanjuku"],
    ["Yuuna Inamura", "Yuna Inamura"],
    ["Yu Kobayashi", "Yuu Kobayashi", "Smith"],
    ["Yuu Nakamura", "Yu Nakamura"],
    ["Yuko Ishikawa", "Yuuko Ishikawa"],
    ["Yuko Tsuburaya", "Yuuko Tsuburaya"],
    ["Yuki Masuda", "Yuuki Masuda"],
    ["Yusuke Nakamura", "Yuusuke Nakamura"],
    ["Yuuko Miyamura", "Yuko Miyamura"],
    ["Kayoko Ishuu", "Kayo Ishu"],
    ["Yuko Kobayashi", "Yuuko Kobayashi"],
    ["Yuuko Kawai", "Yuko Kawai"],
    ["Yuko Mizutani", "Yuuko Mizutani"],
    # other weird syllables
    ["Riu Konaka", "Riyu Konaka"],
    ["Satomi Majima", "Satomi Mashima"],
    ["Mika Okudoi", "Mica Okudoi", "Re-Kiss"],
    ["Kaoru Sasajima", "Kahoru Sasajima"],
    ["Machico Kawana", "Machiko Kawana"],
    ["Rina Honizumi", "Rina Honnizumi"],
    # Prob fine
    ["Buzy", "BUZY", "COLOR"],
    ["GALNERYUS", "Galneryus"],
    ["REOL", "Reol"],
    ["SILENT SIREN", "Silent Siren"],
    ["UCO", "uco"],
    ["THE ALFEE", "ALFEE"],
    ["Gospellers", "The Gospellers"],
    ["The Green Peas", "Green Peas"],
    ["Howmei Girls", "the Howmei Girls"],
    ["The Street Sliders", "Street Sliders"],
    ["THE SPIDERS FROM MARS", "SPIDERS FROM MARS"],
    ["MIWA (BRAVE BIRD)", "MIWA BRAVEBIRD"],
    ["Hikari GENJI SUPER5", "GENJI Super 5"],
    # FINE
    ["MAKE-UP", "MAKE UP PROJECT"],
    ["fripSide", "fripSide NAO project!"],
    ["Norio Sakai", "Locomoriser"],
    ["Naoki Takao", "Naoki", "Locomokaiser"],
    ["Aya Nozawa", "aya"],
    ["Kasumi Matsumura", "KASUMI"],
    ["Mahora Gakuen Chuutoubu 2-A", "Mahora Gakuen Chuutoubu 3-A"],
    ["Azumi Asakura", "Azumi Yamamoto"],
    ["Team Syachihoko", "TEAM SHACHI"],
    ["Nanami Yamashita", "kiracCHU"],
    ["Kuniaki Haishima", "Mr. Haishima"],
    ["Yoko Ishida", "NANA", "Mizuho", "YOKO"],
    ["Sachiko Kobayashi", "Sachi"],
    ["Juri Ihata", "Juri"],
    ["Ame no Kisaki Shoujo Gasshou-dan", "Ame no Kisaki Sisters"],
    ["CIVILIAN", "Lyu:Lyu"],
    ["Sanae Shintani", "Sana"],
    ["ZAQ", "Rina Isaku"],
    ["Tokyo Shounen Shoujo Gasshou-tai", "The Member of LSOT"],
    ["Moka Kamishiraishi", "adieu"],
    ["Kaori Nishina", "ASAKO"],
    ["Hatsune Miku", "Kemurikusa"],
    ["Yukari Konno", "Yukari"],
    ["Ayumi.", "Yozora Orihime"],
    ["Mai Kuraki", "Mai-k"],
    ["Yuko Goda", "YuU"],
    ["DOBERMAN INFINITY", "DOBERMAN INC"],
    ["NHK Tokyo Jidou Gasshou-dan", "Atoms"],
    ["Fuki", "Fuki Commune"],
    ["Mayuki Hiramatsu", "Mayukiss"],
    ["Hazuki Tanaka", "Hazuki"],
    ["Yoko Takahashi", "YAWMIN"],
    ["Shiena Nishizawa", "EXiNA"],
    ["School Food Punishment", "school food punishment"],
    ["Titine Schijvens", "Tea Tea Ne"],
    ["Elena Gobbi Frattini", "LOLITA"],
    ["Melody Castellari", "JEE BEE"],
    ["Gianni Coraini", "KEN LASZLO"],
    ["Ennio Zanini", "FASTWAY", "DUSTY"],
    ["Chris Lindh", "BOBBY SUMMER"],
    ["Christian Codenotti", "ACE"],
    [
        "Clara Moroni",
        "LESLIE PARRISH",
        "CHERRY",
        "DENISE",
        "PRISCILLA",
        "VICKY VALE",
    ],
    [
        "Emanuela Gubinelli",
        "JILLY",
        "ANIKA",
    ],
    ["Nathalie Aarts", "NATHALIE"],
    ["Daniela Rando", "MADISON"],
    ["Giancarlo Pasquini", "DAVE RODGERS"],
    [
        "Giordano Gambogi",
        "TRIUMPH",
        "D-TEAM",
        "DJ FORCE",
        "KASANOVA",
        "MONEY MAN",
        "MR.M",
        "MR. M",
        "MR.MUSIC",
    ],
    ["Claudio Magnani", "ATRIUM", "P. STONE", "TOBY ASH", "SPEEDMAN"],
    [
        "Davide Di Marcantonio",
        "ROBERT PATTON",
        "THOMAS T",
        "DAVID DIMA",
        "DREAM FIGHTERS",
        "DAVE MC LOUD",
        "DAVE Mc LOUD",
        "LOU GRANT",
    ],
    ["Michela Capurro", "MICKEY B.", "MICKEY B"],
    ["Giacomo Caria", "CHRIS T", "NEO"],
    ["Tomas Marin", "MEGA NRG MAN", "DERRECK SIMONS", "MR.GROOVE"],
    [
        "Maurizio De Jorio",
        "MAX COVERI",
        "D. ESSEX",
        "D.ESSEX",
        "MARKO POLO",
        "MORRIS",
        "NIKO",
        "KEVIN JOHNSON",
        "DEJO",
    ],
    ["Fernando Bonini", "BON", "DR.LOVE", "DR.LPVE", "NANDO"],
    ["Simone Valeo", "DAVE SIMON", "SYMBOL", "TENSION", "OVERLOAD"],
    ["Susi Amerio", "SUSAN BELL"],
    ["Sara Righetto", "SARA"],
    ["Annerley Gordon", "ANNALISE"],
    ["Denise De Vincenzo", "NUAGE"],
    ["Roberto Festari", "JOE BANANA", "GARCON"],
    ["Federico Rimonti", "JUNGLE BILL", "FRANZ TORNADO"],
    ["Danillo Lutzoni", "Wild"],
    ["Karen J. Wainwright", "WAIN L", "KAREN"],
    ["Michelle Vanni", "MICHAEL BEAT"],
    ["Antonella Melone", "STARLET"],
    ["Gian Luca Anceschi", "BLACK POWER"],
    ["Luca Torchiani", "EUROFUNK", "PAUL HARRIS", "J-STARK"],
    ["Silvia Ghidini", "VIVI"],
    ["Silvio Rondelli", "LEO RIVER"],
    ["Evelin Malferrari", "FUTURA"],
    ["Marco Rancati", "DANIEL"],
    ["Mario Tarantola", "TERENCE HOLLER"],
    ["Jessa Stebbins", "KEN BLAST"],
    ["Fabio Tordiglione", "J.STORM-GTR"],
    ["Stefano Brandoni", "DIGITAL PLANET", "SPOCK"],
    ["Yasuhiko Hoshino", "dino starr"],
    ["Manuel Caramori", "MANUEL"],
    ["Matteo Setti", "MATT LAND"],
    ["Alessia De Boni", "PAMSY"],
    ["Sara Olivari", "MISTIKA"],
    ["Riccardo Majorana", "RICH HARD"],
    ["Christian De Leo", "IDOL", "DAVE", "CHRIS STANTON"],
    ["Melissa Bianchini", "MELISSA WHITE"],
    ["Filippo Perbellini", "PHIL"],
    ["Filippo Cordioli", "JAGER"],
    ["Alex De Rosso", "ACE WARRIOR"],
    ["Davide Budriesi", "JEAN LOVE", "BUDDY BO"],
    ["Fabrizio Rizzolo", "BRAIN ICE"],
    ["Roberto Tiranti", "POWERFUL T."],
    ["Nicola Mansueto", "NICK MANSELL"],
    ["Massimo Galli", "MIKE DANGER"],
    ["Isabella Branca", "THE WONDER GIRLS"],
    ["Anna Benedetti", "ANNIE"],
    ["Diego Mancino", "DE LA VEGA"],
    [
        "Elena Ferretti",
        "ELENA FERRETTI",
        "HELENA",
        "SOPHIE",
        "VICTORIA",
        "QUEEN OF TIMES",
        "VALENTINA",
    ],
    ["Rin", "Mami Suenaga"],
    ["Ayano Yamamoto", "Super Sonico"],
    ["Nemu Yumemi", "Nemu"],
    ["Waka Kirishima", "Waka from STAR☆ANIS"],
    ["Fuuri Uebana", "Fuuri from STAR☆ANIS"],
    ["Yuna Ichikura", "Yuna from STAR☆ANIS"],
    ["Remi Mitani", "Remi from STAR☆ANIS"],
    ["Eri Aino", "Eri from STAR☆ANIS"],
    ["Risuko Sasakama", "Risuko from STAR☆ANIS"],
    ["Ruka Endou", "Ruka from STAR☆ANIS", "Ruka from AIKATSU\u2606STARS!"],
    ["Sunao Yoshikawa", "Sunao from STAR☆ANIS"],
    ["Moe Yamazaki", "Moe from STAR☆ANIS"],
    ["Mona Tomoyama", "Mona from STAR☆ANIS", "Mona from AIKATSU\u2606STARS!"],
    ["Yuniko Morishita", "Yuniko from STAR☆ANIS"],
    ["Miki Mirai", "Miki from AIKATSU☆STARS!"],
    ["Miho Amane", "Miho from AIKATSU☆STARS!"],
    ["Nanase Matsuoka", "Nanase from AIKATSU☆STARS!"],
    ["Kana Hoshizaki", "Kana from AIKATSU☆STARS!"],
    ["Sena Horigushi", "Sena from AIKATSU☆STARS!"],
    ["Rie Fujishiro", "Rie from AIKATSU☆STARS!"],
    ["Akane Matsunaga", "Aine from BEST FRIENDS!"],
    ["Ibuki Kido", "Mio from BEST FRIENDS!"],
    ["Karen Miyama", "Maika from BEST FRIENDS!"],
    ["Yui Ninomiya", "Ema from BEST FRIENDS!"],
    ["Azusa Tadokoro", "Karen from BEST FRIENDS!"],
    ["Emiri Suyama", "Sakuya from BEST FRIENDS!"],
    ["Yuuki Kuwahara", "Kaguya from BEST FRIENDS!"],
    ["Saori Oonishi", "Alicia from BEST FRIENDS!"],
    ["Rin Aira", "Wakaba from BEST FRIENDS!", "Raki from BEST FRIENDS!"],
    ["Kensuke Ushio", "agraph"],
    ["STEREO DIVE FOUNDATION", "R・O・N"],
    ["Yukana", "Yukana Nogami"],
    ["Ai Otsuka", "LOVE"],
    ["YU-KI", "Yuuki Kitamura"],
    ["KAORI", "Midori Kawana"],
    ["Akino Arai", "AKINO arai"],
    ["saji", "phatmans after school"],
    ["Ai Kakuma", "eye"],
    ["Hibiku Yamamura", "hibiku"],
    ["Milky Holmes Feathers", "Feathers"],
    ["LAZY", "ULTIMATE LAZY for MAZINGER"],
    ["SUEMITSU & THE SUEMITH", "Atsushi Suemitsu"],
    ["UraShimaSakataSen", "Fourpe"],
    ["Meltic StAr", "Meltic"],
    ["AiM", "Ai Maeda"],
    ["Miracle☆Kiratts", "Kiratts"],
    ["Fruit Tart", "Tart"],
    ["Takahiro Sakurai", "MC469MA"],
    ["Cream Anmitsu", "Anmitsu"],
    ["Lupintic Six", "Lupintic Six with Friends", "Lupintic Five with Friends"],
    ["Momoiro Clover Z", "Momoiro Clover", "MomoClo-chan Z"],
    ["Yuuka Saegusa", "U-ka saegusa"],
    ["MIO", "MIQ"],
    ["Special Kids", "Special Kids as chorus"],
    ["DAIGO☆STARDUST", "DAIGO"],
    ["Honey Bee(YURIA)", "Honey Bee"],
    ["Mayumi Morinaga", "senya (Yuuhei Satellite)"],
    ["marina", "Girls Dead Monster (marina)"],
    ["LiSA", "Girls Dead Monster (LiSA)"],
    ["Lisa Komine", "lisa"],
    ["little by little", "Satou-san to Suzuki-kun"],
    ["yoshiki*lisa", "Risa Yoshiki"],
    ["TWO-MIX", "II MIX⊿DELTA"],
    ["T.M.Revolution", "Takanori Nishikawa"],
    ["Mai Mizuhashi", "MARiA"],
    ["Konomi Suzuki", "Koneko Yasagure"],
    ["Hiroyuki Sawano", "SawanoHiroyuki[nZk]"],
    ["GRAN RODEO", "GRANRODEO"],
    ["angela", "ANGELA"],
    ["Minami", "Minami Kuribayashi", "exige"],
    ["Yumi Matsutoya", "Yumi Arai"],
    ["Ushio Hashimoto", "Ushio"],
    ["Ai Kawashima", "♡"],
    ["BUD VIRGIN LOGIC", "BUDVIRGINLOGIC"],
    ["Hyadain", "Nyadain"],
    ["STYLE FIVE", "Iwatobi Machi no Yukai na Nakama-tachi"],
    ["TAKUMI iwasky", "TAKUMI iwasaky"],
    ["Ho-Kago Tea Time - HTT", "Ho-Kago Tea Time"],
    ["Yuki Kajiura", "Fion"],
    [
        "Anna Tsuchiya",
        "ANNA inspi' NANA(BLACK STONES)",
        "ANNA TSUCHIYA inspi' NANA(BLACK STONES)",
    ],
    ["STEEL ANGELS", "Angels"],
    ["Aki Toyosaki", "Melori"],
    ["Current of Air", "COA"],
    ["ERIKA", "Erika Masaki"],
    ["DENKI GROOVE", "Denki Groove"],
    ["Tokyo Arakawa Shounen Shoujo Gasshou-tai", "Arakawa Shounen Shoujo Gasshou-tai"],
    ["Meistersinger", "Tokyo Meistersinger"],
    [
        "7-nin no Mugiwara Kaizoku-dan",
        "Mugiwara Kaizoku-dan",
    ],
    ["Yuka Iwahashi", "Coco Panna"],
    ["Fushigi Hakken no Uta Club", "FHK Fushigi Hakken no Uta Club"],
    ["Rosenburg Engel", "Rosenburg Alptraum"],
    ["White Ryuu", "Hakuryuu"],
    ["Spica", "Team Spica"],
    ["Natsuko Aso", "Nyatsuko Asou"],
    ["Yui Horie", "Miss Monochrome"],
    ["Sakurakko Club Sakura-gumi", "Sakurakko Club"],
    ["Nakayoshi Mantan! Valac Ikka", "Valac Ikka"],
    ["Tommy heavenly\u2076", "Tommy february\u2076"],
    ["Koinu", "Riinu (Sutopuri)"],
    ["Haruka Mimura", "VJ Only"],
    ["Kashitaro Ito", "Kashitaro Itou", "RAGE"],
    ["Ai Shimizu", "Minawa"],
    ["Ayako Kawasumi", "Mahoro"],
    # ["KENN", "SHINJI"],
    ["Eijiro Tai", "Tomo", "TOMO"],
    ["Angel-tai", "Angel '03"],
    ["Rita", "Riko Hirai"],
    ["Ayaka Ohashi", "Mirai from BEST FRIENDS!"],
    ["Mariko Kouda", "miyuki"],
    ["ASCA", "Asuka Oukura"],
    ["meg rock", "GUMI", "Megumi Hinata"],
    ["Benjamin Anderson", "Benjamin"],
    ["Ai Ichikawa", "I.C.I."],
    ["Junjou no Afilia", "Afilia Saga East", "Afilia Saga"],
    ["Yui Itsuki", "Yui"],
    ["Aimi", "KYOKO"],
    ["Risa Tsumugi", "SAKI"],
    ["Natsumi Hirajima", "RIKA"],
    ["Rihona Kato", "TSUBAKI"],
    ["Hazuki Tanda", "MIYU"],
    ["Showtaro Morikubo", "KOOGY"],
    ["Azusa Kataoka", "Azusa Enoki"],
    ["Jun Morioka", "Little Viking"],
    ["MAGIC OF LiFE", "DIRTY OLD MEN"],
    ["coaltar of the deepers", "COALTAR OF THE DEEPERS"],
    ["Yukiji", "Akiko Suzuki"],
    ["aki", "Aki"],
    ["Sound Team jdk", "Falcom Sound Team jdk"],
    # I need to fix
    [
        "Hironobu Kageyama",
        "Hironobu Kageyama (JAM Project)",
        "JAM Project (Hironobu Kageyama)",
    ],
    ["Hiroshi Kitadani", "Hiroshi Kitadani (JAM Project)"],
    ["Masami Okui", "MASAMI", "Masami Okui (JAM Project)"],
    [
        "Yoshiki Fukuyama",
        "Yoshiki Fukuyama (JAM Project)",
        "JAM Project (Yoshiki Fukuyama)",
    ],
    ["Masaaki Endoh", "Masaaki Endoh (JAM Project)", "JAM Project (Masaaki Endoh)"],
    ["765PRO ALLSTARS", "765PRO ALL STARS", "765PRO"],
    ["Precure All-Stars 21", "Precure All Stars"],
    [
        "Tokyo Konsei Gasshou-dan",
        "Shigeru Yamada (Tokyo Konsei Gasshou-dan)",
    ],
]
# Alternative Artists names
# 0000

#
# Awake / Awaking Aquarian Age

# Todo manually after everything is done:
""" SAME GROUP WITH DIFFERENT MEMBER CONFIGURATIONS
jam project
walkure

_________ DIFFERENT ARTIST WITH SAME NAME
karin takahashi
hinata satou

________________ Lead vs BACK UP SINGERS
K-ON 5nin vers + Samidare 20 Love + Gohan wa Okazu + Curry
Dr. Slump All Stars (taeko kawada)
Obocchaman-kun
Yumeno Uta to Yume bouei
humming bird
move etc..
smith with MON
nanjo with prism mates
glitter green
roselia
bang dream
RONDO
Ourin Sisters
eclipse
most of sbr
friends (horimiya)
Uchuu Shoujo Vanaren-tai
neuron cream soft
Sol/Lull BOB
teikoku kageki dan sakurai taisen 2
golden ixion bomber dt

weird stuff
DEATH DEVIL only instrumental
hokago tea time only instrumental
team shachi only instrumental

performer not singer
yoshida brothers
Kenken
"""
