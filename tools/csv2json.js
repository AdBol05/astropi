let fs = require('fs');

let args = process.argv.slice(2);
if (args[0] === undefined) { console.log('\x1b[31m%s\x1b[0m', "ERROR: invalid input, please enter arguments in folowing format:\n<input file path> <output file path>\nOutput file path is optional. Output file will be written to the same path as input if not defined otherwise."); process.exit(9); }
let input = fs.readFileSync(args[0], "utf-8");

input = input.split("\n");

let head = input[0];
input.shift();

/*console.log(head);
console.log(data[0]);
console.log(data[1]);*/

const keys = head.split(",");

let data = [];

for (i in input) {
    data.push(input[i].split(","));
    //console.log(sample);
}
console.log(data);

//* arrays in object are made from array of arrays

let output = Object.fromEntries(keys.map(key => [key, "data placeholder"]));
console.log(output);