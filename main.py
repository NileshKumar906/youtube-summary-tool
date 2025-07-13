from flask import Flask, request, render_template
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lex_rank import LexRankSummarizer
from googletrans import Translator
from waitress import serve
import re

app = Flask(__name__)

def extract_video_id(url):
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
    return match.group(1) if match else None

def get_transcript(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        try:
            transcript = transcript_list.find_transcript(['en'])
        except NoTranscriptFound:
            transcript = transcript_list.find_generated_transcript(['hi'])

        fetched = transcript.fetch()

        # Fix: handle both dict-based and object-based transcript entries
        full_text = " ".join([
            entry['text'] if isinstance(entry, dict) else entry.text
            for entry in fetched
        ])
        return full_text

    except Exception as e:
        print(f"[Transcript Error]: {e}")
        return None

def summarize_text(text, sentence_count=5):
    parser = PlaintextParser.from_string(text, Tokenizer("english"))
    summarizer = LexRankSummarizer()
    summary = summarizer(parser.document, sentence_count)
    return " ".join(str(sentence) for sentence in summary)

@app.route("/", methods=["GET", "POST"])
def index():
    summary = None
    translated_summary = None
    error = None
    selected_language = "en"

    if request.method == "POST":
        url = request.form.get("youtube_url", "")
        selected_language = request.form.get("language", "en")
        video_id = extract_video_id(url)

        if not video_id:
            error = "Invalid YouTube URL."
        else:
            transcript = get_transcript(video_id)
            if transcript:
                summary = summarize_text(transcript)
                if selected_language != "en":
                    try:
                        translator = Translator()
                        translated_summary = translator.translate(summary, dest=selected_language).text
                    except Exception as e:
                        error = "Translation failed."
                        print(f"[Translation Error]: {e}")
            else:
                error = "Transcript not found."

    return render_template(
        "index.html",
        summary=summary,
        translated_summary=translated_summary,
        error=error,
        selected_language=selected_language
    )

if __name__ == "__main__":
    print("[INFO] Running server on http://localhost:8080")
    serve(app, host="0.0.0.0", port=8080)
