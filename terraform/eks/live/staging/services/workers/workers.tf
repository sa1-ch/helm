module "workers" {
  source = "../../../../modules/services/workers"
  worker_groups = [
    {
      name                                     = "mle-shipping-forecast-asg-1"
      instance_name                            = "mle-shipping-forecast-ondemand-instances"
      instance_type                            = "c5.4xlarge"
      desired_capacity                         = 1
      min_size                                 = 0
      max_size                                 = 120
      on_demand_base_capacity                  = 0
      on_demand_percentage_above_base_capacity = 100
      #additional_userdata = "sudo yum install -y nfs-utils amazon-efs-utils"
    }

  ]
}
