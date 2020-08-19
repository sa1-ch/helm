import json
import random

# sample preprocess_handler (to be implemented by customer)
# This is a trivial example, where we simply generate random values
# But customers can read the data from inference_record and trasnform it into 
# a flattened json structure

def preprocess_handler(inference_record):
    event_data = inference_record.event_data
    input_data = {}
    output_data = {}
    
    print('-----------------------')
    
    print('inference_records'+inference_records)
    
    print('-----------------------')
    
    print('even_data'+event_data)
    
    print('-----------------------')
    
    
    return {**input_data, **output_data}