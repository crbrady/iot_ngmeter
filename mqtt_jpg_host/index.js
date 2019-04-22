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
        topicImg[topics[RAW_IMG]] = message;
        image = message;
    }
});


http.createServer(function(req, res){
    let request = url.parse(req.url, true);
    let action = request.pathname;
    console.log("http:" + action);
    // if (action === '/debug') {
    //
    //     res.writeHead(200, {'Content-Type': 'image/jpg' });
    //     res.end(image, 'binary');
    // }

    if (action === topics[DEBUG_IMG]) {
        res.writeHead(200, {'Content-Type': 'image/jpg' });
        res.end(topicImg[topics[DEBUG_IMG]], 'binary');
    }

    if (action === topics[RAW_IMG]) {
        res.writeHead(200, {'Content-Type': 'image/jpg' });
        res.end(topicImg[topics[RAW_IMG]], 'binary');
    }
}).listen(9013, '127.0.0.1');
