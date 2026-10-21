# How Claude runs the Anonymous Wolf Trader video pipeline (any new session)

User: Jacob. Channel: Anonymous Wolf Trader (@awtforex), id UCcXNpTCVOSpJMSb0PJF0Ksg.
Input: the user pastes a gold/XAUUSD analysis. Output: finished video posted to YouTube.

HARD RULES
- Script = the user's analysis. Clean sentences, add a short intro/transitions/recap only. Never add, remove or change any claim, level, target or view. Never invent targets or invalidation levels.
- Spoken + on-screen: "This is my own analysis and not financial advice."
- YouTube: isAiGeneratedContent true. Description notes visuals/voice are AI-made, analysis is the user's.
- Minimise vidIQ credits: script written by Claude (free); vidIQ only for voice (14 cr/1000 chars) and thumbnail (22 cr). Check vidiq_balance first and tell the user the cost.

SETUP ALREADY IN PLACE
- vidIQ connector (jacob.radan2@gmail.com), channel authorized.
- Metricool connector: brand blogId 7357453, YouTube connected, timezone Europe/Berlin.
- This repo (public) = scripts in pipeline/, temporary drop box in videos/.
- Allowed download domains: ai-voiceovers.s3.us-east-1.amazonaws.com, remotionlambda-useast1-2ei5ch6f3q.s3.us-east-1.amazonaws.com, datafeed.dukascopy.com, stooq.com, query1/query2.finance.yahoo.com.

STEPS
1. add_repo JayRadan/awt-video-drop (push), clone to /home/claude/awt-video-drop, copy pipeline/*.py to /home/claude/gold.
2. script.txt: "Anonymous Wolf Trader. Gold update, <date>." + numbered signals + disclaimer close. 300-500 words, <5000 chars.
3. Voice: vidiq_voiceover_list_voices -> user's custom voice if isCustom else Brian nPczCjzI2devNBz1zQrb. vidiq_voiceover_generate, poll, curl MP3 -> voice.mp3.
4. ffmpeg -i voice.mp3 -af silencedetect=noise=-32dB:d=0.3 -f null - -> silences.txt (lines "start X"/"end X"); python3 timing.py script.txt silences.txt <voice_sec> 1.0 -> timing.json.
5. Candles: python3 -I fetch_duka.py 21 candles.json (Dukascopy rate-limits: few, slow requests; if it fails the engine uses illustrative candles and the description must say so). LEVEL=<key level from analysis>.
6. Edit scene headlines/side-panel text in engine.py to match the new analysis (scenes map to script paragraphs in order). Render: LEVEL=.. python3 engine.py timing.json partA.mp4 0 <mid> and partB.mp4 <mid> <end> in parallel (end = last scene end + 2.5); ffmpeg concat; mux voice with -filter_complex "[1:a]adelay=1000|1000,apad[a]" -shortest. Spot-check frames with Read.
7. Title/description/chapters/hashtags written by Claude.
8. Thumbnail: vidiq_generate_thumbnail with referenceImages = channel's last two thumbnails (vidiq_user_videos). Style: dark trading desk, faceless mannequin presenter, gold chart, 2-3 word gold headline + red subline.
9. Publish: copy MP4 to videos/, commit+push, verify raw.githubusercontent.com URL returns 200, Metricool createScheduledPost (blogId 7357453, youtube, EDUCATION, madeForKids false, isAiGeneratedContent true, privacy public unless user says otherwise, publicationDate ~10 min ahead Europe/Berlin). Once Metricool returns a static.metricool.com media URL, git rm the MP4 and push.
10. send_later ~15 min, then vidiq_update_video_thumbnail with the thumbnail URL. If verification_required: ask user to verify YouTube in vidIQ, then retry.

STYLE: dark navy/black, gold #F2C14E, red #FF4D4D, green #2EE6A6; quant-terminal HUD; candlestick chart with key level as red dashed line labelled by role; side panels (positioning, gamma profile, macro regime); typewriter captions synced to voice; ticker; geometric wolf emblem intro/outro.
