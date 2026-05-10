from dataclasses import dataclass


@dataclass
class MusicbrainzArtistAlias:
    sort_name: str
    name: str
    locale: str | None
    type: str | None
    primary: bool | None
    begin_date: str | None
    end_date: str | None


@dataclass
class MusicbrainzArtistArea:
    id: str
    type: str
    type_id: str
    name: str
    sort_name: str
    life_span: dict[str, str | None]


@dataclass
class MusicbrainzArtistTag:
    count: int
    name: str


@dataclass
class MusicbrainzArtist:
    id: str
    type: str
    type_id: str
    score: int
    gender_id: str
    name: str
    sort_name: str
    gender: str
    country: str
    area: MusicbrainzArtistArea
    begin_area: MusicbrainzArtistArea
    ipis: list[str]
    isnis: list[str]
    life_span: dict[str, str | None]
    aliases: list[MusicbrainzArtistAlias]
    tags: list[MusicbrainzArtistTag]


# {
#       "id": "a7d64787-c8ae-4aee-a365-30c5a8e91fe3",
#       "type": "Person",
#       "type-id": "b6e035f4-3ce9-331c-97df-83397230b0df",
#       "score": 100,
#       "gender-id": "36d3d30a-839d-3eda-8cb3-29be4384e4a9",
#       "name": "薛之谦",
#       "sort-name": "Xue, Joker",
#       "gender": "male",
#       "country": "CN",
#       "area": {
#         "id": "7c81bb69-a99b-3487-b6d4-0f76d7a29ca0",
#         "type": "Country",
#         "type-id": "06dd0ae4-8c74-30bb-b43d-95dcedf961de",
#         "name": "China",
#         "sort-name": "China",
#         "life-span": {
#           "ended": null
#         }
#       },
#       "begin-area": {
#         "id": "dec4979e-c0a3-469c-a052-cee5f1e71de9",
#         "type": "City",
#         "type-id": "6fd8f29a-3d0a-32fc-980d-ea697b69da78",
#         "name": "Shanghai",
#         "sort-name": "Shanghai",
#         "life-span": {
#           "ended": null
#         }
#       },
#       "ipis": [
#         "00519718920"
#       ],
#       "isnis": [
#         "0000000466663480"
#       ],
#       "life-span": {
#         "begin": "1983-07-17",
#         "ended": null
#       },
#       "aliases": [
#         {
#           "sort-name": "Xue, Zhiqian",
#           "name": "薛之謙",
#           "locale": "zh_Hant",
#           "type": null,
#           "primary": true,
#           "begin-date": null,
#           "end-date": null
#         },
#         {
#           "sort-name": "Xue, Zhiqian",
#           "name": "薛之谦",
#           "locale": "zh_Hans",
#           "type": null,
#           "primary": true,
#           "begin-date": null,
#           "end-date": null
#         },
#         {
#           "sort-name": "Xue, Joker",
#           "type-id": "894afba6-2816-3c24-8072-eadb66bd04bc",
#           "name": "薛之谦",
#           "locale": "zh",
#           "type": "Artist name",
#           "primary": true,
#           "begin-date": null,
#           "end-date": null
#         },
#         {
#           "sort-name": "Xue, Zhiqian",
#           "name": "Xue Zhiqian",
#           "locale": null,
#           "type": null,
#           "primary": null,
#           "begin-date": null,
#           "end-date": null
#         },
#         {
#           "sort-name": "Xue, Jacky",
#           "name": "Jacky Xue",
#           "locale": "en",
#           "type": null,
#           "primary": null,
#           "begin-date": null,
#           "end-date": null
#         },
#         {
#           "sort-name": "Xue, Joker",
#           "name": "Joker Xue",
#           "locale": "en",
#           "type": null,
#           "primary": true,
#           "begin-date": null,
#           "end-date": null
#         }
#       ],
#       "tags": [
#         {
#           "count": 1,
#           "name": "mandopop"
#         },
#         {
#           "count": 1,
#           "name": "singer-songwriter"
#         }
#       ]
#     }
