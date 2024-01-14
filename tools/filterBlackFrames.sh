mkdir -p filtered_frames && for file in output_frames/*.jpg; do
    if ffmpeg -i "$file" -vf "blackframe=amount=0.01:threshold=0.01,select=eq(n\, -1)" -vsync vfr -q:v 2 -f null - 2>&1 | grep "black_start:"; then
        echo "Deleting $file (black frame)"
        rm "$file"
    else
	echo "Moving $file"
        mv "$file" filtered_frames/
    fi
done
