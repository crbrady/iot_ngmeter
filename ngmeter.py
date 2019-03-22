# Written by Ryan Brady, Loosly based on an intel opencv tutorial
# https://software.intel.com/en-us/articles/analog-gauge-reader-using-opencv

import cv2
import numpy as np
import paho.mqtt.client as mqtt
import time
import datetime


print ("Starting with OpenCV version %s..." %(cv2.__version__ ))
DEBUG = False
dateFormat = '%Y-%m-%d %H:%M:%S'

timeSinceLastDebugRequest = 0

def sortByX(e):
  return e.x

def dist_2_pts(x1, y1, x2, y2):
    return np.sqrt((x2 - x1)**2 + (y2 - y1)**2)

class DialParams:
    def __init__(self, x, y, r):
        self.x = x
        self.y = y
        self.r = r
    def __repr__(self):
        return repr((self.x, self.y, self.r))

def calibrate_gauge(file_name):
    global DEBUG
    img = cv2.imread('%s' %(file_name))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    output_img = cv2.cvtColor(gray,cv2.COLOR_GRAY2RGB)

    #print "reading file "
    height, width = img.shape[:2]
    circleMin = height / 12
    circleMax = height / 2
    circleMaxDist = height / 5
    #print "Image h=%s w=%s  --  circle detect min=%s max=%s maxDist= %s" %(height, width, circleMin, circleMax, circleMaxDist)
    #print "h=%s w=%s" %(height, width)

    circles = cv2.HoughCircles(gray,cv2.HOUGH_GRADIENT,1,int(circleMaxDist),param1=100,param2=70,minRadius=int(circleMin),maxRadius=int(circleMax))
    circles = np.uint16(np.around(circles))

    smallestCircle = 1000000;
    largestCircle = 0;
    for i in circles[0,:]:
        if i[2] < smallestCircle:
            smallestCircle = i[2]
        if i[2] > largestCircle:
            largestCircle = i[2]
    circleSizeMidPoint = (smallestCircle + largestCircle) /2

    topDials = [];
    bottomDials = [];
    for i in circles[0,:]:
        newDial = DialParams(i[0],i[1],i[2]);
        if newDial.r < circleSizeMidPoint:
            newDial.yShift = 3
            topDials.append(newDial)
        else:
            newDial.yShift = 5
            bottomDials.append(newDial)

    bottomDials.sort(key=sortByX)
    topDials.sort(key=sortByX)

    AllDials=[];

    millionDial = bottomDials[0]
    millionDial.unitsPerRev = 1000000
    millionDial.xShift = 0
    millionDial.dialClockwise = False
    AllDials.append(millionDial)

    hundredThouDial = bottomDials[1]
    hundredThouDial.unitsPerRev = 100000
    hundredThouDial.xShift = 0
    hundredThouDial.dialClockwise = True
    AllDials.append(hundredThouDial)

    tenThouDial = bottomDials[2]
    tenThouDial.unitsPerRev = 10000
    tenThouDial.xShift = 4
    tenThouDial.dialClockwise = False
    AllDials.append(tenThouDial)

    thouDial = bottomDials[3]
    thouDial.unitsPerRev = 1000
    thouDial.xShift = 7
    thouDial.dialClockwise = True
    AllDials.append(thouDial)

    halfDial = topDials[0]
    halfDial.unitsPerRev = 10
    halfDial.xShift = 0
    halfDial.dialClockwise = False
    AllDials.append(halfDial)

    twoDial = topDials[1]
    twoDial.unitsPerRev = 40
    twoDial.xShift = 0
    twoDial.dialClockwise = False
    AllDials.append(twoDial)

    totalValue = 0
    for i in range(0, len(AllDials)):
        AllDials[i] = getLineForDial(img, AllDials[i]);
        AllDials[i] = getAngleForDial(AllDials[i]);
        AllDials[i] = getValueForDial(AllDials[i]);
        totalValue += AllDials[i].value

        if (DEBUG == True):
            cv2.line(output_img, AllDials[i].line[0], AllDials[i].line[1], (0, 255, 0), 2)
            cv2.circle(output_img,(AllDials[i].x ,AllDials[i].y),AllDials[i].r,(0,255,0),2)
            cv2.circle(output_img,(AllDials[i].x + AllDials[i].xShift ,AllDials[i].y + AllDials[i].yShift),2,(0,0,255),3)
            cv2.putText(output_img, '%s degrees' %(AllDials[i].angle), (AllDials[i].x - int(AllDials[i].r *.5) ,AllDials[i].y - AllDials[i].r - 10), cv2.FONT_HERSHEY_SIMPLEX, .4,(0,0,255),1,cv2.LINE_AA)
            cv2.putText(output_img, '%s cubic feet' %(AllDials[i].value), (AllDials[i].x - int(AllDials[i].r *.5) ,AllDials[i].y - AllDials[i].r - 30), cv2.FONT_HERSHEY_SIMPLEX, .4,(0,0,255),1,cv2.LINE_AA)

    client.publish("ngmeter/cubicfeet", totalValue, qos=0, retain=False)
    
    if (DEBUG == True):
        cv2.putText(output_img, '%s cubic feet' %(totalValue), (int(width *.55) , int(height * .25)), cv2.FONT_HERSHEY_SIMPLEX, 1,(0,0,255),2,cv2.LINE_AA)
        dateString = time.strftime("%m/%d/%Y %l:%M:%S %p")
        cv2.putText(output_img, '%s' %(dateString), (int(width *.55) , int(height * .1)), cv2.FONT_HERSHEY_SIMPLEX, .5,(0,0,255),1,cv2.LINE_AA)
        debug_img = cv2.imencode('.jpg', output_img)[1].tostring()
        client.publish("ngmeter/debug_img", debug_img, qos=2)

    #cv2.imshow('detected circles',output_img)
    #cv2.waitKey(0)
    #cv2.destroyAllWindows()

    return totalValue

