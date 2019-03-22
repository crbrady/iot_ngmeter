import React from 'react';
import ReactDOM from 'react-dom';
import socketIOClient from 'socket.io-client';
import WebFont from 'webfontloader';
import Toggle from 'react-toggle';
import ReactInterval from 'react-interval';
import './index.css';

import Dropdown from 'react-dropdown'

const isoDropdown = [
    { value: 100, label: '100', className: 'isoClass' },
    { value: 200, label: '200', className: 'isoClass' },
    { value: 320, label: '320', className: 'isoClass' },
    { value: 400, label: '400', className: 'isoClass' },
    { value: 500, label: '500', className: 'isoClass' },
    { value: 640, label: '640', className: 'isoClass' },
    { value: 800, label: '800', className: 'isoClass' },
];

const shutterDropdown = [

    { value: '100', label: '1/1000',  className: 'shutterClass' },
    { value: '200', label: '1/500', className: 'shutterClass' },
    { value: '400', label: '1/250', className: 'shutterClass' },
    { value: '600', label: '1/160', className: 'shutterClass' },
    { value: '1000', label: '1/100', className: 'shutterClass' },
    { value: '1500', label: '1/64', className: 'shutterClass' },
    { value: '3100', label: '1/32', className: 'shutterClass' },
    { value: '6200', label: '1/16', className: 'shutterClass' },
    { value: '12500', label: '1/8', className: 'shutterClass' },
    { value: '25000', label: '1/4', className: 'shutterClass' },
    { value: '50000', label: '1/2', className: 'shutterClass' },
    { value: '100000', label: '1 sec', className: 'shutterClass' },
    { value: '200000', label: '2 sec', className: 'shutterClass' },
    { value: '400000', label: '4 sec', className: 'shutterClass' },
    { value: '600000', label: '6 sec', className: 'shutterClass' },
];

const wbDropdown = [
    { value: 'off', label: 'off', className: 'wbClass' },
    { value: 'auto', label: 'auto', className: 'wbClass' },
    { value: 'sun', label: 'sun', className: 'wbClass' },
    { value: 'cloud', label: 'cloud', className: 'wbClass' },
    { value: 'shade', label: 'shade', className: 'wbClass' },
    { value: 'tungsten', label: 'tungsten', className: 'wbClass' },
    { value: 'fluorescent', label: 'fluorescent', className: 'wbClass' },
    { value: 'incandescent', label: 'incandescent', className: 'wbClass' },
    { value: 'flash', label: 'flash', className: 'wbClass' },
    { value: 'horizon', label: 'horizon', className: 'wbClass' },
];




const socket = socketIOClient.connect("localhost:2000");
//socket.on('message', msg => console.log(msg));
socket.on('connect', function(socket){
    console.log('socket connected!');
    requestStats();
});


WebFont.load({
    google: {
        families: ['Archivo']
    }
});

var c1 = '#78839D';
var c2 = '#C1B7BA';
var c3 = 'white';//#ECD4C6
var c4 = 'white';//#FFE2BB
var c5 = '#FFC58B';

var blankImageBytes = '';

/*
#E6E2AF
#A7A37E
#EFECCA
#046380
#002F2F
 */



//msg(ws.rQshiftBytes());
//<img src={"data:image/jpg;base64," + Base64.encode(data)}></img>




function requestStats(){
    socket.emit('getStatus',"");
}

// window.requestStats = requestStats;


// socket.on('sendstatus', msg => {
//     status = JSON.parse(msg);
//     for(var i =0; i < status.length;i++){
//         status[i].tnPath = "http://localhost:8080/"+status[i].name+"/thumb/" + Math.random().toString().split('.')[1];
//     }
//     //RenderPage();
// });

// socket.on('newthumb',function(msg){
//     console.log(msg);
// });

class Cam extends React.Component{
    state = {
        status:[
            ]
    }

    makePathRandom = (name)=>{
        return "http://localhost:8080/"+name+"/thumb/" + Math.random().toString().split('.')[1];
    }

