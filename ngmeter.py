# Written by Ryan Brady, Loosly based on an intel opencv tutorial
# https://software.intel.com/en-us/articles/analog-gauge-reader-using-opencv

import cv2
import numpy as np
import paho.mqtt.client as mqtt
import time
import datetime
import io
import yaml

with open("config.yaml", 'r') as ymlfile:
    config = yaml.load(ymlfile)

print ("Starting with OpenCV version %s..." %(cv2.__version__ ))

mqttDebug = True
timeSinceLastDebugRequest = 0
dateFormat = '%Y-%m-%d %H:%M:%S'

if(config['debug']['useFileImg'] == False):
    import picamera
    import picamera.array

class DialParams:
    def __init__(self, x, y, r):
        self.x = x
        self.y = y
        self.r = r
        self.value = None
        self.line = None
        self.angle = None
    def __repr__(self):
        return repr((self.x, self.y, self.r))

def sortByX(e):
  return e.x

def dist_2_pts(x1, y1, x2, y2):
    return np.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def configure_dial(dials, rowKey, index):
    newDial = dials[index]
    newDial.unitsPerRev = config[rowKey][index]['unitsPerRev']
    newDial.xShift = config[rowKey][index]['xShift']
    newDial.dialClockwise = config[rowKey][index]['dialClockwise']
    newDial.name = config[rowKey][index]['name']
    return newDial

def getImage():
    if(config['debug']['useFileImg'] == True):
        img = cv2.imread(config['debug']['fileImgName'])
    else:
        stream = io.BytesIO()
        with picamera.PiCamera() as camera:
            camera.resolution = (config['capture']['width'], config['capture']['height'])
            camera.rotation = config['capture']['rotation']
            #camera.start_preview()
            #time.sleep(2)
            with picamera.array.PiRGBArray(camera) as stream:
                camera.capture(stream, format="bgr")
                img = stream.array

    if(config['mode']['passthrough']== True):
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 100]
        result, encimg = cv2.imencode('.jpg', img, encode_param)
        client.publish("ngmeter/raw_img", encimg, qos=2)

