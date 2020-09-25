from metaflow import FlowSpec, step, batch, Parameter, JSONType, batch, resources
import json
from datetime import datetime
import os
import subprocess
from dag_generator import get_shipments_dag
import random, time

import os


def deployment_info(context):
    return json.dumps({"who": context.user_name, "when": datetime.now().isoformat()})

def print_list(lst, temp_string=""):
    temp_string = temp_string + "\t"
    for i in lst:
        if isinstance(i, list):
            print_list(i, temp_string)
        else:
            print(temp_string, i)


class ShipmentsDemoTestOne(FlowSpec):
    deployment_info = Parameter("deployment_info", type=JSONType, default=deployment_info)
    app_cfg = Parameter("app_cfg", type=str, default="s3://mcd-dev-1-metaflows3bucket-lyv8kblmqdjy/inputs/app_cfg.yml")
    job_cfg = Parameter("job_cfg", type=str, default="s3://mcd-dev-1-metaflows3bucket-lyv8kblmqdjy/inputs/job_cfg.yml")


    @resources(cpu=2, memory=1000)
    @step
    def start(self):
        print(self.deployment_info)
        self.pipeline_list = get_shipments_dag(
            app_cfg=self.app_cfg, 
            job_cfg=self.job_cfg
        )
        print_list(self.pipeline_list)
        self.next(self.parent_task, foreach="pipeline_list")


    @resources(cpu=2, memory=1000)
    @step
    def parent_task(self):
        cmd = self.input[0]["parent_task"]["cmd"]
        print("Task ID:", self.input[0]["parent_task"]["id"])
        print("Executing CMD:", cmd)
        
        subprocess.check_call(cmd, shell=True)
        self.train_list = self.input[1]
        self.next(self.train_task, foreach="train_list")
        
    
    @resources(cpu=6, memory=10000)
    @step
    def train_task(self):
        self.train = self.input[0]
        self.score_list = self.input[1]
        self.merge_score = self.input[2]
        
        cmd = self.train["train_task"]["cmd"]
        print("Task ID:", self.train["train_task"]["id"])
        print("Executing CMD:", cmd)
        
        subprocess.check_call(cmd, shell=True)
        self.next(self.score_task, foreach="score_list")
        
        
    @resources(cpu=6, memory=6000)
    @step
    def score_task(self):
        cmd = self.input["score_task"]["cmd"]
        print("Task ID:", self.input["score_task"]["id"])
        print("Executing CMD:", cmd)
        
        subprocess.check_call(cmd, shell=True)
        self.next(self.score_join)
        
        
    @resources(cpu=2, memory=1500)
    @step
    def score_join(self, inputs):
        self.merge_artifacts(inputs)
        
        cmd = self.merge_score["merge_score_task"]["cmd"]
        print("Task ID:", self.merge_score["merge_score_task"]["id"])
        print("Executing CMD:", cmd)
        
        subprocess.check_call(cmd, shell=True)
        self.next(self.train_join)

        
    @resources(cpu=2, memory=1000)
    @step
    def train_join(self, inputs):
        self.merge_artifacts(inputs, exclude=["merge_score", "score_list", "train"])
        self.next(self.parent_join)
        

    @resources(cpu=2, memory=1000)
    @step
    def parent_join(self, inputs):
        self.next(self.end)


    @resources(cpu=2, memory=1000)
    @step
    def end(self):
        print("end")


if __name__ == "__main__":
    ShipmentsDemoTestOne()
