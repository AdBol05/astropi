const ffmpeg = require('fluent-ffmpeg');
const fs = require('fs');

let args = process.argv.slice(2);
if (!fs.existsSync(args[0]) || args[0] === undefined) { console.log('\x1b[31m%s\x1b[0m', "ERROR: Input file path does not exist."); process.exit(9); }

let files = fs.readdirSync(args[0]);
files = files.filter(file => file.endsWith('.h264'));

for (i in files){
    let path = "";
    if (args[0].endsWith('/')) {path = args[0] + files[i];}
    else {path = args[0] + "/" + files[i];}
}

/*ffmpeg()
    .input(args[0])
    .inputFPS(30)
    .outputOptions("-c copy")
    .output(args[0].replace(".h264", ".mp4"))
    .run();*/