def measureMeter(img):
    global config

    if(config['mode']['passthrough']== True):
        return

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    output_img = cv2.cvtColor(gray,cv2.COLOR_GRAY2RGB)

    if(config['debug']['localImg'] == True):
        cv2.imshow('Raw Image',output_img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    height, width = img.shape[:2]
    circleMin = height / config['circleFindParams']['circleMinAsFractionOfTotalHeight']
    circleMax = height / config['circleFindParams']['circleMaxAsFractionOfTotalHeight']
    circleMaxDist = height / config['circleFindParams']['circleMaxDistAsFractionOfTotalHeight']
    if (config['debug']['detailedConsole']):
        print ("Image h=%s w=%s  --  circle detect min=%s max=%s maxDist= %s" %(height, width, circleMin, circleMax, circleMaxDist))

    circles = cv2.HoughCircles(gray,cv2.HOUGH_GRADIENT,1,int(circleMaxDist),param1=100,param2=70,minRadius=int(circleMin),maxRadius=int(circleMax))
    circles = np.uint16(np.around(circles))

    circleYMax = 0;
    circleYMin = 100000;

    for i in circles[0,:]:
        if(i[1] > circleYMax):
            circleYMax = i[1]
        if(i[1] < circleYMin):
            circleYMin = i[1]

    circleYMidPoint = (circleYMin + circleYMax) / 2

    topDials = [];
    bottomDials = [];

    for i in circles[0,:]:
        newDial = DialParams(i[0], i[1], i[2]);
        if newDial.y < circleYMidPoint:
            newDial.yShift = 3
            topDials.append(newDial)
        else:
            newDial.yShift = 5
            bottomDials.append(newDial)

    bottomDials.sort(key=sortByX)
    topDials.sort(key=sortByX)

    if (config['debug']['detailedConsole']):
        print("found %s top circles and %s bottom circles" %(len(topDials), len(bottomDials)))
    AllDials=[];

    AllDials.append( configure_dial(bottomDials, 'bottomDials', 0) )
    AllDials.append( configure_dial(bottomDials, 'bottomDials', 1) )
    AllDials.append( configure_dial(bottomDials, 'bottomDials', 2) )
    AllDials.append( configure_dial(bottomDials, 'bottomDials', 3) )

    AllDials.append( configure_dial(topDials, 'topDials', 0) )
    AllDials.append( configure_dial(topDials, 'topDials', 1) )


    totalValue = 0
    lines = getAllLines(img)
    for i in range(0, len(AllDials)):
        AllDials[i] = getLineForDial(lines, AllDials[i]);
        AllDials[i] = getAngleForDial(AllDials[i]);
        AllDials[i] = getValueForDial(AllDials[i]);
        if(AllDials[i].value is None):
            print('Read Dials Failed on %s' %(AllDials[i].name))
            return 'Error'
        totalValue += AllDials[i].value

        if (mqttDebug == True):
            cv2.line(output_img, AllDials[i].line[0], AllDials[i].line[1], (0, 255, 0), 2)
            cv2.circle(output_img,(AllDials[i].x ,AllDials[i].y),AllDials[i].r,(0,255,0),2)
            cv2.circle(output_img,(AllDials[i].x + AllDials[i].xShift ,AllDials[i].y + AllDials[i].yShift),2,(0,0,255),3)
            cv2.putText(output_img, '%s degrees' %(AllDials[i].angle), (AllDials[i].x - int(AllDials[i].r *.5) ,AllDials[i].y - AllDials[i].r - 10), cv2.FONT_HERSHEY_SIMPLEX, .4,(0,0,255),1,cv2.LINE_AA)
            cv2.putText(output_img, '%s cubic feet' %(AllDials[i].value), (AllDials[i].x - int(AllDials[i].r *.5) ,AllDials[i].y - AllDials[i].r - 30), cv2.FONT_HERSHEY_SIMPLEX, .4,(0,0,255),1,cv2.LINE_AA)

    client.publish("ngmeter/cubicfeet", totalValue, qos=0, retain=False)

    if (mqttDebug == True):
        cv2.putText(output_img, '%s cubic feet' %(totalValue), (int(width *.55) , int(height * .25)), cv2.FONT_HERSHEY_SIMPLEX, 1,(0,0,255),2,cv2.LINE_AA)
        dateString = time.strftime("%m/%d/%Y %l:%M:%S %p")
        cv2.putText(output_img, '%s' %(dateString), (int(width *.55) , int(height * .1)), cv2.FONT_HERSHEY_SIMPLEX, .5,(0,0,255),1,cv2.LINE_AA)
        debug_img = cv2.imencode('.jpg', output_img)[1].tostring()
        client.publish("ngmeter/debug_img", debug_img, qos=2)

    if(config['debug']['localImg'] == True):
        cv2.imshow('Final Debug',output_img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    return totalValue

def getValueForDial(dial):
    if(dial.angle is None):
        return dial
    steps = dial.angle / 36
    dial.steps = int(steps)
    dial.value = int(steps) * dial.unitsPerRev / 10
    return dial

def getAngleForDial(dial):
    global config

    if(dial.line is None):
        return dial

    final_angle =  0
    x_angle = dial.line[1][0] - dial.line[0][0]
    y_angle = dial.line[1][1] - dial.line[0][1]

    if dial.dialClockwise:
        x_angle = x_angle * -1

    res = np.arctan(np.divide(float(y_angle), float(x_angle)))
    res = np.rad2deg(res)
    if x_angle > 0 and y_angle > 0:  #in quadrant I
        final_angle = 270 - res
    if x_angle < 0 and y_angle > 0:  #in quadrant II
        final_angle = 90 - res
    if x_angle < 0 and y_angle < 0:  #in quadrant III
        final_angle = 90 - res
    if x_angle > 0 and y_angle < 0:  #in quadrant IV
        final_angle = 270 - res

    dial.angle = int(final_angle)
    return dial


def getAllLines(img):
    global config

    gray2 = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blackWhiteThreshold = config['lineFindParams']['blackWhiteThreshold']
    maxImgValue = config['lineFindParams']['maxImgValue']
    th, dst2 = cv2.threshold(gray2, blackWhiteThreshold, maxImgValue, cv2.THRESH_BINARY_INV);

    houghTheshold = config['lineFindParams']['houghTheshold']
    minLineLength = config['lineFindParams']['minLineLength']
    maxLineGap = config['lineFindParams']['maxLineGap']
    lines = cv2.HoughLinesP(image=dst2, rho=3, theta=np.pi / 180, threshold=houghTheshold, minLineLength=minLineLength, maxLineGap=maxLineGap)  # rho is set to 3 to detect more lines, easier to get more then filter them out later

    if(config['debug']['detailedConsole'] == True):
        print ("Found %s lines" %(len(lines)))
    return lines


def getLineForDial(lines, dial):
    global config

    x = dial.x
    y = dial.y
    r = dial.r


    final_line_list = []

    diff1LowerBound = config['lineForDialParams']['diff1LowerBound'] #diff1LowerBound and diff1UpperBound determine how close the line should be from the center
    diff1UpperBound = config['lineForDialParams']['diff1UpperBound']
    diff2LowerBound = config['lineForDialParams']['diff2LowerBound'] #diff2LowerBound and diff2UpperBound determine how close the other point of the line should be to the outside of the gauge
    diff2UpperBound = config['lineForDialParams']['diff2UpperBound']

    maxFoundDist = 0;
    finalX = 0;
    finaly = 0;

    for i in range(0, len(lines)):
        for x1, y1, x2, y2 in lines[i]:
            diff1 = dist_2_pts(x, y, x1, y1)  # x, y is center of circle
            diff2 = dist_2_pts(x, y, x2, y2)  # x, y is center of circle
            #set diff1 to be the smaller (closest to the center) of the two), makes the math easier
            fX = x2
            fY = y2
            if (diff1 > diff2):
                temp = diff1
                diff1 = diff2
                diff2 = temp
                fX = x1
                fY = y1

            # check if line is within an acceptable range
            if (((diff1<diff1UpperBound*r) and (diff1>diff1LowerBound*r) and (diff2<diff2UpperBound*r)) and (diff2>diff2LowerBound*r)):
                line_length = dist_2_pts(x1, y1, x2, y2)
                # add to final list
                final_line_list.append([x1, y1, x2, y2])

                if diff2 > maxFoundDist:
                    maxFoundDist = diff2
                    finalX = fX
                    finalY = fY

    print ("Lines trimed to %s lines, for %s" %(len(final_line_list), dial.name ))
    if(len(final_line_list) == 0):
        return dial
    else:
        dial.line = [(x + dial.xShift, y + dial.yShift), (finalX, finalY)];
        return dial

def main():
    global mqttDebug
    global timeSinceLastDebugRequest

    adjustedTimeSince = timeSinceLastDebugRequest + 10
    if(adjustedTimeSince > time.time()):
        mqttDebug = True
        print("Running in debug image mode...")
    else:
        mqttDebug = False

    start = time.time()
    # name the calibration image of your gauge 'gauge-#.jpg', for example
    # 'gauge-5.jpg'.  It's written this way so you can easily try multiple images
    img = getImage()
    units = measureMeter(img)
    # feed an image (or frame) to get the current value, based on the
    # calibration, by default uses same image as calibration

    end = time.time()
    print ("Current reading: %s  (took %.2f seconds)" %(units, (end - start)))
    time.sleep(2)
    main()

def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker with code %s" %(rc))
    client.subscribe("ngmeter/debug_img/request", qos=0)




# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    if(msg.topic == "ngmeter/debug_img/request"):
        #print("debug requested")
        global timeSinceLastDebugRequest
        timeSinceLastDebugRequest = time.time()

    #print(msg.topic+" "+str(msg.payload))

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("192.168.0.2", 1883, 60)
client.loop_start()

main()
