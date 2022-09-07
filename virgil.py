#!/usr/bin/env python3

import json
import subprocess

from collections import namedtuple

Scale = namedtuple("Scale", "instances type")


def main():
    print("You must target the desired environment with 'bosh' and 'om' CLIs.")

    print("Fetching VM types from OM.")
    vm_types = _om_curl("/api/v0/vm_types")
    type_to_vcpu = {
        vm_type.get("name"):
            vm_type.get("cpu")
            for vm_type in vm_types.get("vm_types")
    }

    print("Fetching products from OM.")
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
    core_command = "lscpu | grep 'Thread(s) per core' | cut -d ':' -f 2 | tr -d ' '"
    bosh_output = subprocess.run(
        ["bosh", "ssh", "-c", core_command, "-r", "--json"],
        stdout=subprocess.PIPE,
        text=True
    ).stdout
    core_ratios = {
        instance.get("instance").split("/")[0]:
            int(instance.get("stdout"))
            for instance in json.loads(bosh_output).get("Tables")[0].get("Rows")
    }

    print("Collating data...")
    row_template = "{:<20}{:<15}{:<30}{:<10}{:<10}"
    headers = ["VM", "Instances", "Type", "vCPUs", "Cores"]
    print(f"\n{row_template.format(*headers)}")
    for name, scale in ig_to_scale.items():
        vcpu_count = type_to_vcpu.get(scale.type) * scale.instances
        vcpu_multiplier = core_ratios.get(name)
        print(row_template.format(
            name,
            scale.instances,
            scale.type,
            vcpu_count,
            vcpu_count/vcpu_multiplier
        ))


def _om_curl(path: str) -> dict:
    response_json = subprocess.run(
        ["om", "curl", "-s", "-p", path],
        stdout=subprocess.PIPE,
        text=True
    ).stdout
    return json.loads(response_json)


if __name__ == "__main__":
    main()
