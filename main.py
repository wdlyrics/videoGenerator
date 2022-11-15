# from pydantic import env_settings
import requests
import json 
import gtts
import random
import os
from tqdm.auto import tqdm
from moviepy.editor import *
import os
import glob
# from dotenv import load_dotenv
from moviepy.video.io.VideoFileClip import VideoFileClip
from mutagen.mp3 import MP3
import argparse

# load_dotenv() #load .env

# PEXELS_API_KEY = os.getenv('PEXELS_API_KEY') #add your api key in .ENV
# AMOUNT_OF_VIDEOS_TO_MAKE = None
# TTS_ENABLED = False

# download background video from pexels - https://www.pexels.com/api/documentation/#videos-search__parameters
def downloadVideo(id) -> str:
    """Downloads video from Pexels with the according video ID """
    url = "https://www.pexels.com/video/" + str(id) + "/download.mp4"
    # Streaming, so we can iterate over the response.
    response = requests.get(url, stream=True)
    total_size_in_bytes= int(response.headers.get('content-length', 0))
    block_size = 1024 #1 Kibibyte
    progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)
    save_as = "tempFiles/vid.mp4" # the name you want to save file as
    with open(save_as, 'wb') as file:
        for data in response.iter_content(block_size):
            progress_bar.update(len(data))
            file.write(data)
    progress_bar.close()
    if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
        print("ERROR, something went wrong")
    return save_as

        

def scrapeVideos(pexelsApiKey: str):
    """Scrapes video's from PEXELS about nature in portrait mode with API key"""
    print("scrapeVideos()")
    parameters = {
        'query' : 'nature',
        'orientation' : 'portrait',
        #'page' : '1',
    }
    try:
        pexels_auth_header = {
            'Authorization' : pexelsApiKey
        }
        print("Trying to request Pexels page with your api key")
        resp = requests.get("https://api.pexels.com/videos/search", headers=pexels_auth_header, params=parameters)
        statusCode = resp.status_code
        if statusCode != 200:
            if statusCode == 429:
                print(f"""You sent too many requests(you have exceeded your rate limit)!\n 
                The Pexels API is rate-limited to 200 requests per hour and 20,000 requests per month (https://www.pexels.com/api/documentation/#introduction).\n
                Returned status code: {statusCode}""")
            else:
                print(f"Error requesting Pexels, is your api key correct? Returned status code: {statusCode}")
            print("Exiting...!")
            exit()
    except:
        print("Error in request.get....!??")
    data = json.loads(resp.text)
    results = data['total_results']
    if results == 0:
        print("No video results for your query: ", parameters['query'],"\nExiting..." )
        exit()
    return data

def usedQuoteToDifferentFile():
    """Removes the used quote from the .txt and places the quote in usedQuotes.txt"""
    quote = None
    with open('quotes/motivational.txt', 'r+') as file:
        lines = file.readlines()
        quote = lines[0]
        file.seek(0)
        file.truncate()
        file.writelines(lines[1:])
    
    with open('quotes/usedQuotes.txt', 'a') as file:
        file.write(quote)


def getQuote():
    """Get 1 quote from the text file"""
    with open('quotes/motivational.txt', 'r+') as file:
        lines = file.readlines()
        x = lines[0].replace("\n","").replace("-", "\n -")
        print ("Quote: ", x)
        return x

# def makeMp3(data):
#     """Make mp3 from the quote text, so we know the duration it takes to read"""
#     save_as = "tempFiles/speech.mp3"
#     tts = gtts.gTTS(data, lang='en', tld='ca')
#     tts.save(save_as)
#     return save_as

def videoIntro(introText, videoNumber) -> CompositeVideoClip:
    intro_text_clip = TextClip(
        txt=introText[videoNumber],
        fontsize=70,
        size=(800, 0),
        font="Roboto-Regular",
        color="white",
        method="caption",
        ).set_position('center')
    
    intro_width, intro_height = intro_text_clip.size
    intro_color_clip = ColorClip(
        size=(intro_width+100, intro_height+50),
        color=(0,0,0)
        ).set_opacity(.6)
    intro_clip = VideoFileClip("intro_clip/2_hands_up.mp4").resize((1080,1920))
    intro_clip_duration = 6
    text_with_bg= CompositeVideoClip([intro_color_clip, intro_text_clip]).set_position(lambda t: ('center', 200+t)).set_duration(intro_clip_duration)
    intro_final = CompositeVideoClip([intro_clip, text_with_bg]).set_duration(intro_clip_duration)
    return intro_final

