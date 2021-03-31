#! /bin/bash

mkdir master_gold_dir
mkdir tmp
cd master_gold_dir
git clone https://github.com/cloud-bulldozer/cerberus.git
echo $PWD
cd cerberus
./CI/tests/test_daemon_disabled.sh
mv time_tracker.json master_time_tracker.json
mv master_time_tracker.json ../../tmp
cd ../..
rm -rf master_gold_dir
