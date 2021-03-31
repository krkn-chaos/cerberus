set -xeEo pipefail

source CI/tests/common.sh

trap error ERR
trap finish EXIT

function funtional_test_daemon_disabled {
    sed -i '/^\([[:space:]]*iterations: *\).*/s//\15/;/^\([[:space:]]*sleep_time: *\).*/s//\12/;/^\([[:space:]]*daemon_mode: *\).*/s//\1False/;' config/config.yaml
    python3 start_cerberus.py -c config/config.yaml
    echo "${test_name} test: Success"
}

funtional_test_daemon_disabled
