# Variable values for Packer (use with -var-file=variables.pkrvars.hcl)
aws_region = "ap-south-1"
instance_type = "t3.micro"
rhel_version = "9"
amazonlinux_version = "2026"
source_ami_owners = {
  rhel        = "309956199498"
  amazonlinux = "137112412989"
}
ami_regions = ["ap-south-1"]
build_timestamp = null
