pipeline {
    agent any

    options{
        checkoutToSubdirectory('vyos')
        disableConcurrentBuilds()
    }

    environment {
        INMANTA_MODULE_REPO='https://github.com/inmanta/'
        INMANTA_TEST_ENV="${env.WORKSPACE}/env"
    }

    triggers {
        pollSCM('* * * * *')
        cron("H H(2-5) * * *")
    }

    stages {
        stage('Test') {
            steps {
                sh 'rm -rf $INMANTA_TEST_ENV; python3 -m venv $INMANTA_TEST_ENV; $INMANTA_TEST_ENV/bin/python3 -m pip install -U  inmanta pytest-inmanta netaddr; $INMANTA_TEST_ENV/bin/python3 -m pip install -r vyos/requirements.txt'
                // fix for bug in pytest-inmanta where folder name is used as module name
                dir('vyos'){
                    lock('vyos_host') {
                        withCredentials([string(credentialsId: 'vyos_host', variable: 'VY_TEST_HOST')]) {
                            sh 'unset SSH_CLIENT && unset SSH_CONNECTION && $INMANTA_TEST_ENV/bin/python3 -m pytest --junitxml=junit.xml -vvv tests'
                        }
                    }
                }
            }
        }
        stage('Test_New') {
            steps {
                // fix for bug in pytest-inmanta where folder name is used as module name
                dir('vyos'){
                    lock('vyos_host_1.2') {
                        withCredentials([string(credentialsId: 'vyos_host_1.2', variable: 'VY_TEST_HOST')]) {
                            sh 'unset SSH_CLIENT && unset SSH_CONNECTION && $INMANTA_TEST_ENV/bin/python3 -m pytest --junitxml=junit_new.xml -vvv tests'
                        }
                    }
                }
            }
        }
    }

    post {
        always {
            junit 'vyos/junit.xml'
            junit 'vyos/junit_new.xml'
        }
    }
}
