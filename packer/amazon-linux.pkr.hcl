# Source AMI Configuration for Amazon Linux in ap-south-1
source "amazon-ebs" "amazonlinux" {
  ami_name      = "amzn${var.amazonlinux_version}-hardened-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"
  instance_type = var.instance_type
  region        = var.aws_region
  
  # Fetch latest Amazon Linux AMI from ap-south-1
  source_ami_filter {
    filters = {
      name                = "al${var.amazonlinux_version}-ami-${var.amazonlinux_version}.*-x86_64"
      root-device-type    = "ebs"
      virtualization-type = "hvm"
      architecture        = "x86_64"
    }
    most_recent = true
    owners      = [var.source_ami_owners["amazonlinux"]]
  }
  
  ssh_username = "ec2-user"
  ssh_timeout  = "10m"
  
  # Enhanced tagging for better management
  tags = {
    Name        = "Amazon-Linux-${var.amazonlinux_version}-Hardened-AMI"
    Environment = "Production"
    Hardened    = "false"
    OS          = "AmazonLinux${var.amazonlinux_version}"
    Version     = var.amazonlinux_version
    Region      = var.aws_region
    BuiltBy     = "Packer"
    BuildDate   = formatdate("YYYY-MM-DD hh:mm:ss ZZZ", timestamp())
  }
  
  # Copy AMI to multiple regions if needed
  ami_regions = var.ami_regions
  
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
  
  iam_instance_profile = "packer-ami-builder"
}

build {
  sources = ["source.amazon-ebs.amazonlinux"]
  
  provisioner "ansible" {
    playbook_file    = "../ansible/playbook.yml"
    user             = "ec2-user"
    use_proxy        = false
    ansible_env_vars = ["ANSIBLE_HOST_KEY_CHECKING=False"]
    extra_arguments  = [
      "--extra-vars", "ansible_python_interpreter=/usr/bin/python3",
      "--extra-vars", "hardening_level=cis_level1"
    ]
  }
  
  post-processor "manifest" {
    output     = "manifest-amzn.json"
    strip_path = true
  }
}
