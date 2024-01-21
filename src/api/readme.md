### steps to build image and push image to artfiact registry
cd  project_home
docker build -t cloud-run-python-api .

gcloud auth configure-docker us-central1-docker.pkg.dev

docker tag cloud-run-python-api-linux-amd64 us-central1-docker.pkg.dev/gcp-demo-telemetry/jhbjhbjbkjn/cloud-run-python-api-linux-amd64
docker push us-central1-docker.pkg.dev/gcp-demo-telemetry/jhbjhbjbkjn/cloud-run-python-api-linux-amd64