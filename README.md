# Virgil

Script for getting Cores from TAS foundations. Not intended for production use.

Named after the train/drill thing from _The Core (2003)_.

Inspired by https://cloud.google.com/compute/docs/instances/set-threads-per-core#view_the_number_of_threads_per_core

## Instructions

1. Install `python3` and `pip3` (should come with most Operating Systems)
1. Install the [`bosh`](https://bosh.io/docs/cli-v2-install/) CLI.
1. `pip3 install -r requirements.txt` (ideally we wouldn't need this step, so it would work in internetless environments) 
1. Target the desired environment and deployment with `bosh`.
1. `./virgil.py`

## Current (Known) Limitations

1. ~Only works on Linux stemcells~
1. ~Doesn't work for Isolation Segments~
1. Unvalidated for all IaaSs and configurations (e.g. vSphere Distributed Resource Scheduler)
