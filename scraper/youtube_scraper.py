from youtube_transcript_api import YouTubeTranscriptApi

def scrape_youtube(video_id):

    transcript_text = []
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        transcript_text = [t["text"] for t in transcript]
    except:
        transcript_text = []

    data = {
        "source_url": f"https://youtube.com/watch?v={video_id}",
        "source_type": "youtube",
        "author": "",
        "published_date": "",
        "language": "",
        "region": "",
        "topic_tags": [],
        "trust_score": "",
        "content_chunks": transcript_text
    }

    return data
