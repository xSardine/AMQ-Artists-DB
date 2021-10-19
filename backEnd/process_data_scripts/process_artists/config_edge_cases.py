# Different artist with the same name
{
    "new_artist": {"artist_name": [], "members": [],},
    "linked_song": [],
}
same_name_edge_case = [
    {
        "new_artist": {
            "artist_name": ["TRIGGER"],
            "members": ["Mikako Komatsu", "Chika Anzai"],
        },
        "linked_song": [15281],
    },
    {"new_artist": {"artist_name": ["ELISA"], "members": [],}, "linked_song": [19357],},
    {
        "new_artist": {"artist_name": ["Minami"], "members": [],},
        "linked_song": [22683, 23201],
    },
    {
        "new_artist": {
            "artist_name": ["Friends"],
            "members": ["Emi Okamoto", "Miura Tarou"],
        },
        "linked_song": [28669, 32174],
    },
    {
        "new_artist": {
            "artist_name": ["Kirakira"],
            "members": ["Chika Anzai", "Ibuki Kido", "Yurika Kubo"],
        },
        "linked_song": [23107],
    },
    {
        "new_artist": {
            "artist_name": ["Angels"],
            "members": [
                "Aya Hisakawa",
                "Kikuko Inoue",
                "Shiho Kikuchi",
                "Kotono Mitsuishi",
                "Sakura Tange",
            ],
        },
        "linked_song": [249],
    },
    {
        "new_artist": {"artist_name": ["Sphere"], "members": [],},
        "linked_song": [1176, 8936],
    },
    {
        "new_artist": {"artist_name": ["Maiko"], "members": [],},
        "linked_song": [30215, 30216],
    },
    {
        "new_artist": {"artist_name": ["Eve"], "members": [],},
        "linked_song": [24088, 24571, 30653, 34728, 30712],
    },
    {
        "new_artist": {"artist_name": ["YamaArashi"], "members": [],},
        "linked_song": [28756],
    },
]


template = {"group": "", "alternate_configs": [{"members": [], "linked_song": []}]}

