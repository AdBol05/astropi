const fs = require('fs');
//const { NetCDFReader } = require("netcdfjs");

let args = process.argv.slice(2);

let data = fs.readFileSync(args[0], "utf-8");

console.log("====================================================\n" + "redaing file: " + args[0] + "\n" + "====================================================\n");

/*let reader = new NetCDFReader(Buffer.from(data));
console.log(reader.getDataVariable("raster_image"));*/
let dataArr = data.split(";");

//console.log(dataArr[321]);
//console.log(dataArr.length);

if (!fs.existsSync("./NCtemp")){
    fs.mkdirSync("./NCtemp");
}

let dat = dataArr[321].split("=")[1];
fs.writeFileSync("./NCtemp/321.txt", dat);

let samples = dat.split(",\n  ");
console.log(samples[samples.length - 1]);