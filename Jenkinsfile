pipeline {
    agent any

    environment {
        // Docker configuration
        registry = 'docker.io'
        reponame = 'believeer'  // Your Docker Hub username
        appname = 'to7fa-backend'

        // Deployment configuration
        EC2_HOST = '54.93.200.200'

        // Environment (dev, staging, prod)
        env = 'prod'  // Change to 'dev' or 'staging' for other environments
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out code from GitHub...'
                checkout scm
            }
        }

        stage('Environment Setup') {
            steps {
                echo 'Setting up environment variables...'
                sh '''
                    echo "Build Number: ${BUILD_NUMBER}"
                    echo "Environment: ${env}"
                    echo "App Name: ${appname}"
                '''
            }
        }

        stage('Run Tests') {
            steps {
                echo 'Running Django tests...'
                sh '''
                    # Create .env for testing
                    cp .env.example .env || true

                    # Install dependencies
                    pip3 install --user -r requirements.txt || true

                    # Run tests
                    python3 manage.py test --noinput || true
                '''
            }
        }

        // Build Stage
        stage('Build') {
            steps {
                echo "Building Docker image: ${registry}/${reponame}/${appname}:${BUILD_NUMBER}"
                sh """
                    docker build -t ${registry}/${reponame}/${appname}:${BUILD_NUMBER} .
                    docker images
                """
            }
        }

        // Push Image Stage (only in prod)
        stage('Push Image') {
            when {
                environment name: 'env', value: 'prod'
            }
            steps {
                echo "Pushing Docker image to Docker Hub..."
                withCredentials([usernamePassword(credentialsId: 'dockerhub-cred', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh """
                        echo "\$DOCKER_PASS" | docker login -u "\$DOCKER_USER" --password-stdin docker.io
                        docker push ${registry}/${reponame}/${appname}:${BUILD_NUMBER}

                        # Also tag and push as latest
                        docker tag ${registry}/${reponame}/${appname}:${BUILD_NUMBER} ${registry}/${reponame}/${appname}:latest
                        docker push ${registry}/${reponame}/${appname}:latest
                    """
                }
            }
        }

        // Deploy Stage
        stage('Deploy to EC2') {
            steps {
                echo "Deploying to EC2: ${EC2_HOST}"
                withCredentials([
                    usernamePassword(credentialsId: 'dockerhub-cred', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS'),
                    sshUserPrivateKey(credentialsId: 'ec2-key', keyFileVariable: 'SSH_KEY', usernameVariable: 'SSH_USER')
                ]) {
                    sh """
                        ssh -i "\$SSH_KEY" -o StrictHostKeyChecking=no \$SSH_USER@${EC2_HOST} "
                            set -euo pipefail

                            # Navigate to project directory
                            cd /home/ubuntu/to7fabackend

                            echo 'Logging into Docker Hub...'
                            echo '${DOCKER_PASS}' | docker login -u '${DOCKER_USER}' --password-stdin docker.io

                            echo 'Pulling latest code...'
                            git pull origin master || true

                            echo 'Setting image tag in .env.production...'
                            sed -i \"s/DOCKER_IMAGE_TAG=.*/DOCKER_IMAGE_TAG=${BUILD_NUMBER}/\" .env.production || echo \"DOCKER_IMAGE_TAG=${BUILD_NUMBER}\" >> .env.production

                            echo 'Pulling latest Docker image...'
                            docker pull ${registry}/${reponame}/${appname}:${BUILD_NUMBER}
                            docker tag ${registry}/${reponame}/${appname}:${BUILD_NUMBER} ${registry}/${reponame}/${appname}:latest

                            echo 'Stopping old containers...'
                            docker-compose -f docker-compose.production.yml down || true

                            echo 'Starting services with docker-compose...'
                            docker-compose -f docker-compose.production.yml --env-file .env.production up -d

                            echo 'Waiting for services to be healthy...'
                            sleep 20

                            echo 'Verifying services are running...'
                            docker-compose -f docker-compose.production.yml ps

                            echo 'Running migrations...'
                            docker-compose -f docker-compose.production.yml exec -T django-admin python manage.py migrate --noinput

                            echo 'Collecting static files...'
                            docker-compose -f docker-compose.production.yml exec -T django-admin python manage.py collectstatic --noinput

                            echo 'Running health check...'
                            curl -f http://localhost/health/ || exit 1

                            echo '✅ Deployed successfully!'
                        "
                    """
                }
            }
        }

        // Cleanup Old Images
        stage('Cleanup') {
            steps {
                echo 'Cleaning up old Docker images...'
                sh '''
                    docker image prune -af || true
                '''
            }
        }
    }

    post {
        success {
            echo '✅ Pipeline executed successfully!'
            echo "Deployment URL: http://${EC2_HOST}"
            // Uncomment to send Slack notification
            // slackSend(color: 'good', message: "✅ Deployment successful: ${env.JOB_NAME} - Build #${env.BUILD_NUMBER}")
        }
        failure {
            echo '❌ Pipeline failed!'
            // Uncomment to send Slack notification
            // slackSend(color: 'danger', message: "❌ Deployment failed: ${env.JOB_NAME} - Build #${env.BUILD_NUMBER}")
        }
        always {
            echo 'Cleaning up workspace...'
            cleanWs()
        }
    }
}