def createVideo(quoteText: str, bgMusic: str, bgVideo: str, videoNumber: int, ttsAudio: bool):
    """Creates the entire video with everything together - this should be split up in different methods"""
    introText = ['A quote about never giving up on your dreams','A quote about being yourself','A quote about believing in yourself','A quote about making your dreams come true','A quote about happiness','A quote to remind you to stay positive','A quote about never giving up', 'A quote about being grateful', 'A quote about taking risks', 'A quote about living your best life']
    print(f"Introtext we will use: {introText[videoNumber]}")
    intro_final = videoIntro(introText, videoNumber)

    quoteArray = []
    quoteArray.append(quoteText)
    totalTTSTime = 0
    completedVideoParts = []

    print(f"Going to create a total of {len(quoteArray)} 'main' clips")
    for idx, sentence in enumerate(quoteArray):
        #create the audio
        save_as = f"tempFiles/temp_audio_{str(idx)}.mp3"
        tts = gtts.gTTS(sentence, lang='en', tld='ca')
        #save audio
        tts.save(save_as)
        audio = MP3(save_as)
        time = audio.info.length
        totalTTSTime += time
        print(f"Mp3 {str(idx)} has audio length: {time} ")

        #createTheClip with the according text
        text_clip = TextClip(
            txt=sentence,
            fontsize=70,
            size=(800, 0),
            font="Roboto-Regular",
            color="white",
            method="caption",
            ).set_position('center')
        #make background for the text
        tc_width, tc_height = text_clip.size
        color_clip = ColorClip(
            size=(tc_width+100, tc_height+50),
            color=(0,0,0)
            ).set_opacity(.6)

        text_together = CompositeVideoClip([color_clip, text_clip]).set_duration(time).set_position('center')
        audio_clip = AudioFileClip(save_as)
        new_audioclip = CompositeAudioClip([audio_clip])
        text_together.audio = new_audioclip
        completedVideoParts.append(text_together)

    combined_quote_text_with_audio = concatenate_videoclips(completedVideoParts).set_position('center') 
    combined_quote_text_with_audio.set_position('center')

    #calculate total time
    total_video_time = intro_final.duration + totalTTSTime
    background_clip = VideoFileClip(bgVideo).resize((1080,1920))
    final_export_video = CompositeVideoClip([background_clip, combined_quote_text_with_audio]).subclip(0, totalTTSTime)

    #Set audio
    backgroundMusic = AudioFileClip(bgMusic)
    totalAudio = audioClip(ttsAudio, backgroundMusic, final_export_video, total_video_time, intro_final.duration)

    final = concatenate_videoclips([intro_final, final_export_video])
    final.audio = totalAudio
    final.write_videofile("VID_" + str(videoNumber) + ".mp4", threads=12)

def audioClip(ttsAudio: bool, backgroundMusic, final_export_video, total_video_time, introDuration: int) -> CompositeAudioClip:
    """Makes the audioclip for the entire video, ttsAudio is the boolean that the user sets (yes/no TTS in the quotetext)"""
    new_audioclip = None
    if ttsAudio:
        new_audioclip = CompositeAudioClip([
            backgroundMusic, 
            final_export_video.audio.set_start(introDuration) #uncomment to get TTS audio -> goes to else
            ]).subclip(0,total_video_time)
    else:
        new_audioclip = CompositeAudioClip([
        backgroundMusic, 
        ]).subclip(0,total_video_time)
    return new_audioclip



def randomBgMusic():
    """Get a random 'sad' song from the sad_music folder"""
    dir = "sad_music"
    x = random.choice(os.listdir(dir)) 
    print("Random music chosen: ", x)
    return dir + "/" + x


def deleteTempFiles():
    """Deletes the downloaded/generated vid.mp4 and speech.mp3"""
    print("Deleting temporary downloaded files / generated mp3 file")
    files = glob.glob('tempFiles/*')
    for x in files:
        os.remove(x)

def cleanUpAfterVideoFinished():
    usedQuoteToDifferentFile()
    # deleteTempFiles()

def getBackgroundVideo(pexelsApiKey) -> str:
    scrapedVideosJson = scrapeVideos(pexelsApiKey)
    videoArray = scrapedVideosJson['videos']
    randomVideoToScrape = random.randint(0, len(videoArray)-1)
    videoId = videoArray[randomVideoToScrape]['id']
    print("Going to scrape video with id: ", videoId)
    bgVideo = downloadVideo(videoId)
    return bgVideo

def mainVideoLoop(parsedArgs):
    """Make X amount of videos."""
    for i in range(parsedArgs.amount_of_videos): #amount of videos to generate
        bgVideo = getBackgroundVideo(parsedArgs.pexels_api_key)
        quoteText = getQuote()
        # mp3 = makeMp3(quoteText) # make mp3 and save as: speech.mp3
        bgMusic = randomBgMusic()
        ttsAudio = True
        createVideo(quoteText, bgMusic, bgVideo, i, ttsAudio)
        cleanUpAfterVideoFinished()
        print("finished! video: ", i)

def parseCLIargs():
    my_parser = argparse.ArgumentParser(description="""
    Help section of video generator
    """)

    #required args
    required = my_parser.add_argument_group('Required arguments')
    required.add_argument('-a', '--amount-of-videos',
                        help='The amount of videos to generate. Example: 5',
                        type=int,
                        required=True,
                        metavar='')

    required.add_argument('-p', '--pexels-api-key',
                        help='Your pexels API key, for downloading background videos',
                        type=str,
                        required=True,
                        metavar='')

    #optional args
    optional = my_parser.add_argument_group('Optional arguments')

    optional.add_argument('-tts', '--tts-enabled',
                            help='Enables TTS audio for the quote, default is OFF',
                            action='store_true',
                        )


    # Execute parse_args()
    parsedArgs = my_parser.parse_args()
    return parsedArgs

    print('ALL ARGUMENTS PROVIDED CORRECTLY')

if __name__ == "__main__":
    parsedArgs = parseCLIargs()
    mainVideoLoop(parsedArgs)
    


