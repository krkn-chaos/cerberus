# Building your own Cerberus image

1. Git clone the Cerberus repository using `git clone https://github.com/cloud-bulldozer/cerberus.git`.
2. Modify the python code and yaml files to address your needs.
3. Execute `podman build -t <new_image_name>:latest .` in the containers directory within cerberus to build an image from a Dockerfile.
4. Execute `podman run --detach --name <container_name> <new_image_name>:latest` to start a container based on your new image.

# Building the Cerberus image on IBM Power (ppc64le arch)

1. Git clone the Cerberus repository using `git clone https://github.com/cloud-bulldozer/cerberus.git` on an IBM Power Systems server.
2. Modify the python code and yaml files to address your needs.
3. Execute `podman build -t <new_image_name>:latest -f Dockerfile-ppc64le` in the containers directory within cerberus to build an image from the Dockerfile for Power.
4. Execute `podman run --detach --name <container_name> <new_image_name>:latest` to start a container based on your new image.

# Running in a docker network with Kraken
Its possible to run within a docker network, where you have appropriate configured your config so that each individual tool is working correctly for your cluster, here are examples of how you achieve this:

`docker run -d -e LANG="en_US.UTF-8"  \
    -v "$(pwd)/config/cerberus/default_config.yml":/root/cerberus/config/config.yaml \
    -v "$KUBE_TMP":/root/.kube/config \
    --health-cmd "curl http://127.0.0.1:8080" \
    --health-interval 10s \
    --health-timeout 5s \
    --entrypoint python3 \
    --network "$CHAOS_NETWORK" \
    --name "$CERBERUS_CONTAINER" \
    quay.io/openshift-scale/cerberus:latest \
    start_cerberus.py -c config/config.yaml`

`docker build -t "$KRAKEN_CONTAINER-runner":latest -f "$(pwd)/docker/kraken/Dockerfile" .`
\
The Dockerfile includes setuptools: \
`FROM quay.io/openshift-scale/kraken
 RUN pip3 install -U setuptools`
    
`docker run -d -v "$config":/root/kraken/config/config.yaml \
    -v "$(pwd)/scenarios":/scenarios \
    -v "$KUBE_TMP":/root/.kube/config \
    --name "$KRAKEN_CONTAINER" \
    --network "$CHAOS_NETWORK" \
    --entrypoint python3 \
    "$KRAKEN_CONTAINER":latest \
    run_kraken.py -c config/config.yaml`

## Troubleshooting 

If you encounter encoding issues when running the containerized version such as:

`ERROR:root:'ascii' codec can't decode byte 0xc2 in position 838243: ordinal not in range(128)`

it is possible to overcome by specifying the locale for encoding by adding a parameter to your step 4 above:

Execute `podman run --detach -e LANG="en_US.UTF-8" --name <container_name> <new_image_name>:latest`
