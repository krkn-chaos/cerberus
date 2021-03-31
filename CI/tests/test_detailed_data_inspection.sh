set -xeEo pipefail

source CI/tests/common.sh

trap error ERR
trap finish EXIT

function funtional_test_detailed_data_inspection {
    if [[ `oc get ns test-namespace` ]]; then
        oc delete ns test-namespace
    fi
    oc create ns test-namespace
    sed -i '/watch_namespaces:/,/cerberus_publish_status/{//!d}; /watch_namespaces:/a\        -    test-namespace\' config/config.yaml
    sed -i '/^\([[:space:]]*iterations: *\).*/s//\110/;/^\([[:space:]]*sleep_time: *\).*/s//\12/;/^\([[:space:]]*daemon_mode: *\).*/s//\1False/;/^\([[:space:]]*inspect_components: *\).*/s//\1True/;' config/config.yaml
    export -f create_and_delete_pod
    parallel ::: "python3 start_cerberus.py -c config/config.yaml" create_and_delete_pod
    oc delete ns test-namespace
    if [[ ! -d "inspect_data/test-namespace-logs" ]]
    then
        echo "${test_name} test: Fail"
        exit 1
    else
        echo "${test_name} test: Success"
    fi
}

funtional_test_detailed_data_inspection
