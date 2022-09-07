# Virgil

Script for getting Cores from TAS foundations. Not intended for production use.

Named after the train/drill thing from _The Core (2003)_.

## Instructions

1. Install the [`bosh`](https://bosh.io/docs/cli-v2-install/) and [`om`](https://github.com/pivotal-cf/om) CLIs.
1. Target the desired environment with both `bosh` and `om`.
1. `./virgil.py`

## Current (Known) Limitations

1. Only works on Linux stemcells
1. Doesn't work for Isolation Segments
1. Unvalidated for all IaaSs and configurations (e.g. vSphere Distributed Resource Scheduler)
