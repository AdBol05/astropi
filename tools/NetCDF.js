const fs = require('fs');

let args = process.argv.slice(2);

let data = fs.readFileSync(args[0], "utf-8");

console.log(data);