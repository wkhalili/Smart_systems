'''
Second Kafka consumer.
- Recieves the selected poses and features.
- Applies the model
- Sends to consumer3:
    - finished execution
    - executing status of the model
'''

from kafka import KafkaConsumer, KafkaProducer
import json
import lab_config as config

# To consume latest messages and auto-commit offsets
consumer = KafkaConsumer('json-topic2',
                         bootstrap_servers=['localhost:9092'],
                         auto_offset_reset='latest') # earliest  latest

producer = KafkaProducer(bootstrap_servers=['localhost:9092'],
                         value_serializer=lambda m: 
                         json.dumps(m).encode('ascii'))


class Shoulder_Exercise:    
    def __init__(self):        
        self.state = 'parallel'
        self.moves = 0
        self.move_shoulder = 0
        self.move_start_time = 0
        self.move_duration = 0
        
    def execute(self, pose_features):        
        shoulder = self.get_lower_shoulder(pose_features)
        move_complete = 0 
        
        # Update state of movement
        if self.state == 'parallel':
            self.move_start_time = pose_features['timestamp']
            if shoulder != 'parallel':
                self.state = 'turn_in'
                self.move_shoulder = shoulder
                print('TURN IN')
        elif self.state == 'turn_in':
            if pose_features['corner'] >= config.move_end_corener:
                self.state = 'turn_out'
                print('TURN OUT')
            # Detect when move is cancelled
            if (shoulder == 'parallel') and ((pose_features['corner']+2) < config.move_start_corner): 
                self.state = 'parallel'
                print('CANCEL')
        elif self.state == 'turn_out':
            if shoulder == 'parallel':
                self.state = 'parallel'
                self.moves += 1
                move_complete = 1
                print('COMPLETE, no '+str(self.moves))
                
        # Get duration of current move (no problem if move_start_time is not set)
        self.move_duration = pose_features['timestamp'] - self.move_start_time
        print(self.move_duration)
        
        # Move checks
        warning = ""
        if (self.state == 'turn_in') or (self.state == 'turn_out'):
            # Check movement speed (when detetion score is ok)
            if pose_features['corner/sec'] > config.move_speed_warning:
                if pose_features['score'] > config.move_speed_warning_min_score:
                    warning = 'Moving to fast now'
        if move_complete:            
            if (self.move_duration >= (config.move_druation_warning*1000)): # duration is in ms
                warning = 'Executed excercise to slow'
        if warning:
            print(warning)
            producer.send('json-topic2', {'warning' : warning})
            
        # Return results
        if move_complete:                
            # Return move info
            move_finish = {'moves_total': self.moves,
                          'shoulder': self.move_shoulder,
                          'duration': self.move_duration}
            return move_finish
        return 0
    
    def get_lower_shoulder(self, pose_features):
        shoulder = pose_features['shoulder']
        # Check if lower shoulder is not actually straight
        if (pose_features['corner'] < config.move_start_corner):
            shoulder = 'parallel'
        return shoulder
    
    def get_status(self, data_corner):
        corner_direction = config.move_start_corner
        if (self.state == 'turn_in'):
            corner_direction = config.move_end_corener
        status = {'state' : self.state,
                  'shoulder' : self.move_shoulder,
                  'corner' : data_corner['corner'],
                  'corner_dir' : corner_direction,
                  'duration': self.move_duration}
        return status
        

''' Main loop '''
shoulder_excersie = Shoulder_Exercise()
for message in consumer:
    mes = json.loads(message.value.decode('ascii'))
    if 'reset' in mes :                
        print("Info: Reset")
        shoulder_excersie = Shoulder_Exercise()
    elif 'pose' in mes:             
        # Execute model
        move_complete = shoulder_excersie.execute(mes['pose'])        
        # Send results
        if(move_complete):
            producer.send('json-topic2', {'result' : move_complete})
        else:
            update = shoulder_excersie.get_status(mes['pose'])
            producer.send('json-topic2', {'update' : update})
    #else:
    #    print("Received unkown data: "+str(mes))
    
    