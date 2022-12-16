const fs = require('fs');
const jpeg = require('jpeg-js');
//const { NetCDFReader } = require("netcdfjs");

let args = process.argv.slice(2);

let data = fs.readFileSync(args[0], "utf-8");

console.log("====================================================\n" + "redaing file: " + args[0] + "\n" + "====================================================\n");

let dataArr = data.split(";");

if (!fs.existsSync("./NCtemp")) {fs.mkdirSync("./NCtemp");}

let dat = dataArr[321].split("=")[1];
fs.writeFileSync("./NCtemp/321.txt", dat);

let samples = dat.split(",\n  ");
console.log(samples[samples.length - 1]);

for (i in samples) {
    samples[i] = samples[i].replaceAll(" ", "");
    console.log("\n========================================================\n\n" + samples[i]);
    let count = (samples[i].match(/,/g) || []).length;
    console.log("->" + count);
}

//fs.writeFileSync("./NCtemp/321arr.txt", JSON.stringify(samples));

const width = 720;
const height = 500;

const pixels = samples[0];

const jpegData = jpeg.encode({ width, height, data: pixels });
fs.writeFileSync("./NCtemp/test.jpg", jpegData.data);