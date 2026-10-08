# Third-party components

The MIT license at the repository root covers VideoHunter's own code only.
The portable distribution retains the bundled Python and package license files.

- Python 3.11: runtime/LICENSE.txt; https://www.python.org/
- yt-dlp: runtime/Lib/site-packages/yt_dlp-2026.8.19.dist-info/; https://github.com/yt-dlp/yt-dlp
- curl_cffi and other runtime packages: see their respective .dist-info license files.
- winotify: runtime/Lib/site-packages/winotify-1.1.0.dist-info/; https://github.com/versa-syahptr/winotify
- FFmpeg / FFprobe: GPL build ffmpeg-N-126374-g089a48eb36-win64-gpl;
  see licenses/FFmpeg-LICENSE.txt. Bundled binaries are copied unchanged from
  the installed yt-dlp.FFmpeg WinGet package. Build project:
  https://github.com/yt-dlp/FFmpeg-Builds ; FFmpeg upstream:
  https://github.com/FFmpeg/FFmpeg/tree/089a48eb36

Third-party components retain their own licenses; they are not relicensed under MIT.
