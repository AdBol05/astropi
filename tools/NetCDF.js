const fs = require('fs');
const { NetCDFReader } = require("netcdfjs");

let args = process.argv.slice(2);

let data = fs.readFileSync(args[0], "utf-8");
let reader = new NetCDFReader(Buffer.from(data));

console.log(reader);