from moviepy.editor import *
import numpy as np
import wave
import os

# TODO: Add exceptions and error detection and output to user
# TODO: Add pitch control for the speed up factor of active parts so it doesnt sound weird with 1.5 factor
# TODO: Instead of saving a wav file, pass the soundarray variable 


def find_filename(filepath):
    # Decided to find the path filename and extension using regex library
    # so I could learn how to user regex
    import os
    import re

    if os.path.isfile(filepath):
        
        full_filename_pattern = re.compile(r'\b[\w\-\s]+\.\w+$') # Find filename with extension
        only_path_pattern = re.compile(r'^.+[\\]')
        only_filename_pattern = re.compile(r'\b[\w\-\s]+(?=\.\w+$)') # Find filename with no extension
        only_extension_pattern = re.compile(r'\b\w+$') # find filename extension
        
        file_path = re.findall(only_path_pattern, filepath)
        file_name = re.findall(only_filename_pattern, filepath)
        file_format = re.findall(only_extension_pattern, filepath)

        return file_path[0], file_name[0], file_format[0]
    else: 
        print("Sorry, there was an error")






def convert_to_wav(filepath):
    import os
    
    # Check if file exists
    if os.path.isfile(filepath):
        video = VideoFileClip((filepath))
        audio = video.audio

        path, name, format = find_filename(filepath)
        new_filename = path + name +"_audio.wav"
        if os.path.isfile(new_filename) == False:
            audio.write_audiofile(new_filename, fps = audio.reader.fps)
            video.close()
        return new_filename





def detect_silence(filename):
    with wave.open(filename) as file:
        # Defining variables
        fps = file.getframerate()
        nframes = file.getnframes()
        nchannels = file.getnchannels()
        duration = nframes/fps
        # # # # # # # # # # # # # # # #
        
        file_data = file.readframes(-1)

        audio_sig = np.frombuffer(file_data, np.int16)[::nchannels]
        volume = np.where(audio_sig >= 0, audio_sig/audio_sig.max(), audio_sig/audio_sig.min())

        db_data = 20 * np.log10(volume)
        db_thresh = db_data.clip(-30, 0)

        # More variables
        magic_n = 10
        num_chunks = int(duration*magic_n)
        chunk_size = int(fps/magic_n)
        total_fit = (num_chunks * chunk_size)
        # # # # # # # # # # # # # # # #

        chunks = db_data[:total_fit].reshape((num_chunks, chunk_size))
        chunks_mask = np.where(chunks > -30, True, False)
        chunks_mean = np.mean(chunks_mask, axis=1)

        mask = np.where(chunks_mean > 0.3, True, False)

        for i in range(magic_n):
            mask += np.roll(mask, 1)
            mask += np.roll(mask, -1)

        mask = np.pad(mask, (1,1), 'constant')
        
        back_porch = np.logical_and(np.logical_xor(np.roll(mask, 1), mask), mask)
        front_porch = np.logical_and(np.logical_xor(np.roll(mask, -1), mask), mask)

        start_list = np.where(back_porch)[-1]/magic_n
        stop_list = np.where(front_porch)[-1]/magic_n
        
        return start_list, stop_list




    

def shorten_lecture(filepath):
    silent_factor = 5
    active_factor = 1.2

    print("\n\nConverting audio to a wav file")
    wav_file = convert_to_wav(filepath)

    print("\n\nDetecting silent parts")
    start_list, stop_list = detect_silence(wav_file)
    zipped_list = list(zip(start_list, stop_list))
    
    with VideoFileClip((filepath)) as full_video:
        clips = []
        a_clips = []
        
        clips_len = len(start_list) * 2 - 1# the length of start_list and stop_list is equal and therfore (list len) * 2
        print("\n\nSubclips to process: ", clips_len)
        for i in range(clips_len):
            list_index = int(i/2)
            if i % 2 > 0:
                clip = full_video.subclip(stop_list[list_index], start_list[list_index+1])
                clip_s = clip.fx(vfx.speedx, factor = silent_factor)    
            else:
                clip = full_video.subclip(start_list[list_index], stop_list[list_index])
                clip_s = clip.fx(vfx.speedx, factor = active_factor)
            
            clips.append(clip_s)
            a_clips.append(clip_s.audio)

        path, name, format = find_filename(filepath)
        edited_video_name = path + name + "_edited.mp4"
        edited_audio_name = path + name + "_edited_audio.mp3"

        print("\n\nConcatenating audio clips ..")
        if os.path.isfile(edited_audio_name) == False:
            final_audio = concatenate_audioclips(a_clips)
            final_audio.write_audiofile(edited_audio_name, ffmpeg_params=['-preset','veryfast'])

        print("\n\nConcatenating video clips ..")
        final_video = concatenate_videoclips(clips)

        print("\n\nMerging audio with video .. ")
        final_video.write_videofile(edited_video_name, codec='libx264', fps=30, audio=edited_audio_name, preset='faster', threads=2)
        
        print('\n\nFinished creating video file')
    return True







        

if __name__ == "__main__":
    import time
    while True:
        # # # # # # # # # # # # # # # # # # #
        # # # PATH OF VIDEO TO SHORTEN # # #
        filepath = input("File Path : ")
        # # # # # # # # # # # # # # # # # # # 
        # # # # # # # # # # # # # # # # # # #
        
        start = time.time()
        shorten_lecture(filepath)
        stop = time.time()
        print("\nTime took: ", stop-start)
