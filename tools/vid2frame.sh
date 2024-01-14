mkdir -p output_frames
for file in *.mp4;
	do ffmpeg -i "$file" -r 30 -q:v 2 "output_frames/${file%.*}_frame_%04d.jpg";
	done