    content(){ return this.state.status.map((cam) =>
        <div style={camDivStyle} key={cam.name}>
            <div style={camTopDiv}>
                <div style={camNameDiv}>
                    <h4 style = {camHeading}>{cam.name}</h4>
                </div>
            </div>

            <div style={camMidDiv}>
                <img id={cam.name+'_tn'} src={cam.tnPath}></img>
            </div>

            <div style={camBottomDiv}>
                <div>
                    <div style={statsCol1}>
                        <span style={statsPStyle}>
                            Mem: {parseInt(cam.freeRam/1000000)}M / {parseInt(cam.totalRam/1000000)}M
                        </span>
                    </div>
                    <div style={statsCol2}>
                        <span style={statsPStyle}>
                            OS: {cam.platform}
                        </span>
                    </div>
                    <div style={statsCol3}>
                        <span style={statsPStyle}>
                            Uptime: {parseInt(cam.uptime/86400)}d {parseInt(cam.uptime/3600)%24}h {parseInt(cam.uptime/60)%60}m
                        </span>
                    </div>

                </div>
                <div>
                    <CamControl />
                </div>
            </div>
        </div>
    );}

    render(){

        socket.on('sendstatus', msg => {
            var status;
            status = JSON.parse(msg);
            for(var i =0; i < status.length;i++){
                status[i].tnPath =this.makePathRandom(status[i].name);
            }
            this.setState({status : status});
        });

        socket.on('newthumb', (msg) => {
            var tnImg = document.getElementById(msg+'_tn');
            if(tnImg){
                tnImg.setAttribute('src',this.makePathRandom(msg));
            }

        })


        return (
            <div>
                {this.content()}
            </div>
        );
    }

}

class CamControl extends React.Component {
    render(){
        return(
            <div>
                <div style={camControlCol1}>
                    <button style={fullPreviewButton}>Full Preview</button>
                </div>
                <div style={camControlCol2}>
                    <span style={toggleLabel}>Rapid Preview</span>

                    <Toggle
                        // defaultChecked={this.state.baconIsReady}
                        // onChange={this.handleBaconChange}
                    />

                </div>
                <div style={camControlCol3}>
                    <span style={toggleLabel}>Enable</span>
                    <Toggle
                        // defaultChecked={this.state.baconIsReady}
                        // onChange={this.handleBaconChange}
                    />
                </div>
            </div>
        );
    }
}

class App extends React.Component {

    constructor() {
        super();

        this.state = {
            endpoint: "localhost:2000",
            isoIndex: 0,
            shutterIndex: 7,
            wbIndex: 5
        }
    };

    // method for emitting a socket.io event
    // send = () => {
    //     const socket = socketIOClient(this.state.endpoint)
    // }

    getIsoSetting = () => {
        return isoDropdown[this.state.isoIndex].value;
    }

    getShutterSetting = () => {
        return shutterDropdown[this.state.shutterIndex].value;
    }

    getWbSetting = () => {
        return wbDropdown[this.state.wbIndex].value;
    }

    sendCamSettings = (value) =>{
        console.log(value);
        socket.emit('cameraSettings',JSON.stringify(value));
    };

    newIsoValue = (msg) =>{
        for(var i = 0; i < isoDropdown.length;i++){
            if(isoDropdown[i].value == msg.value){
                this.setState({isoIndex:i})

                var camObj = {};
                camObj.iso = msg.value;
                camObj.shutter = this.getShutterSetting();
                camObj.wb = this.getWbSetting();

                this.sendCamSettings(camObj);
            }
        }
    };

    newShutterValue = (msg) =>{
        for(var i = 0; i < shutterDropdown.length;i++){
            if(shutterDropdown[i].value == msg.value){
                this.setState({shutterIndex:i})

                var camObj = {};
                camObj.iso = this.getIsoSetting();
                camObj.shutter = msg.value;
                camObj.wb = this.getWbSetting();

                this.sendCamSettings(camObj);
            }
        }
    };

    newWbValue = (msg) =>{
        for(var i = 0; i < wbDropdown.length;i++){
            if(wbDropdown[i].value == msg.value){
                this.setState({wbIndex:i})

                var camObj = {};
                camObj.iso = this.getIsoSetting();
                camObj.shutter = this.getShutterSetting();
                camObj.wb = msg.value;

                this.sendCamSettings(camObj);
            }
        }
    };