same_group_different_artists = [
    {
        "group": "StylipS",
        "alternate_configs": [
            {
                "members": ["Arisa Noto", "Maho Matsunaga", "Moe Toyota", "Miku Itō"],
                "linked_song": [
                    13264,
                    13265,
                    20633,
                    13731,
                    13807,
                    13809,
                    14336,
                    21216,
                    14835,
                    15241,
                ],
            }
        ],
    },
    {
        "group": "Sanshuu Chuugaku Yuusha-bu",
        "alternate_configs": [
            {
                "members": [
                    "Haruka Terui",
                    "Suzuko Mimori",
                    "Yumi Uchiyama",
                    "Tomoyo Kurosawa",
                    "Juri Nagatsuma",
                    "Kana Hanazawa",
                ],
                "linked_song": [17758, 18468, 35129, 35130],
            }
        ],
    },
    {
        "group": "Oratorio The World God Only Knows",
        "alternate_configs": [
            {"members": ["ELISA", "Lia"], "linked_song": [11379]},
            {"members": ["Saori Hayami"], "linked_song": [13321]},
        ],
    },
    {
        "group": "Kalafina",
        "alternate_configs": [
            {
                "members": [
                    "Keiko Yoshinari",
                    "WAKANA",
                    "Hikaru Masai",
                    "Maya (Kalafina)",
                ],
                "linked_song": [31731, 31732],
            },
            {
                "members": ["Keiko Yoshinari", "WAKANA"],
                "linked_song": [31728, 31729, 31730, 31734, 31735],
            },
        ],
    },
    {
        "group": "ClariS",
        "alternate_configs": [
            {
                "members": ["Clara (ClariS)", "Alice (ClariS)"],
                "linked_song": [
                    10843,
                    "reunion",
                    12406,
                    "Connect",
                    "Naisho no Hanashi",
                    12530,
                    12533,
                    12536,
                    12742,
                    13352,
                    13354,
                    17899,
                    17900,
                ],
            },
        ],
    },
    {
        "group": "MYTH & ROID",
        "alternate_configs": [
            {
                "members": ["Mayu Maeshima"],
                "linked_song": [
                    "STYX HELIX",
                    "STRAIGHT BET",
                    "Paradisus-Paradoxum",
                    15595,
                    18567,
                    "JINGO JUNGLE",
                    "L.L.L.",
                ],
            },
        ],
    },
    {
        "group": "Colors",
        "alternate_configs": [
            {"members": ["Sayaka Kitahara", "Ayahi Takagaki"], "linked_song": [13319]},
            {"members": ["Sayaka Kitahara", "Yu Kobayashi"], "linked_song": [20855]},
        ],
    },
    {
        "group": "eyelis",
        "alternate_configs": [
            {"members": ["Masuda Takeshi"], "linked_song": [12766, 12772]},
        ],
    },
    {
        "group": "Zukkoke Girls",
        "alternate_configs": [
            {
                "members": ["Chisa Yokoyama", "MIYU", "SUZUTOMO"],
                "linked_song": [21828],
            },
        ],
    },
    {
        "group": "Needless\u2605Girls+",
        "alternate_configs": [
            {
                "members": [
                    "Saori Goto",
                    "Emiri Katō",
                    "Eri Kitamura",
                    "Yui Makino",
                    "Minori Chihara",
                ],
                "linked_song": [10209],
            },
        ],
    },
    {
        "group": "supercell",
        "alternate_configs": [
            {
                "members": ["Nagi Yanagi"],
                "linked_song": [8521, 9031, "Kimi no Shiranai Monogatari", 13030],
            },
            {"members": ["Ann", "gaku"], "linked_song": [27198]},
            {"members": ["Ann"], "linked_song": [27214]},
        ],
    },
    {
        "group": "My Melodies",
        "alternate_configs": [
            {
                "members": [
                    "Mai Fukuda",
                    "Sayaka Ueno",
                    "Moeko Koizumi",
                    "Saki Itakura",
                    "Manami Okada",
                ],
                "linked_song": [7583, 7588],
            },
        ],
    },
    {
        "group": "Nagarekawa Girls",
        "alternate_configs": [
            {
                "members": [
                    "Miku Itō",
                    "Sachika Misawa",
                    "Maya Yoshioka",
                    "Inori Minase",
                    "Shiori Izawa",
                    "Mikako Izawa",
                    "Minami Tsuda",
                ],
                "linked_song": [14058],
            },
            {
                "members": [
                    "Miku Itō",
                    "Sachika Misawa",
                    "The rest of the fucking town",
                ],
                "linked_song": [22287],
            },
        ],
    },
    {
        "group": "Almost The Entire Fucking Cast",
        "alternate_configs": [
            {
                "members": [
                    "Miyuki Kanbe",
                    "Daisuke Kishio",
                    "Kumi Yamakado",
                    "Chieko Honda",
                    "Yuki Matsuoka",
                    "Miyako Itō",
                    "Sayori Ishizuka",
                    "Miki Tsuchiya",
                    "Sanae Kobayashi",
                    "Eri Kitamura",
                    "Noriko Shitaya",
                    "Ema Kogure",
                    "Hitomi Terakado",
                    "Yuki Matsuda",
                    "Ryoko Nagata",
                    "Chihiro Kusaka",
                    "Kana Ueda",
                    "Asumi Nakada",
                    "Satomi Arai",
                    "Madoka Kimura",
                    "Hiroaki Miura",
                    "Maria Yamamoto",
                    "Yuuki Tai",
                    "Mayumi Asano",
                    "Kiyotaka Furushima",
                    "Atsushi Kisaichi",
                    "Takako Honda",
                    "Setsu Oohashi",
                    "Yasuyuki Kase",
                    "Keiji Okuda",
                    "Chiaki Takahashi",
                    "Eri Saito",
                    "Ryoko Shintani",
                    "Yuko Goto",
                    "Hajime Iijima",
                    "Takehiro Murozono",
                    "Jun Fukuyama",
                    "Kumiko Nishihara",
                ],
                "linked_song": [27281],
            },
        ],
    },
    {
        "group": "Uchujin",
        "alternate_configs": [
            {"members": ["Noko"], "linked_song": [12639]},
            {"members": ["Mariko Gouto"], "linked_song": [12640]},
            {"members": ["Shiho Nanba"], "linked_song": [12641]},
        ],
    },
    {
        "group": "fripSide",
        "alternate_configs": [{"members": ["nao"], "linked_song": [9498, 22427]}],
    },
    {
        "group": "Veil",
        "alternate_configs": [
            {"members": ["Misuzu Togashi"], "linked_song": [23669]},
            {"members": ["Aoi Tada"], "linked_song": [23668]},
            {"members": ["Lia"], "linked_song": [10780]},
        ],
    },
]
