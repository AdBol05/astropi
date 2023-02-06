const ffmpeg = require('fluent-ffmpeg');
const fs = require('fs');

let args = process.argv.slice(2);
if (!fs.existsSync(args[0]) || args[0] === undefined) { console.log('\x1b[31m%s\x1b[0m', "ERROR: Input file path does not exist."); process.exit(9); }

let files = fs.readdirSync(args[0], (err, files_) => {
    if (err) {
        console.error(err);
        return;
    }

    const out = files_.filter(file => file.endsWith('.h264'));
    return out;
});

console.log(files);

/*ffmpeg()
    .input(args[0])
    .inputFPS(30)
    .outputOptions("-c copy")
    .output(args[0].replace(".h264", ".mp4"))
    .run();*/