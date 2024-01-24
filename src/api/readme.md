### steps to build image and push image to artfiact registry
cd project_home

##### on a linux machine this should work, the remaining steps are based on my setup on an M1 mac but they should be platform agnostic
docker build -t cloud-run-python-api .

#### if you on an ARM based mac (M1, M2 etc), image has to be built with the platform linux/amd64 flag for cloud run to run successfully
docker buildx build --platform linux/amd64 -t cloud-run-python-api-linux-amd64 .

gcloud auth configure-docker [LOCATION]-docker.pkg.dev

docker tag cloud-run-python-api-linux-amd64 [LOCATION]-docker.pkg.dev/[PROJECT_ID]/[REPO_NAME]/cloud-run-python-api-linux-amd64

docker push [LOCATION]-docker.pkg.dev/[PROJECT_ID]/[REPO_NAME]/cloud-run-python-api-linux-amd64
