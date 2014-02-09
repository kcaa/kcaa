var http = require('http');

http.createServer(function (req, res) {
  var headers = {
    'Content-Type': 'text/plain'};
  res.writeHead(200, headers);
  res.end('Hello World\n');
}).listen(1337, '127.0.0.1');

console.log('Server running at http://127.0.0.1:1337/');
