# Variables for AMI building in ap-south-1 region
variable "aws_region" {
  type    = string
  default = "ap-south-1"
}

variable "instance_type" {
  type    = string
  default = "t3.micro"
}

variable "rhel_version" {
  type    = string
  default = "9"
}

variable "amazonlinux_version" {
  type    = string
  default = "2023"
}

variable "source_ami_owners" {
  type = map(string)
  default = {
    rhel          = "309956199498"  # Red Hat official owner ID
    amazonlinux   = "137112412989"  # Amazon owner ID
  }
}

variable "ami_regions" {
  type    = list(string)
  default = ["ap-south-1"]
}

variable "build_timestamp" {
  type    = string
  default = null
}