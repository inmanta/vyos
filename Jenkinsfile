pipeline {
    agent any

    options{
        checkoutToSubdirectory('vyos')
        disableConcurrentBuilds()
    }

    environment {
        VY_TEST_HOST=credentials('vyos_host')
        INMANTA_MODULE_REPO='https://github.com/inmanta/'
        INMANTA_TEST_ENV="${env.WORKSPACE}/env"
    } 

    stages {
        stage('Test') {
            steps {
                sh 'rm -rf $INMANTA_TEST_ENV; python3 -m venv $INMANTA_TEST_ENV; $INMANTA_TEST_ENV/bin/python3 -m pip install -U  inmanta pytest-inmanta netaddr; $INMANTA_TEST_ENV/bin/python3 -m pip install -r vyos/requirements.txt'
                // fix for bug in pytest-inmanta where folder name is used as module name
                dir('vyos'){
                    sh 'unset SSH_CLIENT && $INMANTA_TEST_ENV/bin/python3 -m pytest --junitxml=junit.xml -vvv tests'
                }
            }
        }
    }

    post {
        always {
            junit 'vyos/junit.xml'
        }
    }
}
