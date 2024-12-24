# how-to-agent

Before running on local, fill the `.env` file with your `yubikey` and production `iaf_token`. 
On krylov leave yubikey part empty.


### 1.  Create a New Conda Environment (Optional)
```
conda create --name how_to_agent python=3.10
conda activate how_to_agent
```

### 2.  Install Packages in the Conda Environment (for development)
```
pip install -r requirements-dev.txt
```

### 3.  Start the application
```
streamlit run demos/demo_v0/main_app.py --server.runOnSave true
```

**Note: Never commit `.env` file with your key and token.**

To make git ignore it.
```
git update-index --assume-unchanged .env
```

## Updating image
### 1. Login to docker
```
docker login hub.tess.io
```

### 2. Build image
```
./build_image.sh
```

## Deploy demo to Tess

### 1. Update the Image Version
Update the image version in `demo/deployment/federated-deployment.yaml`. For example, change:

```yaml
image: "hub.tess.io/rapid_inov/how-to-agent-streamlit:20241121123533"
```

to:

```yaml
image: "hub.tess.io/rapid_inov/how-to-agent-streamlit:20241122153642"
```

### 2. Deploy the New Demo
Navigate to the deployment directory and apply the changes:

```sh
cd demo/deployment
tess kubectl --context=fcp-dev apply -f federated-deployment.yaml
```

### 3. Check Deployment Status
You can check the deployment status at [cloud.ebay.com](https://cloud.ebay.com/object/detail/FederatedDeployment:howtoagent:fcp:coreaipx-dev).

### 4. Access the Demo
[How-to-agent](https://howtoagent-coreaipx.qa.ebay.com)


## Running PyKrylov tasks
Run from the root directory of the project.
Index building task (modify the config-index-builder.yaml file to change the parameters):
```
export PYTHONPATH=$PYTHONPATH:<YOUR_REPO_PATH>/how-to-agent/src
python src/pykrylov_jobs/pykrylov_main.py --task index_builder --config-path src/pykrylov_jobs/configs/config-index-builder.yaml --project-name how-to-agent 
```