    render() {
        document.body.style.backgroundColor = c2;
        document.body.style.margin = 0;


        return (
            <div>
                <div style={topBarStyle} >
                    <h2 style={mainTitleStyle}>RasScan</h2>
                    <button style={refreshButtonStyle}> Refresh </button>
                    <div class="isoDropdown">
                        <span class="camSettingsHeading">ISO</span>
                        <Dropdown options={isoDropdown} onChange={this.newIsoValue} value={isoDropdown[this.state.isoIndex]} placeholder="Select an option" />
                    </div>
                    <div class="shutterDropdown">
                        <span class="camSettingsHeading">Shutter</span>
                        <Dropdown options={shutterDropdown} onChange={this.newShutterValue} value={shutterDropdown[this.state.shutterIndex]} placeholder="Select an option" />
                    </div>
                    <div class="wbDropdown">
                        <span class="camSettingsHeading">White Balance</span>
                        <Dropdown options={wbDropdown} onChange={this.newWbValue} value={wbDropdown[this.state.wbIndex]} placeholder="Select an option" />
                    </div>
                </div>
                <div style={horizontalSpacerStyle}>
                </div>
                <div>
                    <Cam />
                </div>
            </div>
        );
    }
}

export default App






const topBarStyle = {
    margin: '0px',
    border: '0px',
    background: c1,
    width: '100%',
    height: '50px'
}


const horizontalSpacerStyle = {
    margin: '0px',
    border: '0px',
    width: '100%',
    height: '6px'
}

const camDivStyle = {
    margin: '5px ',
    width: '320px',
    height: '320px',
    border: '5px solid '+c3,
    float: 'left',
    borderRadius: '5px'
};

const camTopDiv = {
    margin: '0px ',
    width: '100%',
    height: '25px',
    background: c3
};

const camHeading = {
    fontFamily: 'Archivo',
    margin:'auto',
    lineHeight:'25px',
    verticalAlign:'middle'
}

const camMidDiv = {
    width: '100%',
    height: '250px',
    background: c4
};

const camBottomDiv = {
    width: '100%',
    height: '45px',
    background: c3
};

const camNameDiv = {
    top:'50%',
    textAlign:'left'
}

const mainTitleStyle = {
    float: 'left',
    color:'white',
    paddingLeft:'14px',
    paddingRight:'14px',
    fontFamily: 'Archivo',
    margin:'auto',
    lineHeight:'54px',
    verticalAlign:'middle',
    display: 'inline'
}

const refreshButtonStyle = {
    marginTop:'5px',
    fontSize:'15px',
    width:'100px',
    borderWidth:'0px',
    fontFamily: 'Archivo',
    lineHeight:'35px',
    verticalAlign:'middle',
    borderRadius: '20px',
    backgroundColor:c4,
    float:'left'
}

const statsPStyle = {
    fontFamily: 'Archivo',
    margin:'auto',
    lineHeight:'25px',
    verticalAlign:'middle',
    fontSize:'12px',
    display: 'inline'
}

const toggleLabel = {
    fontFamily: 'Archivo',
    marginRight:'5px',
    marginLeft:'5px',
    lineHeight:'22px',
    verticalAlign:'top',
    fontSize:'12px'
}

const columnStyleThird ={
    float: 'left',
    width: '33%',
    textAlign:'center'
}

const statsCol1 ={
    float: 'left',
    width: '35%',
    textAlign:'left'
}

const statsCol2 ={
    float: 'left',
    width: '20%',
    textAlign:'center'
}

const statsCol3 ={
    float: 'left',
    width: '45%',
    textAlign:'right'
}


const camControlCol1 ={
    float: 'left',
    width: '25%',
    textAlign:'left',
    lineHeight:'20px'
}

const camControlCol2 ={
    float: 'left',
    width: '45%',
    textAlign:'right',
    lineHeight:'20px'
}

const camControlCol3 ={
    float: 'left',
    width: '30%',
    textAlign:'right'
}

const fullPreviewButton ={
    wdith:'100%'
}




