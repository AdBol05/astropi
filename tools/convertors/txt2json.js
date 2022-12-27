let fs = require('fs');

let args = process.argv.slice(2);
if(args[0] === undefined) {console.log('\x1b[31m%s\x1b[0m',"ERROR: invalid input, please enter arguments in folowing format:\n<input file path> <output file path (optional)>"); process.exit(9);}
let data = fs.readFileSync(args[0], "utf-8");

