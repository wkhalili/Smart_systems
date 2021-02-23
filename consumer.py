from kafka import KafkaConsumer
import json
import numpy as np
import math
# To consume latest messages and auto-commit offsets


Parts=["nose","leftEye","rightEye","leftEar","rightEar","leftShoulder","rightShoulder","leftElbow","rightElbow","leftWrist","rightWrist","leftHip","rightHip","leftKnee","rightKnee","leftAnkle","rightAnkle"]
#       0       1           2       3               4       5               6               7           8           9           10          11          12      13          14          15          16       
def sortTime(st):
    ls=list()
    for i in st:
        ls.append(i['timestamp'])
    return list(np.sort(np.array(ls)))
def findDist(x1,y1,x2,y2):
    return(math.sqrt(math.pow((x2-x1),2)+math.pow((y2-y1),2)))
def positionList(st,part,tm):
    ls_x=list()
    ls_y=list()    
    for i in tm:
        for j in st:
            if j['timestamp'] == i:
                for k in j['keypoints']:
                    if k['part'] == part:
                        ls_x.append(k['position']['x'])
                        ls_y.append(k['position']['y'])
    return ls_x, ls_y


def process(st,Part):
    tm=sortTime(st)
    l_sh_x,l_sh_y=positionList(st,Part[5],tm)    
    r_sh_x,r_sh_y=positionList(st,Part[6],tm)    
    l_e_x,   l_e_y=positionList(st,Part[7],tm)    
    r_e_x, r_e_y=positionList(st,Part[8],tm)
    l_w_x, l_w_y=positionList(st,Part[9],tm)
    r_w_x, r_w_y=positionList(st,Part[10],tm)
    l_k_x, l_k_y=positionList(st,Part[13],tm)
    r_k_x, r_k_y=positionList(st,Part[14],tm)
    l_h_x, l_h_y=positionList(st,Part[11],tm)
    r_h_x, r_h_y=positionList(st,Part[12],tm)
    l_a_x, l_a_y=positionList(st,Part[15],tm)
    r_a_x, r_a_y=positionList(st,Part[16],tm)
    
    a_rs_lw=list()
    ls=list()
    for i in range(len(l_a_x)):       
        #ls.append(findCompAngle(l_sh_x[i],l_sh_y[i],r_sh_x[i],r_sh_y[i],r_e_x[i],r_e_y[i]))
        #ls.append(findCompAngle(r_sh_x[i],r_sh_y[i],l_sh_x[i],l_sh_y[i],l_e_x[i],l_e_y[i]))
        #print("right under arm =",findCompAngle(r_h_x[i],r_h_y[i],r_sh_x[i],r_sh_y[i],r_e_x[i],r_e_y[i]))
        #print("left under arm =",findCompAngle(l_h_x[i],l_h_y[i],l_sh_x[i],l_sh_y[i],l_e_x[i],l_e_y[i]))
        print("right shoulder =",findCompAngle(l_sh_x[i],l_sh_y[i],r_sh_x[i],r_sh_y[i],r_w_x[i],r_w_y[i]))
        #print("left shoulder =",findCompAngle(r_h_x[i],r_h_y[i],l_sh_x[i],l_sh_y[i],l_e_x[i],l_e_y[i]))
        print("right elbow =",findCompAngle(r_sh_x[i],r_sh_y[i],r_e_x[i],r_e_y[i],r_w_x[i],r_w_y[i]))
        #print("left elbow =",findCompAngle(l_sh_x[i],l_sh_y[i],l_e_x[i],l_e_y[i],l_w_x[i],l_w_y[i]))
        #print("right knee =",findCompAngle(r_h_x[i],r_h_y[i],r_k_x[i],r_k_y[i],r_a_x[i],r_a_y[i]))
        #print("left knee =",findCompAngle(l_h_x[i],l_h_y[i],l_k_x[i],l_k_y[i],l_a_x[i],l_a_y[i]))
        
        
    return ls
def findCompAngle(p1x,p1y,p2x,p2y,p3x,p3y):#A,B,C
    a=findDist(p2x, p2y,p3x,p3y)
    b=findDist(p3x, p3y,p1x,p1y)
    c=findDist(p1x, p1y,p2x,p2y)
    angle=(math.pow(a,2)+math.pow(c,2)-math.pow(b,2))/(2*a*c)
    #return math.atan(c/a)
    return (180/np.pi)*(np.arccos(angle))
consumer = KafkaConsumer('json-topic2',
                         bootstrap_servers=['localhost:9092'],
                         auto_offset_reset='latest')

for message in consumer:
    
    st=json.loads(message.value.decode('ascii'))
    
    print(st['excercise'][0]['score'])
    print(st['excercise'][1]['score'])
    
    if len(st['excercise']) > 1:
        process(st['excercise'], Parts)
    #print(len(st['excercise']))
    #print (len(message.value.decode('ascii')))


