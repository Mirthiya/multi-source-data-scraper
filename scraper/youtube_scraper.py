from pytube import YouTube
from youtube_transcript_api import YouTubeTranscriptApi

def scrape_youtube(video_id):

    url = f"https://youtube.com/watch?v={video_id}"

    try:
        yt = YouTube(url)
        author = yt.author
        publish_date = str(yt.publish_date)
        description = yt.description
    except:
        author = ""
        publish_date = ""
        description = ""

    transcript_text = []

    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        transcript_text = [t["text"] for t in transcript]
    except:
        transcript_text = description.split("\n")

    return {
        "source_url": url,
        "source_type": "youtube",
        "author": author,
        "published_date": publish_date,
        "language": "en",
        "region": "",
        "topic_tags": [],
        "trust_score": "",
        "content_chunks": transcript_text
    }
