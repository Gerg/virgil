#!/usr/bin/env python3

import json
import subprocess

from collections import namedtuple

Scale = namedtuple("Scale", "instances type")


def main():
    print("You must target the desired environment with 'bosh' and 'om' CLIs.")

    print("Fetching deployed products from OM.")
    products = _om_curl("/api/v0/deployed/products")
    cf_product_guid = next((
        product.get("guid")
        for product in products
        if product.get("type") == "cf"
    ))

    print(f"Fetching deployed manifest for {cf_product_guid} from OM.")
    manifest = _om_curl(f"/api/v0/deployed/products/{cf_product_guid}/manifest")
    instance_groups = manifest.get("instance_groups")
    ig_to_scale = {
        instance_group.get("name"):
            Scale(instance_group.get("instances"), instance_group.get("vm_type"))
            for instance_group in instance_groups
            if instance_group.get("instances") > 0
    }

    print("Fetching CPU data from BOSH.")
    lscpu_output = _bosh_ssh("lscpu")
    cpu_infos = {
        instance.get("instance").split("/")[0]:
            _parse_cpu_data(instance.get("stdout"))
            for instance in json.loads(lscpu_output).get("Tables")[0].get("Rows")
    }

    print("Collating data...")
    row_template = "{:<20}{:<15}{:<30}{:<10}{:<10}"
    headers = ["VM", "Instances", "VM Type", "vCPUs", "Cores"]
    print(f"\n{row_template.format(*headers)}")
    print(f"{row_template.format(*(['---'] * len(headers)))}")
    for name, scale in ig_to_scale.items():
        cpu_info = cpu_infos.get(name)
        vcpu_count = cpu_info.get("CPU(s)") * scale.instances
        core_count = cpu_info.get("Core(s) per socket") * scale.instances
        print(row_template.format(
            name,
            scale.instances,
            scale.type,
            vcpu_count,
            core_count
        ))


def _om_curl(path: str) -> dict:
    response_json = subprocess.run(
        ["om", "curl", "-s", "-p", path],
        stdout=subprocess.PIPE,
        text=True
    ).stdout
    return json.loads(response_json)


def _bosh_ssh(command: str) -> str:
    return subprocess.run(
        ["bosh", "ssh", "-c", command, "-r", "--json"],
        stdout=subprocess.PIPE,
        text=True
    ).stdout


def _parse_cpu_data(stdout: str) -> dict:
    lines = stdout.split("\r\n")
    split_lines = (
        [part.strip() for part in line.split(":")]
        for line in lines
        if len(line) > 0
    )
    return {line[0]: line[1] for line in split_lines}


if __name__ == "__main__":
    main()
