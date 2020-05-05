FLAC = "FLAC"
MP3_128 = "MP3_128"
MP3_256 = "MP3_256"
MP3_320 = "MP3_320"
MP4_RA1 = "MP4_RA1"
MP4_RA2 = "MP4_RA2"
MP4_RA3 = "MP4_RA3"

FALLBACK_QUALITIES = [MP3_320, MP3_128, FLAC]
FORMAT_LIST = [MP3_128, MP3_256, MP3_320, FLAC]

TRACK_FORMAT_MAP = {
    FLAC: {
        "code": 9,
        "ext": ".flac"
    },
    MP3_128: {
        "code": 1,
        "ext": ".mp3"
    },
    MP3_256: {
        "code": 5,
        "ext": ".mp3"
    },
    MP3_320: {
        "code": 3,
        "ext": ".mp3"
    },
    MP4_RA1: {
        "code": 13,
        "ext": ".mp4"
    },
    MP4_RA2: {
        "code": 14,
        "ext": ".mp4"
    },
    MP4_RA3: {
        "code": 15,
        "ext": ".mp3"
    }
}
