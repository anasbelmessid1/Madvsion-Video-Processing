
# Your code starts here

import os
import requests
from groq import Groq
from moviepy.video.io.VideoFileClip import VideoFileClip
import re

# Set up API keys from environment variables
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
VIDEO_URL = os.environ.get('VIDEO_URL')

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)

# Define your functions
def download_video(url, output_filename='input_video.mp4'):
    try:
        yt = YouTube(url)
        stream = yt.streams.filter(progressive=True, file_extension='mp4').get_highest_resolution()
        stream.download(filename=output_filename)
        print(f"Video downloaded: {output_filename}")
    except Exception as e:
        print(f"An error occurred while downloading the video: {e}")

def transcribe_with_groq(video_file):
    # Transcribe the video using Groq's distil-whisper model
    try:
        with open(video_file, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(video_file, file.read()),
                model="distil-whisper-large-v3-en",
                response_format="verbose_json",
            )
            transcript = transcription.text
            print("Transcription completed.")
            return transcript
    except Exception as e:
        print(f"An error occurred during transcription: {e}")
        return None

def get_insightful_moments(transcript):
    # Use Groq's Llama 3.2 model to extract insightful moments
    try:
        prompt = f"""
You are an assistant that extracts the most insightful moments from a video transcript. Given the transcript below, identify the top 3 insightful moments. For each moment, provide the timestamp (in seconds) and a brief description.

Transcript:
{transcript}

Output format:
1. Timestamp: [start_time]-[end_time] seconds
   Insight: [description]
2. Timestamp: [start_time]-[end_time] seconds
   Insight: [description]
3. Timestamp: [start_time]-[end_time] seconds
   Insight: [description]
"""
        completion = client.chat.completions.create(
            model="llama-3.2-90b-text-preview",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=1024,
            top_p=1,
            stream=False,
            stop=None,
        )
        insights_text = completion.choices[0].message.content
        print("Insights generated.")
        return insights_text
    except Exception as e:
        print(f"An error occurred while getting insights: {e}")
        return None

def parse_insights(insights_text):
    # Parse the output to extract timestamps and descriptions
    try:
        pattern = r"(\d+)\.\s*Timestamp:\s*(\d+)-(\d+)\s*seconds\s*Insight:\s*(.*?)(?=\n\d+\.|$)"
        matches = re.findall(pattern, insights_text, re.DOTALL)
        insights = []
        for match in matches:
            _, start_time, end_time, description = match
            insights.append({
                "start_time": int(start_time),
                "end_time": int(end_time),
                "description": description.strip()
            })
        print("Insights parsed.")
        return insights
    except Exception as e:
        print(f"An error occurred while parsing insights: {e}")
        return []

def extract_clips(video_file, insights):
    try:
        video = VideoFileClip(video_file)
        for idx, insight in enumerate(insights):
            start_time = insight['start_time']
            end_time = insight['end_time']
            clip = video.subclip(start_time, end_time)
            clip_filename = f"clip_{idx+1}.mp4"
            clip.write_videofile(clip_filename, codec="libx264")
            print(f"Extracted clip: {clip_filename}")
        print("All clips extracted.")
    except Exception as e:
        print(f"An error occurred while extracting clips: {e}")

# Main execution flow
if __name__ == "__main__":
    download_video(VIDEO_URL)
    video_file = 'input_video.mp4'

    transcript = transcribe_with_groq(video_file)
    if transcript:
        insights_text = get_insightful_moments(transcript)
        if insights_text:
            insights = parse_insights(insights_text)
            if insights:
                extract_clips(video_file, insights)
            else:
                print("No insights to extract clips from.")
        else:
            print("Failed to generate insights.")
    else:
        print("Transcription failed.")
