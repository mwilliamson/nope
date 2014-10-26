var http = require("http");
var querystring = require("querystring");
var fs = require("fs");
var vm = require("vm");
var path = require("path");

var streamBuffers = require("stream-buffers");


var server = http.createServer(function(request, response) {
    if (request.method === "POST") {
        var bodyChunks = [];
        request.on("data", function(data) {
            bodyChunks.push(data);
        });
        request.on("end", function() {
            try {
                var body = bodyChunks.join("");
                var args = querystring.parse(body);
                var result = runProgram(args.cwd, args.main);
                response.writeHead(200, {
                   "Content-Type": "application/json" 
                });
                response.end(JSON.stringify(result));
            } catch (error) {
                response.writeHead(500, {
                   "Content-Type": "application/json" 
                });
                response.end(JSON.stringifiy({
                    error: error.toString()
                }));
            }
        });
    } else {
        response.writeHead(200, {"Content-Type": "plain/text"});
        response.end("OK");
    }
});

server.listen(process.argv[2]);


function runProgram(cwd, main) {
    var fullPath = path.join(cwd || "", main || "");
    var stdout = new streamBuffers.WritableStreamBuffer();
    var stderr = new streamBuffers.WritableStreamBuffer();

    var actualStdoutWrite = process.stdout.write;
    var actualStderrWrite = process.stderr.write;
    process.stdout.write = stdout.write.bind(stdout);
    process.stderr.write = stderr.write.bind(stderr);
    
    var returnCode;
    try {
        // `require` is cached, but we should always be getting unique paths anyway
        require(fullPath);
        returnCode = 0;
    } catch (error) {
        returnCode = 1;
        process.stderr.write(error.stack);
    }
    process.stdout = actualStdoutWrite;
    process.stderr = actualStderrWrite;
    return {
        returnCode: returnCode,
        stdout: stdout.getContentsAsString() || "",
        stderr: stderr.getContentsAsString() || ""
    };
}
