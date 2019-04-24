const http = require('http');
const url = require('url');

const mqtt = require('mqtt');

const PropertiesReader = require('properties-reader');
const properties = PropertiesReader('properties.prop');
const client  = mqtt.connect('mqtt://' + properties.get('brokerip'));

let image;
let thumbnails = {};

let topics = [];
topics.push('ngmeter/status');
topics.push('ngmeter/cubic_feet');
topics.push('ngmeter/debug_img');
topics.push('ngmeter/raw_img');

let DEBUG_IMG = 2;
let RAW_IMG = 3;

console.log('Starting server...');

topicImg = {};


client.on('connect', function () {
    console.log("mqtt connected");
    client.subscribe(topics[0]);
    client.subscribe(topics[1]);
    client.subscribe(topics[2],{qos:2});
    client.subscribe(topics[3],{qos:2});
});

client.on('message', function (topic, message) {

    if(topic === topics[0]){
        console.log("ngmeter/status: " + message.toString());
    }

    if(topic === topics[1]){
        console.log("ngmeter/cubic_feet: " + message.toString());
    }

    if(topic === topics[DEBUG_IMG]){
        topicImg[topics[DEBUG_IMG]] = message;
        image = message;
    }

    if(topic === topics[RAW_IMG]){
        console.log(message.length);
        topicImg[topics[RAW_IMG]] = message;
        image = message;
    }
});

let html = "<html>\n" +
    "<script>\n" +
    "window.onload = function() {\n" +
    "    var image = document.getElementById(\"img\");\n" +
    "\n" +
    "    function updateImage() {\n" +
    "        image.src = image.src.split(\"?\")[0] + \"?\" + new Date().getTime();\n" +
    "    }\n" +
    "\n" +
    "    setInterval(updateImage, 5000);\n" +
    "}\n" +
    "</script>\n" +
    "\n" +
    //"<body onload=\"updateImage();\">\n" +
    "<img id=\"img\" src=\"http://192.168.0.2:9013/ngmeter/debug_img\" style=\"position:absolute;top:0;left:0\"/>\n" +
    "</body>\n" +
    "</html>";



http.createServer(function(req, res){
    let request = url.parse(req.url, true);
    let action = request.pathname;
    console.log("http:" + action);

    if (action === "/html/"+topics[DEBUG_IMG]) {
        res.writeHead(200, {'Content-Type': 'text/html' });
        res.end(html);
    }

    if (action === "/"+topics[DEBUG_IMG]) {
        res.writeHead(200, {'Content-Type': 'image/jpg' });
        res.end(topicImg[topics[DEBUG_IMG]], 'binary');
    }

    if (action === "/"+topics[RAW_IMG]) {
        console.log("RAW_IMG " + topicImg[topics[RAW_IMG]].length);
        res.writeHead(200, {'Content-Type': 'image/jpg' });
        res.end(topicImg[topics[RAW_IMG]], 'binary');
    }
}).listen(9013, "0.0.0.0");
