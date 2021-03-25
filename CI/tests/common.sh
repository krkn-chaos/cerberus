ERRORED=false

function finish {
    if [ $? -eq 1 ] && [ $ERRORED != "true" ]
    then
        error
    fi
}

function error {
    echo "Error caught."
    ERRORED=true
}

function create_and_delete_pod {
    for ((i=1;i<5;i++));
    do
        oc apply -f CI/tests/test-configs/hello_openshift_pod.yaml -n test-namespace
        kubectl wait --for=condition=Ready pod/hello-pod -n test-namespace
        sleep 2s
        oc delete pods hello-pod -n test-namespace 
    done
}
