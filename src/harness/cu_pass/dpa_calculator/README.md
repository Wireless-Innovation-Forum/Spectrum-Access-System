# DPA Calculator

## Docker
### Build
From the root directory, run
```shell
docker build . -f src/harness/cu_pass/dpa_calculator/Dockerfile -t dpa
```

### Run
Mount data directory volumes and use environment variables matching the container volume paths.

```shell
docker run \
  --env AWS_ACCESS_KEY_ID=<aws_access_key_id>
  --env AWS_SECRET_ACCESS_KEY=<aws_secret_access_key>
  --env AWS_DEFAULT_REGION=<aws_region>
  -v "<PATH_TO_LOCAL_COMMON_DATA>:/cu_pass/Common-Data" \
  dpa
```

## AWS
### Push docker image
#### Setup
- Ensure the [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) is installed.

#### Set AWS repository variable
- Mac/Linux
    ```shell
    export AWS_REPO=<aws_account_id>.dkr.ecr.<aws_region>.amazonaws.com
    export AWS_REGISTRY=$AWS_REPO/dpa_calculator:latest
    ```

- Windows
    ```shell
    set AWS_REPO <aws_account_id>.dkr.ecr.<aws_region>.amazonaws.com
    set AWS_REGISTRY $AWS_REPO/dpa_calculator:latest
    ```

#### ECR
- Login
    ```shell
    aws ecr get-login-password | docker login --username AWS --password-stdin "$AWS_REPO"
    ```
- Push
    ```shell
    docker tag dpa "$AWS_REGISTRY"
    docker push "$AWS_REGISTRY"
    ```

### EC2 Instance
1. Launch EC2 instance with 20 GB of memory
2. Attach Common-Data volume to instance
   1. [Format](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-using-volumes.html) the volume
       - Example
         ```shell
         sudo mkdir /Common-Data
         sudo mount /dev/xvdf /Common-Data
         ```
      
3. SSH into the instance
4. [Install](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/docker-basics.html) Docker
   ```shell
   sudo yum update -y
   sudo amazon-linux-extras install docker
   sudo yum install docker
   sudo service docker start
   sudo usermod -a -G docker ec2-user
   ```
5. Disconnect and SSH back into the instance
6. Setup AWS config
   ```shell
    aws config
    ```
7. Log in using the ECR login command above
8. Run the docker image with the command above and the image in the ECR repo
    ```shell
    docker run -it \
      --env AWS_ACCESS_KEY_ID=$(aws configure get aws_access_key_id) \
      --env AWS_SECRET_ACCESS_KEY=$(aws configure get aws_secret_access_key) \
      --env AWS_DEFAULT_REGION=$(aws configure get region) \
      -v "/Common-Data:/cu_pass/Common-Data" \
      <ecs_image>
    ```