#!/usr/bin/env python
##Audio segmenting tools
import os
from os import path
import sys
import pyAudioAnalysis
from pyAudioAnalysis import audioBasicIO as aIO
from pyAudioAnalysis import audioSegmentation as aS
from pydub import AudioSegment
from pydub.utils import make_chunks
import librosa
import wave
import numpy as np
import numpy
import sklearn.cluster
import time
import scipy
from pyAudioAnalysis import audioFeatureExtraction as aF
from pyAudioAnalysis import audioTrainTest as aT
from pyAudioAnalysis import audioBasicIO
import matplotlib.pyplot as plt
from scipy.spatial import distance
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import sklearn.discriminant_analysis
import csv
import os.path
import sklearn
import sklearn.cluster
import hmmlearn.hmm
import cPickle
import glob

#audio_file = sys.argv[1]
audio_file='/Users/PSYC-dap3463/Desktop/Ellen/Ellen.wav'

###Configurations###
data_dir='/Users/PSYC-dap3463/Desktop/Ellen'
pAA_dir='/Users/PSYC-dap3463/Applications/pyAudioAnalysis'
AudioSegment.converter = "/usr/local/bin/ffmpeg"
####################

##Remove Periods of silence
[Fs, x] = aIO.readAudioFile(audio_file)
segments = aS.silenceRemoval(x, Fs, 0.050, 0.050, smoothWindow = 1.0, Weight = 0.3, plot = False)

def slice(infile, outfilename, start_ms, end_ms):
    width = infile.getsampwidth()
    rate = infile.getframerate()
    fpms = rate / 1000 # frames per ms
    length = (end_ms - start_ms) * fpms
    start_index = start_ms * fpms

    out = wave.open(outfilename, "w")
    out.setparams((infile.getnchannels(), width, rate, length, infile.getcomptype(), infile.getcompname()))

    infile.rewind()
    anchor = infile.tell()
    infile.setpos(anchor + start_index)
    out.writeframes(infile.readframes(length))

infile = wave.open(audio_file, mode=None)
j=0
k=0
for i in segments:
    print i
    outfile = audio_file.replace(' ', '')[:-4] + '_SR_' + str(j) + '.wav'
    start=segments[k][0]
    end=segments[k][1]
    slice(infile, outfile, int(start)*1000, int(end)*1000)
    j = j + 1
    k = k + 1

sound_path = data_dir + '/' + os.listdir(data_dir)[2]
combined_sounds = AudioSegment.from_wav(sound_path)
for FILE in os.listdir(data_dir)[2:]:
    sound_path = data_dir + '/' + FILE
    sound = AudioSegment.from_wav(sound_path)
    combined_sounds = combined_sounds + sound

audfile_cleaned = audio_file.replace(' ', '')[:-4] + '_SR_merged' + '.wav'
combined_sounds.export(audfile_cleaned, format="wav")

outfile = audio_file.replace(' ', '')[:-4] + '_SR_merged_clipped.wav'
start=1000*int(5)
duration = AudioSegment.from_wav(audfile_cleaned).duration_seconds
end= 1000*int(duration - 5)
slice(infile, outfile, start, end)

##Remove random noise bursts (high amplitude sounds)
def match_target_amplitude(sound, target_dBFS):
    change_in_dBFS = target_dBFS - sound.dBFS
    return sound.apply_gain(change_in_dBFS)

def sound_slice_normalize(sound, sample_rate, target_dBFS):
    def max_min_volume(min, max):
        for chunk in make_chunks(sound, sample_rate):
            if chunk.dBFS < min:
                yield match_target_amplitude(chunk, min)
            elif chunk.dBFS > max:
                yield match_target_amplitude(chunk, max)
            else:
                yield chunk

    return reduce(lambda x, y: x + y, max_min_volume(target_dBFS[0], target_dBFS[1]))

sound = AudioSegment.from_wav(outfile)
normalized_db = min_normalized_db, max_normalized_db = [-40.0, -35.0]
sample_rate = 10000
normalized_sound = sound_slice_normalize(sound, sample_rate, normalized_db)
audfile_cleaned_norm = audio_file.replace(' ', '')[:-4] + '_cleaned_norm' + '.wav'
normalized_sound.export(audfile_cleaned_norm, format="wav")

##Apply low bandpass filter to remove non-human sounds
# Created input file with:
sound_prefilt = AudioSegment.from_wav(audfile_cleaned_norm)
sound_postlpfilt = AudioSegment.low_pass_filter(sound, 2000)
sound_postfilt = AudioSegment.high_pass_filter(sound_postlpfilt, 200)
outfile_filt = audio_file.replace(' ', '')[:-4] + '_SR_norm_filtered.wav'
sound_postfilt.export(outfile_filt, format="wav")

##Increase overall volume by 6 dB
orig = AudioSegment.from_wav(outfile_filt)
louder = orig + 6

##save louder
outfile_final = audio_file.replace(' ', '')[:-4] + '_final.wav'
louder.export(outfile_final, format='wav')

##Convert audio .wav file to .flac
audfile_wav = AudioSegment.from_wav(outfile_final)
audfile_flac_name = audio_file.replace(' ', '')[:-4] + '.flac'
audfile_flac = audfile_wav.export(audfile_flac_name, format = "flac")

##Speech-to-text
import json
from watson_developer_cloud import SpeechToTextV1

IBM_USERNAME = "369721a7-d096-4268-8ec6-b8dd2bce3074"
IBM_PASSWORD = "KCNZVRSLviMq"

stt = SpeechToTextV1(username=IBM_USERNAME, password=IBM_PASSWORD)
audio_file = open(AUDIO_FILE, "rb")

with open('transcript_result.json', 'w') as fp:
    result = stt.recognize(audio_file, content_type="audio/x-flac", continuous=True, timestamps=True)
    json.dump(result, fp, indent=2)