def getValueForDial(dial):
    steps = dial.angle /36
    dial.steps = int(steps)
    dial.value = int(steps) * dial.unitsPerRev /10
    return dial

def getAngleForDial(dial):
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

def getLineForDial(img, dial):
    x = dial.x
    y = dial.y
    r = dial.r

    gray2 = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thresh = 80
    maxValue = 255
    th, dst2 = cv2.threshold(gray2, thresh, maxValue, cv2.THRESH_BINARY_INV);

    #print "%s" %(dial.unitsPerRev)
    minLineLength = 10
    maxLineGap = 0
    lines = cv2.HoughLinesP(image=dst2, rho=3, theta=np.pi / 180, threshold=100,minLineLength=minLineLength, maxLineGap=0)  # rho is set to 3 to detect more lines, easier to get more then filter them out later

    #print "Found %s lines" %(len(lines))

    final_line_list = []

    diff1LowerBound = 0.0 #diff1LowerBound and diff1UpperBound determine how close the line should be from the center
    diff1UpperBound = 0.59
    diff2LowerBound = 0.6 #diff2LowerBound and diff2UpperBound determine how close the other point of the line should be to the outside of the gauge
    diff2UpperBound = 1.3

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

    #print "Lines trimed to %s lines" %(len(final_line_list))
    dial.line = [(x + dial.xShift, y + dial.yShift), (finalX, finalY)];
    return dial;

def main():
    global DEBUG
    global timeSinceLastDebugRequest
    adjustedTimeSince = timeSinceLastDebugRequest + 10
    if(adjustedTimeSince > time.time()):
        DEBUG = True
        print("Running in debug image mode...")
    else:
        DEBUG = False

    start = time.time()
    file_name='cam7.jpg'
    # name the calibration image of your gauge 'gauge-#.jpg', for example 'gauge-5.jpg'.  It's written this way so you can easily try multiple images
    units = calibrate_gauge("test.jpg")
    #feed an image (or frame) to get the current value, based on the calibration, by default uses same image as calibration
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

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
