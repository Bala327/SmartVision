import struct, math, sys
sr=22050; freq=440; dur=3
s=[int(32767*math.sin(2*math.pi*freq*i/sr)) for i in range(sr*dur)]
stereo=[]
[stereo.extend([x,x]) for x in s]
sys.stdout.buffer.write(struct.pack(f'{len(stereo)}h',*stereo))
