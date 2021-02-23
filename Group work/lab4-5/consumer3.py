'''
Third Kafka consumer.
Receives:
    - finished execution
    - executing status of the model
'''

from kafka import KafkaConsumer, KafkaProducer
import json
import matplotlib.pyplot as plt
import time
import logging

import lab_config as config


logger = logging.getLogger(__name__)
# message format
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
output_file = "output.log"
handler = logging.FileHandler(output_file)
handler.setFormatter(formatter)
# set minimal level to INFO
logger.setLevel(logging.INFO)
logger.addHandler(handler)

# To consume latest messages and auto-commit offsets
consumer = KafkaConsumer('json-topic2',
                         bootstrap_servers=['localhost:9092'],
                         auto_offset_reset='latest') # earliest  latest

producer = KafkaProducer(bootstrap_servers=['localhost:9092'],
                         value_serializer=lambda m: 
                         json.dumps(m).encode('ascii'))

moves_left_cnt = 0
moves_right_cnt = 0
state = 'parallel'
pose = None
warning = ''
warning_time_start = time.time()+config.warning_duration # +warning_duration otherwise warning starts immediately


def handle_finished_move(move_finish):    
    global moves_left_cnt
    global moves_right_cnt
    print()
    shoulder = move_finish['shoulder']
    if shoulder == 'leftShoulder':
        moves_left_cnt += 1
    elif shoulder == 'rightShoulder':
        moves_right_cnt += 1
    logger.info("Move "+shoulder+" complete in "+str(move_finish['duration']/1000)+" sec")
    logger.info("Moves left:  "+str(moves_left_cnt))
    logger.info("Moves right: "+str(moves_right_cnt))

def handle_update(status):
    global state
    state = status['state']     
    if state == 'parallel':
        logger.debug("State: "+str(status['state']))
    elif (state == 'turn_in') or (state == 'turn_out'):
        logger.debug("Moving " + status['shoulder']
                +" to "+str(status['corner_dir']) +" degrees"
                +" (pos: "+str(int(status['corner']))+" degrees"
                + ", time: "+str(status['duration']/1000)+" sec)")

plt.ion()
# live plot, to be called consequently
def liveplot_pose():
    # clear axes
    plt.gca().cla()     
    # plot keypoints
    if pose:
        shoulder = None
        for part in pose['keypoints']:
            x1 = part['position']['x']
            y1 = part['position']['y']
            plt.scatter(x1, y1, color='r')
            plt.text(x1, y1, part['part'], color='b', fontsize=10)
            # Draw line between shoulders
            if 'Shoulder' in part['part']:
                if not shoulder:
                    shoulder = (x1, y1)
                else:
                    x2,y2 = shoulder
                    plt.plot((x1, x2), (y1,y2), color='r')
    # plot warning    
    if time.time() < (warning_time_start + config.warning_duration):
        plt.text(500, 425, ('Warning: '+str(warning)), color='r', fontsize=10)
    # plot status
    plt.text(500, 450, ('Moves left: '+str(moves_left_cnt)), color='k', fontsize=10)
    plt.text(500, 475, ('Moves right: '+str(moves_right_cnt)), color='k', fontsize=10)
    plt.text(500, 500, ('Move state: '+str(state)), color='k', fontsize=10)
    # show plot
    plt.title('posenet')
    plt.axis([512, 0, 512, 0])
    plt.draw()
    plt.pause(0.1)  
   

try:
    logger.info("Consumer 3 started")
    for message in consumer:
        mes = json.loads(message.value.decode('ascii'))
        #print(mes)
        if 'result' in mes :
            handle_finished_move(mes['result'])
        elif 'update' in mes: 
            handle_update(mes['update'])
        elif 'pose' in mes:
            pose = (mes['pose'])
        elif 'warning' in mes:
            warning = (mes['warning'])
            logger.info('Warning: '+str(warning))
            warning_time_start = time.time()
        #else:
        #    print("Received unkown data: "+str(mes))
        liveplot_pose()
except:
    logging.exception('Consumer 3 quit')
    logging.shutdown()
    raise
    
    