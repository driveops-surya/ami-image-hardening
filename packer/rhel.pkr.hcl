packer {
  required_plugins {
    amazon = {
      source  = "github.com/hashicorp/amazon"
      version = "~> 1.2"
    }
  }
}

# Variable declarations
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

variable "source_ami_owners" {
  type = map(string)
  default = {
    rhel = "309956199498"  # Red Hat official owner ID
  }
}

variable "build_timestamp" {
  type    = string
  default = null
}

variable "build_id" {
  type    = string
  default = null
}

# Source AMI Configuration for RHEL in ap-south-1
source "amazon-ebs" "rhel" {
  ami_name      = "rhel-${var.rhel_version}-base-${formatdate("YYYYMMDD-HHmmss", timestamp())}"
  instance_type = var.instance_type
  region        = var.aws_region
  
  # Fetch latest RHEL 9 AMI from ap-south-1
  source_ami_filter {
    filters = {
      name                = "RHEL-${var.rhel_version}.*_HVM-*"
      root-device-type    = "ebs"
      virtualization-type = "hvm"
      architecture        = "x86_64"
    }
    most_recent = true
    owners      = [var.source_ami_owners["rhel"]]
  }
  
  ssh_username = "ec2-user"
  ssh_timeout  = "15m"
  
  # Basic tags for the initial AMI
  tags = {
    Name        = "RHEL-${var.rhel_version}-Base-${formatdate("YYYYMMDD", timestamp())}"
    Environment = "Production"
    Hardened    = "false"
    OS          = "RHEL"
    Version     = var.rhel_version
    Region      = var.aws_region
    BuiltBy     = "Packer"
    BuildDate   = formatdate("YYYY-MM-DD hh:mm:ss ZZZ", timestamp())
    BuildID     = var.build_id != null ? var.build_id : "local"
    Stage       = "pre-hardening"
  }
  
  # Keep AMI private (default)
  # No ami_groups specified = private to your account
  
  # Encryption settings
  encrypt_boot = true
  
  # Volume configuration
  launch_block_device_mappings {
    device_name           = "/dev/xvda"
    volume_size           = 20
    volume_type           = "gp3"
    delete_on_termination = true
    encrypted             = true
  }
  
  # IAM instance profile for Packer
  iam_instance_profile = "packer-ami-builder"
}

# Build configuration
build {
  sources = ["source.amazon-ebs.rhel"]
  
  # Pre-provisioning: Ensure Python is installed (required for some Ansible modules)
  provisioner "shell" {
    inline = [
      "echo 'Waiting for cloud-init to complete...'",
      "sudo dnf update -y",
      "sudo dnf install -y python3 python3-pip",
      "sudo alternatives --set python /usr/bin/python3",
      "python3 --version",
      "echo 'Base system ready'"
    ]
  }
  
  # Note: Ansible hardening is NOT applied here.
  # Ansible will be applied later on the running EC2 instance.
  # This Packer build only creates a base RHEL AMI.
  
  # Post-processor to generate manifest
  post-processor "manifest" {
    output     = "manifest.json"
    strip_path = true
  }
}