let fs = require('fs');

let args = process.argv.slice(2);
if (args[0] === undefined) { console.log('\x1b[31m%s\x1b[0m', "ERROR: invalid input, please enter arguments in folowing format:\n<input file path> <output file path>\nOutput file path is optional. Output file will be written to the same path as input if not defined otherwise."); process.exit(9); }

if (!fs.existsSync(args[0])) { console.log('\x1b[31m%s\x1b[0m', "ERROR: Input file path does not exist."); process.exit(9); }

console.log("reading file from " + args[0]);
let input = fs.readFileSync(args[0], "utf-8");

console.log("processing...");

input = input.split("\n");
let keys = input[0].split(",");
input.shift();
let data = [];

for (i in input[0].split(",")) { data.push([]); }
for (i in input) {
    for (j in data) {
        data[j].push(input[i].replace("\r","").split(",")[j]);
    }
}

let l = 0;
let output = Object.fromEntries(keys.map(key => [key.replace("\r", ""), data[l++]]));
//console.log(output);

if (args[1] !== undefined) { fs.writeFileSync(args[1], JSON.stringify(output)); }
else { fs.writeFileSync(args[0].replace(".csv", ".json"), JSON.stringify(output)); }

console.log(output);

console.log("written output to " + args[0].replace(".csv", ".json"));