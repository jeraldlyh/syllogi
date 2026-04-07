from typing import Any


import yt_dlp


def _run_ytdlp(url: str, opts: Any | None = None, *, download: bool = False) -> Any:
    """Run yt-dlp with the given URL and options."""

    default_opts: Any = {
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": False,
    }
    if opts:
        default_opts.update(opts)

    with yt_dlp.YoutubeDL(params=default_opts) as ydl:
        # encode url
        result = ydl.extract_info(url=url, download=download)

        return result


print(
    _run_ytdlp(
        url="ytsearch:The Daily Ketchup Podcast We thought Primary School would be EASY! (ft. Saffron Sharpe) | Ketchup Class EP01",
        opts={
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "opus",
                    "preferredquality": "0",
                }
            ],
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
        },
    )
)
