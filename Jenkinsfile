pipeline {
    agent any

    options {
        skipDefaultCheckout(true)
        disableConcurrentBuilds()
        timeout(time: 15, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10', artifactNumToKeepStr: '5'))
        timestamps()
    }

    triggers {
        pollSCM('H/2 * * * *')
    }

    environment {
        PYTHON_PATH = '/opt/homebrew/bin/python3'
        PIP_DISABLE_PIP_VERSION_CHECK = '1'
        PYTHONUNBUFFERED = '1'
    }

    stages {
        stage('Verify Environment') {
            steps {
                sh '"$PYTHON_PATH" --version && git --version && uname -sm'
            }
        }
        stage('Checkout') {
            steps {
                checkout scm
                sh 'git rev-parse HEAD'
            }
        }
        stage('Install Dependencies') {
            steps {
                sh '''
                    "$PYTHON_PATH" -m venv .venv
                    .venv/bin/python -m pip install -r requirements.txt
                '''
            }
        }
        stage('Lint') {
            steps {
                sh '.venv/bin/python -m flake8 app.py tests/ scripts/'
            }
        }
        stage('Test') {
            steps {
                sh '''
                    mkdir -p reports
                    .venv/bin/python -m pytest tests/ -v \
                        --junitxml=reports/junit.xml \
                        --cov=app --cov-branch --cov-fail-under=90 \
                        --cov-report=term-missing --cov-report=html --cov-report=xml
                '''
            }
            post {
                always {
                    junit testResults: 'reports/junit.xml', allowEmptyResults: true
                    publishHTML(target: [
                        allowMissing: true,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'htmlcov',
                        reportFiles: 'index.html',
                        reportName: 'Coverage Report'
                    ])
                }
            }
        }
        stage('Build') {
            steps {
                sh '.venv/bin/python -m PyInstaller --clean --noconfirm --onefile --name jenkins-flask-app app.py'
                archiveArtifacts artifacts: 'dist/jenkins-flask-app,coverage.xml,reports/junit.xml', fingerprint: true
            }
        }
        stage('Deploy') {
            steps {
                sh '.venv/bin/python scripts/deploy.py'
            }
        }
    }
    post {
        success { echo 'CI/CD pipeline completed successfully. App: http://localhost:5001/' }
        failure { echo 'CI/CD pipeline failed. Check stage output; deployment only follows passing checks.' }
    }
}
