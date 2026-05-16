packer {
  required_plugins {
    amazon = {
      version = ">= 1.2.8"
      source  = "github.com/hashicorp/amazon"
    }

    ansible = {
      version = ">= 1.1.1"
      source  = "github.com/hashicorp/ansible"
    }
  }
}

source "amazon-ebs" "rhel" {

  ami_name      = "rhel-${var.rhel_version}-hardened-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"
  instance_type = var.instance_type
  region        = var.aws_region

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

  iam_instance_profile = "packer-ami-builder"

  encrypt_boot = true
  kms_key_id   = null

  ami_regions = var.ami_regions

  launch_block_device_mappings {
    device_name           = "/dev/xvda"
    volume_size           = 20
    volume_type           = "gp3"
    delete_on_termination = true
    encrypted             = true
  }

  tags = {
    Name            = "RHEL-${var.rhel_version}-Hardened-AMI"
    Environment     = "Production"
    Hardened        = "false"
    OS              = "RHEL"
    Version         = var.rhel_version
    Region          = var.aws_region
    BuiltBy         = "Packer"
    SecurityStatus  = "PendingScan"
    ComplianceLevel = "CIS-Level1"
    BuildDate       = formatdate("YYYY-MM-DD hh:mm:ss ZZZ", timestamp())
  }
}

build {

  sources = ["source.amazon-ebs.rhel"]

  provisioner "shell" {
    inline = [
      "sudo dnf clean all",
      "sudo dnf update -y",
      "sudo dnf install -y python3 python3-pip unzip tar wget curl"
    ]
  }

  provisioner "ansible" {

    playbook_file = "../ansible/playbook.yml"

    user      = "ec2-user"
    use_proxy = false

    ansible_env_vars = [
      "ANSIBLE_HOST_KEY_CHECKING=False",
      "ANSIBLE_FORCE_COLOR=True",
      "PYTHONUNBUFFERED=1",
      "ANSIBLE_SSH_ARGS='-o ControlMaster=auto -o ControlPersist=60s'"
    ]

    extra_arguments = [
      "--extra-vars", "ansible_python_interpreter=/usr/bin/python3",
      "--extra-vars", "hardening_level=cis_level1",
      "--verbose"
    ]
  }

  post-processor "manifest" {
    output     = "manifest-rhel.json"
    strip_path = true
  }
}