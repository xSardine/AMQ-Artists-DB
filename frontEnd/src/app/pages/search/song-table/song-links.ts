import type { Song } from '../songs/song';

type AnimeListSite = {
  img: string;
  alt: string;
  label: string;
  getUrl: (song: Song) => string | null;
};

type SongDistLink = {
  label: string;
  infoLabel: string;
  title: string;
  field: 'HQ' | 'MQ' | 'audio';
};

export const ANIME_LIST_SITES: readonly AnimeListSite[] = [
  {
    img: 'assets/img/ANN_Logo.png',
    alt: 'Anime News Network',
    label: 'ANN',
    getUrl: (song) => `https://www.animenewsnetwork.com/encyclopedia/anime.php?id=${song.annId}`,
  },
  {
    img: 'assets/img/MyAnimeList_Logo.png',
    alt: 'MyAnimeList',
    label: 'MAL',
    getUrl: (song) => song.linked_ids?.myanimelist
      ? `https://myanimelist.net/anime/${song.linked_ids.myanimelist}`
      : null,
  },
  {
    img: 'assets/img/AniList_logo.png',
    alt: 'Anilist',
    label: 'AniList',
    getUrl: (song) => song.linked_ids?.anilist
      ? `https://anilist.co/anime/${song.linked_ids.anilist}`
      : null,
  },
  {
    img: 'assets/img/Kitsu_Logo.png',
    alt: 'Kitsu',
    label: 'Kitsu',
    getUrl: (song) => song.linked_ids?.kitsu
      ? `https://kitsu.app/anime/${song.linked_ids.kitsu}`
      : null,
  },
  {
    img: 'assets/img/AniDB_Logo.png',
    alt: 'Anidb',
    label: 'AniDB',
    getUrl: (song) => song.linked_ids?.anidb
      ? `https://anidb.net/anime/${song.linked_ids.anidb}`
      : null,
  },
];

export const SONG_DIST_LINKS = [
  {
    label: '720',
    infoLabel: '720p',
    title: 'Open 720 link',
    field: 'HQ',
  },
  {
    label: '480',
    infoLabel: '480p',
    title: 'Open 480 link',
    field: 'MQ',
  },
  {
    label: 'MP3',
    infoLabel: 'MP3',
    title: 'Open MP3 link',
    field: 'audio',
  },
] as const satisfies readonly SongDistLink[];
