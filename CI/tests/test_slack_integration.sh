set -xeEo pipefail

source CI/tests/common.sh

trap error ERR
trap finish EXIT

function funtional_test_slack_integration {
    if [[ `oc get ns test-namespace` ]]; then
        oc delete ns test-namespace
    fi
    oc create ns test-namespace
    sed -i '/watch_namespaces:/a\        -    test-namespace\' config/config.yaml
    sed -i '/^\([[:space:]]*iterations: *\).*/s//\110/;/^\([[:space:]]*sleep_time: *\).*/s//\12/;/^\([[:space:]]*daemon_mode: *\).*/s//\1False/;' config/config.yaml
    day=$( date '+%A' )
    sed -i '/^\([[:space:]]*slack_integration: *\).*/s//\1True/;/^\([[:space:]]*'$day': *\).*/s//\1 AAAAAAAAA/;' config/config.yaml
    export -f create_and_delete_pod
    parallel ::: "python3 start_cerberus.py -c config/config.yaml" create_and_delete_pod
    oc delete ns test-namespace
    echo "${test_name} test: Success"
}

funtional_test_slack_integration
