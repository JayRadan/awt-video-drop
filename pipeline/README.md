# Anonymous Wolf Trader — video pipeline

Flow (run by Claude in a fresh session):
1. Script: clean the user's analysis into a 300–450 word script (never change the content), save script.txt.
2. Voice: vidiq_voiceover_generate (custom cloned voice if listed, else Brian nPczCjzI2devNBz1zQrb); download MP3 (domain ai-voiceovers.s3.us-east-1.amazonaws.com is allowed).
3. Timing: ffmpeg silencedetect -> silences.txt; python3 timing.py script.txt silences.txt <voice_len> 1.0 -> timing.json
4. Candles: python3 fetch_duka.py 21 candles.json (Dukascopy, may 429 — engine falls back to illustrative candles if the file is missing).
5. Render: python3 engine.py timing.json partA.mp4 0 <mid> and partB.mp4 <mid> <end> in parallel; concat; mux voice with adelay=1000.
6. Thumbnail: vidiq_generate_thumbnail with the channel's last thumbnails as referenceImages.
7. Publish: commit MP4 to videos/ in this repo, push, use raw.githubusercontent.com URL as media in Metricool createScheduledPost (blogId 7357453, youtube, unlisted or public), then git rm + push.
8. Thumbnail/privacy: vidiq_update_video_thumbnail / vidiq_update_video (needs YouTube verification in vidIQ).
