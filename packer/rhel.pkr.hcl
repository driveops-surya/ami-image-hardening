packer {
  required_plugins {
    amazon = {
      source  = "github.com/hashicorp/amazon"
      version = "~> 1.2"
    }
    ansible = {
      source  = "github.com/hashicorp/ansible"
      version = "~> 1.1"
    }
  }
}

# Source AMI Configuration for RHEL in ap-south-1
source "amazon-ebs" "rhel" {
  ami_name      = "rhel-${var.rhel_version}-hardened-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"
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
  ssh_timeout  = "10m"
  
  # Enhanced tagging for better management
  tags = {
    Name        = "RHEL-${var.rhel_version}-Hardened-AMI"
    Environment = "Production"
    Hardened    = "false"
    OS          = "RHEL"
    Version     = var.rhel_version
    Region      = var.aws_region
    BuiltBy     = "Packer"
    BuildDate   = formatdate("YYYY-MM-DD hh:mm:ss ZZZ", timestamp())
  }
  
  # Copy AMI to multiple regions if needed
  ami_regions = var.ami_regions
  
  # Encryption settings
  encrypt_boot = true
  kms_key_id   = null  # Use default AWS managed key
  
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

build {
  sources = ["source.amazon-ebs.rhel"]
  
  # Ansible provisioning for hardening
  provisioner "ansible" {
    playbook_file    = "../ansible/playbook.yml"
    user             = "ec2-user"
    use_proxy        = false
    ansible_env_vars = [
      "ANSIBLE_HOST_KEY_CHECKING=False",
      "ANSIBLE_SSH_ARGS='-o ControlMaster=auto -o ControlPersist=60s'"
    ]
    extra_arguments = [
      "--extra-vars", "ansible_python_interpreter=/usr/bin/python3",
      "--extra-vars", "hardening_level=cis_level1",
      "--verbose"
    ]
  }
  
  # Post-processor to generate manifest (kept)
  post-processor "manifest" {
    output     = "manifest-rhel.json"
    strip_path = true
  }
  
  # REMOVED: amazon-import post-processor (not needed for standard AMI builds)
}