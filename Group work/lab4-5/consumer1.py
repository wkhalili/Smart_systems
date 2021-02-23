'''
First Kafka consumer.
- Recieves the 17 poses from posenet + timestamp.
- Deletes the not used pose parts
- Calculates features (corner, cahnged degrees per second)
- Sends to conusmer 2
  - selected poses + features
  - if score is acceptable
'''

from kafka import KafkaConsumer, KafkaProducer
import json
import math
import lab_config as config

# To consume latest messages and auto-commit offsets
consumer = KafkaConsumer('json-topic',
                         bootstrap_servers=['localhost:9092'],
                         auto_offset_reset='latest') # earliest  latest

producer = KafkaProducer(bootstrap_servers=['localhost:9092'],
                         value_serializer=lambda m: 
                         json.dumps(m).encode('ascii'))

# Comment out the unused pose parts
use_parts = ['nose',
              'leftEye',
              'rightEye',
              #'leftEar',
              #'rightEar',
              'leftShoulder',
              'rightShoulder',
              #'leftElbow',
              #'rightElbow',
              #'leftWrist',
              #'rightWrist',
              #'leftHip',
              #'rightHip',
              #'leftKnee',
              #'rightKnee',
              #'leftAnkle',
              #'rightAnkle'
             ]

def remove_unused_parts(pose):
    remove_indices = []
    for index, part in enumerate((pose['excercise']['keypoints'])):
        if part['part'] not in use_parts:
            remove_indices.append(index)
    # remove reversed becose otherwise does the indexorder change
    for index in reversed(remove_indices):
        del pose['excercise']['keypoints'][index]   
    return pose


def pose_acceptable(pose, min_part_score):
    for part in (pose['excercise']['keypoints']):
        if part['score'] < min_part_score:
            print("Warning: Throw away pose because score "+str(part['score'])+" < "+str(min_part_score)+" for "+str(part['part']))
            return False        
    return True


def pretty_print_pose(pose):
    print()
    print('time:  ' + str(pose['excercise']['timestamp']))
    for part in (pose['excercise']['keypoints']):
        print(part)

def calculate_corner(data):    
    # Calculate the degrees between the shoulders
    index_shoulder_l = use_parts.index('leftShoulder')
    index_shoulder_r = use_parts.index('rightShoulder')
    shoulder_width = abs(data[index_shoulder_l]['position']['x'] - data[index_shoulder_r]['position']['x'])
    shoulder_height = abs(data[index_shoulder_l]['position']['y'] - data[index_shoulder_r]['position']['y'])
    x = shoulder_height / shoulder_width
    corner = math.degrees(math.atan(x))    
    # Check which shoulder is lower    
    shoulder = 'leftShoulder'
    if (data[index_shoulder_l]['position']['y'] < data[index_shoulder_r]['position']['y']):
        shoulder = 'rightShoulder'  
    # Calculate score
    score = (data[index_shoulder_l]['score'] + data[index_shoulder_r]['score']) / 2
    return {'corner':corner, 'shoulder':shoulder, 'score':score}

def degrees_per_sec(data, data_prev):    
    diff_corner = abs(data['corner'] - data_prev['corner'])
    diff_time_ms = abs(data['timestamp'] - data_prev['timestamp'])
    degree_per_sec = diff_corner / diff_time_ms * 1000 # timestamp is in ms
    return degree_per_sec

    
''' Main loop '''
# Reset the next consumer
producer.send('json-topic2', {'reset' : 0})

pose_data_prev = None
for message in consumer:    
    # Handle received data
    pose = json.loads(message.value.decode('ascii'))
    pose = remove_unused_parts(pose)    
    #pretty_print_pose(pose)
    if not pose_acceptable(pose, config.min_part_score):
        producer.send('json-topic2', {'warning' : "Detection score to low"})
    else:
        pose_data = {'keypoints' : pose['excercise']['keypoints']}
        # Calculate the corner difference between shoulders
        corner = calculate_corner(pose['excercise']['keypoints'])
        pose_data.update(corner)
        # Add timestamp
        pose_data.update({'timestamp' : pose['excercise']['timestamp']})
        # Add difference between corner over time
        # Send data to next consumer
        if pose_data_prev:
            degree_per_sec = degrees_per_sec(pose_data, pose_data_prev)
            pose_data.update({'corner/sec' : degree_per_sec})
            #print('corner: ' + str(data_corner))        
            producer.send('json-topic2', {'pose' : pose_data})
            
        pose_data_prev = pose_data

