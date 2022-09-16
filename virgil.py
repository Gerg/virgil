#!/usr/bin/env python3

import json
import re
import subprocess
import yaml

from collections import namedtuple

Scale = namedtuple("Scale", "instances type")
CPUData = namedtuple("CPUData", "cores vcpus")


def main():
    print("You must target the desired environment and deployment with 'bosh' CLI.")

    print("Fetching deployed manifest from BOSH.")
    manifest_yaml = subprocess.run(
        ["bosh", "manifest"],
        stdout=subprocess.PIPE,
        text=True
    ).stdout
    manifest = yaml.safe_load(manifest_yaml)
    instance_groups = manifest.get("instance_groups")
    relevant_igs = [
            instance_group for instance_group in instance_groups
            if (
                instance_group.get("instances") > 0
                and instance_group.get("lifecycle") != "errand"
            )]
    ig_to_scale = {
        instance_group.get("name"):
            Scale(instances=instance_group.get("instances"), type=instance_group.get("vm_type"))
            for instance_group in relevant_igs
    }

    print("Fetching CPU data from BOSH (this may take some time).")
    instance_cpu_data = {
        instance_group.get("name"):
            _get_cpu_data(instance_group)
            for instance_group in relevant_igs}

    print("Collating data...")
    row_template = "{:<25}{:<15}{:<30}{:<10}{:<10}"
    headers = ["VM", "Instances", "VM Type", "vCPUs", "Cores"]
    print(f"\n{row_template.format(*headers)}")
    print(f"{row_template.format(*(['---'] * len(headers)))}")
    for name, scale in ig_to_scale.items():
        cpu_info = instance_cpu_data.get(name)
        vcpu_count = cpu_info.vcpus * scale.instances
        core_count = cpu_info.cores * scale.instances
        print(row_template.format(
            name,
            scale.instances,
            scale.type,
            vcpu_count,
            core_count
        ))


def _bosh_ssh(ig_name: str, command: str) -> str:
    return subprocess.run(
        ["bosh", "ssh", f"{ig_name}/0", "-c", command, "-r", "--json"],
        stdout=subprocess.PIPE,
        text=True
    ).stdout


def _get_cpu_data(instance_group: dict) -> CPUData:
    print(f"Fetching CPU data for {instance_group.get('name')}.")
    if ("windows" in instance_group.get("stemcell")):
        bosh_output = _bosh_ssh(
            instance_group.get("name"),
            "wmic cpu get NumberOfCores,NumberOfLogicalProcessors /format:list"
        )
        wmic_output = json.loads(bosh_output).get("Tables")[0].get("Rows")[0].get("stdout")
        cpu_data = _parse_cpu_data(wmic_output, "=")
        return CPUData(
            cores=int(cpu_data.get("NumberOfCores")),
            vcpus=int(cpu_data.get("NumberOfLogicalProcessors")),
        )
    else:
        bosh_output = _bosh_ssh(
            instance_group.get("name"),
            "lscpu"
        )
        lscpu_output = json.loads(bosh_output).get("Tables")[0].get("Rows")[0].get("stdout")
        cpu_data = _parse_cpu_data(lscpu_output, ":")
        return CPUData(
            cores=int(cpu_data.get("Core(s) per socket")),
            vcpus=int(cpu_data.get("CPU(s)")),
        )


# Source: https://stackoverflow.com/questions/14693701
ansi_escape = re.compile(r'''
    \x1B  # ESC
    (?:   # 7-bit C1 Fe (except CSI)
        [@-Z\\-_]
    |     # or [ for CSI, followed by a control sequence
        \[
        [0-?]*  # Parameter bytes
        [ -/]*  # Intermediate bytes
        [@-~]   # Final byte
    )
''', re.VERBOSE)


def _parse_cpu_data(stdout: str, delimiter: str) -> dict:
    lines = stdout.split("\r\n")
    cleaned_lines = [ansi_escape.sub('', line) for line in lines]
    split_lines = [
        [part.strip() for part in line.split(delimiter)]
        for line in cleaned_lines
        if len(line) > 0
    ]
    return {line[0]: line[1] for line in split_lines if len(line) == 2}


if __name__ == "__main__":
    main()
