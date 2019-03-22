
const http = require('http');
const url = require('url');


const mqtt = require('mqtt')
const fs = require('fs');

const PropertiesReader = require('properties-reader');
const properties = PropertiesReader('properties.prop');
const client  = mqtt.connect('mqtt://' + properties.get('brokerip'));

var image;
var thumbnails = {};

console.log('Starting server...');

try{
  image = fs.readFileSync('./blankThumb.jpg');
}
catch(err){
  console.log('err: blankThumb.jpg is missing');
}

client.on('connect', function () {
    console.log("mqtt connected");
    client.subscribe('ngmeter/status');
    client.subscribe('ngmeter/cubic_feet');
    client.subscribe('ngmeter/debug_img');
});


setInterval(getDebugImg, 5000);

function getDebugImg(){
    client.publish('ngmeter/debug_img/request', 'true');
}


client.on('message', function (topic, message) {

    if(topic == "ngmeter/status"){
        console.log("ngmeter/status: " + message.toString());
    }

    if(topic == "ngmeter/cubic_feet"){
        console.log("ngmeter/cubic_feet: " + message.toString());
    }

    if(topic == "ngmeter/debug_img"){
        image = message;
    }
});


var clientStatus = [];


var server = require('http').createServer();
var io = require('socket.io')(server);
io.on('connection', function(client){

    //io.emit('message', 'This is the time: ' +new Date());
    client.on('event', function(data){});
    client.on('disconnect', function(){});
    client.on('getStatus', function(msg){
        console.log('got get status');
    });
    client.on('sendstatus',function (msg) {
        console.log('status sent');
    })
    client.on( 'cameraSettings',function(msg){
        console.log(msg);
        camSettings = JSON.parse(msg);
    }
)

});
server.on('connection',function(){
    console.log('socket client connected');
})


server.listen(2000);

http.createServer(function(req, res){
    var request = url.parse(req.url, true);
    var action = request.pathname;
    console.log("http:"+action);
    if (action == '/debug') {

        res.writeHead(200, {'Content-Type': 'image/jpg' });
        res.end(image, 'binary');
    }


}).listen(8080, '127.0.0.1');
