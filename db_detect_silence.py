import wave
import numpy as np
import matplotlib.pyplot as plt



if __name__ == "__main__":
        
    filepath = r""


    file = wave.open(filepath)

    fps = file.getframerate()
    nframes = file.getnframes()
    nchannels = file.getnchannels()
    duration = nframes/fps

    print("Audio file: ", filename)
    print("# of Channels: ", nchannels)
    print("Framerate (FPS): ", fps)
    print("# of Frames: ", nframes)
    print("Duration: ", duration)

    magic_n = 10
    num_chunks = int(duration*magic_n)
    chunk_size = int(fps/magic_n)
    total_fit = (num_chunks * chunk_size)

    data = file.readframes(-1)
    audio_sig = np.frombuffer(data, np.int16)
    audio_sig = audio_sig[::nchannels]

    volume = np.where(audio_sig >= 0, audio_sig/audio_sig.max(), audio_sig/audio_sig.min())

    db_data = 20 * np.log10(volume)
    db_thresh = db_data.clip(-30, 0)

    chunks = db_data[:total_fit].reshape((num_chunks, chunk_size))

    chunks_mask = np.where(chunks > -30, True, False)
    chunks_mean = np.mean(chunks_mask, axis=1)
    mask = np.where(chunks_mean > 0.3, True, False)

    for i in range(magic_n*2):
        mask += np.roll(mask, 1)
        mask += np.roll(mask, -1)

    mask = np.pad(mask, (1,1), 'constant')
    
    back_porch = np.logical_and(np.logical_xor(np.roll(mask, 1), mask), mask)
    front_porch = np.logical_and(np.logical_xor(np.roll(mask, -1), mask), mask)

    start_list = np.where(back_porch)[-1]/magic_n
    stop_list = np.where(front_porch)[-1]/magic_n

    list_len = len(start_list)

    timeline = np.linspace(0, duration, num=len(volume))


    plt.figure(1)
    plt.title(filename)

    plt.subplot(411)
    plt.plot(timeline, volume)

    plt.subplot(412)
    plt.plot(timeline, db_data)
    plt.plot(timeline, db_thresh)

    plt.subplot(413)
    plt.plot(chunks_mean)

    plt.subplot(414)
    plt.plot(mask)
    plt.plot(front_porch,color="purple")
    plt.plot(back_porch,color="red")

    plt.show()
