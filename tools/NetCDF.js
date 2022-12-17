const fs = require('fs');
const jpeg = require('jpeg-js');

let args = process.argv.slice(2);

if(args.length !== 5) {console.log('\x1b[31m%s\x1b[0m',"ERROR: invalid input, please enter arguments in folowing format:\n<input file path> <frame number> <image width in px> <image height in px> <output file path>"); process.exit(9);}

let data = fs.readFileSync(args[0], "utf-8");

console.log("========================================================");
console.log('\x1b[32m%s\x1b[0m',"redaing file: " + args[0]);
console.log("========================================================\n");

let dataArr = data.split(";");

if (!fs.existsSync("./NCtemp")) {fs.mkdirSync("./NCtemp");}

let dat = dataArr[321].split("=")[1];
fs.writeFileSync("./NCtemp/321.txt", dat);

let samples = dat.split(",\n  ");
console.log(samples[args[1]]);

const pixels = samples[args[1]];

const width = args[2];
const height = args[3];

const jpegData = jpeg.encode({ width, height, data: pixels });
fs.writeFileSync(args[4], jpegData.data);

console.log("========================================================")
console.log(jpegData);

console.log("========================================================")
console.log('\x1b[32m%s\x1b[0m',"file written to: " + args[4]);
console.log("========================================================");