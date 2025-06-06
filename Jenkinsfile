import groovy.json.JsonSlurperClassic

def reqMap = [
  'all': [ zip: 'lambda_package.zip', exclude: ''],
  'core': [ zip: 'core.zip', exclude: '"**/numpy*" "**/panda*"' ],
  'uscis': [ zip: 'uscis.zip', exclude: '"**/six*" "**/urllib3*" "**/numpy*" "**/panda*"']
]

def layers = ['arn:aws:lambda:us-east-1:336392948345:layer:AWSSDKPandas-Python39:29']

pipeline {
  agent {
    label 'CRIS_BUILD_187'
  }
  environment {
    FUNCTION_NAME = 'ops-api-lambda-function-devTest'
    REGION = 'us-east-1'
    ZIP_FILE = 'lambda_package.zip'
    ARN_FILE = 'lambda_arn.txt'
  }
  parameters {
    string defaultValue: 'develop', description: 'Select git branch', name: 'GIT_BRANCH', trim: true
  }
  stages {
      stage('Clone Repository') {
          steps {
             cleanWs()
             checkout([$class: 'GitSCM',
                 branches: [[name: "*/develop"]], 
                 userRemoteConfigs: [[ 
                   url: 'https://git.uscis.dhs.gov/USCIS/cris-OPTS-ETL.git',   
                   credentialsId: 'github-service-act-token'
              ]]
            ])
         }
      } 
      stage('Install Requirements') {
        steps {
          dir(env.WORKSPACE){
            script {
            ['core'].each { layer ->
              sh """
              echo "INFO: Current directory: ${env.WORKSPACE}"
              echo "INFO: Installing Python3 dependencies from requirements-${layer}.txt..."
              python3.9 -m venv venv
              . venv/bin/activate
              pip3.9 install --upgrade pip
              pip3.9 install -r requirements-${layer}.txt -t ./${layer} --no-deps
              """
            }
            }
          }
        }
      }
      stage('Prepare') {
          steps {
            withCredentials([[
                  $class: 'AmazonWebServicesCredentialsBinding',
                  credentialsId: 'aws-nonprod-accesskey',
                  accessKeyVariable: 'AWS_ACCESS_KEY_ID',
                  secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'
              ]]) {
                script {
                  
                  ['core'].each { layer ->
                    println "INFO: Zipping and publishing all required files for Lambda layer ${layer} to ${reqMap[layer].zip}..."
                    sh """
                      mkdir -p python/lib/python3.9/
                      mv ${layer} python/lib/python3.9/site-packages
                      zip -r ${reqMap[layer].zip} python -x "**/_pycache_/" ".pyc" ".git/" "*/README.md" "**/Jenkinsfile" "logs/*" "test/*" ${reqMap[layer].exclude}
                      mv python/lib/python3.9/site-packages ${layer}
                      find ./${layer}
                    """
                    stdOut = sh(returnStdout: true, script: """
                      aws lambda publish-layer-version \
                        --layer-name ${layer} \
                        --zip-file fileb://${reqMap[layer].zip} \
                        --compatible-runtimes python3.9 || true
                    """).trim()
                    def layerArn = new JsonSlurperClassic().parseText(stdOut).LayerVersionArn
                    layers += layerArn
                  }
                  sh '''
                    echo "INFO: Waiting for Lambda function configuration update to complete..."
                    while true; do
                      STATUS=$(aws lambda get-function-configuration \
                        --function-name $FUNCTION_NAME \
                        --region $REGION \
                        --query 'State' --output text)
                      echo "Current status: $STATUS"
                      if [ "$STATUS" = "Active" ]; then
                        break
                      fi
                      sleep 5
                    done
                  '''
                  println "INFO: Updated layers ARNs: \"${layers.join('", "')}\""
                  sh """
                    pwd
                    echo "INFO: Zipping and publishing all required files for Lambda function..."
                    zip -r lambda_package.zip config src
                    
                    echo "INFO: Updating lambda config to use layers (should be updated so layer versions are based off output of previous step"
                    aws lambda update-function-configuration --function-name ops-api-lambda-function-devTest \
                      --layers ${layers.join(' ')} || true
                  """
                  sh '''
                    echo "INFO: Waiting for Lambda function configuration update to complete..."
                    while true; do
                      STATUS=$(aws lambda get-function-configuration \
                        --function-name $FUNCTION_NAME \
                        --region $REGION \
                        --query 'State' --output text)
                      echo "Current status: $STATUS"
                      if [ "$STATUS" = "Active" ]; then
                        break
                      fi
                      sleep 5
                    done
                  '''
                }
            }
          }
      }

      stage('Deploy Lambda') {
          steps {
              withCredentials([[
                  $class: 'AmazonWebServicesCredentialsBinding',
                  credentialsId: 'aws-nonprod-accesskey',
                  accessKeyVariable: 'AWS_ACCESS_KEY_ID',
                  secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'
              ]]) {
                  sh '''
                      echo "Creating Lambda function with ${ZIP_FILE}..."
                      aws lambda create-function \
                        --function-name $FUNCTION_NAME \
                        --runtime python3.9 \
                        --role arn:aws:iam::297322678787:role/ops-api-lambda-access-role \
                        --handler lambda_handler.lambda_handler \
                        --zip-file fileb://$ZIP_FILE \
                        --region $REGION || true

                      echo "Waiting for Lambda function to become Active..."
                      while true; do
                          STATUS=$(aws lambda get-function-configuration \
                              --function-name $FUNCTION_NAME \
                              --region $REGION \
                              --query 'State' --output text)
                          echo "Current status: $STATUS"
                          if [ "$STATUS" = "Active" ]; then
                              break
                          fi
                          sleep 5
                      done
                      
                      echo "Waiting for Lambda function update status to be successful..."
                      while true; do
                          STATUS=$(aws lambda get-function-configuration \
                              --function-name $FUNCTION_NAME \
                              --region $REGION \
                              --query 'LastUpdateStatus' --output text)
                          echo "Current status: $STATUS"
                          if [ "$STATUS" = "Successful" ]; then
                              break
                          fi
                          sleep 5
                      done
                        
                      echo "Updating function code..."
                      aws lambda update-function-code \
                          --function-name $FUNCTION_NAME \
                          --zip-file fileb://$ZIP_FILE \
                          --region $REGION

                      echo "Getting Lambda ARN..."
                      aws lambda get-function \
                          --function-name $FUNCTION_NAME \
                          --region $REGION \
                          --query 'Configuration.FunctionArn' \
                          --output text > $ARN_FILE
                  '''
              }
          }
      }

      stage('Setup CloudWatch Schedule') {
          steps {
              withCredentials([[
                  $class: 'AmazonWebServicesCredentialsBinding',
                  credentialsId: 'aws-nonprod-accesskey',
                  accessKeyVariable: 'AWS_ACCESS_KEY_ID',
                  secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'
              ]]) {
                  sh '''
                      LAMBDA_ARN=$(cat $ARN_FILE)

                      echo "Creating CloudWatch Events rule..."
                      aws events put-rule \
                          --schedule-expression "rate(15 minutes)" \
                          --name ops-api-devTest-schedule \
                          --region $REGION

                      echo "Adding permission for CloudWatch to invoke Lambda..."
                      aws lambda add-permission \
                          --function-name $FUNCTION_NAME \
                          --statement-id ops-api-devTest-event \
                          --action lambda:InvokeFunction \
                          --principal events.amazonaws.com \
                          --region $REGION || true

                      echo "Creating target for CloudWatch Events..."
                      aws events put-targets \
                          --rule ops-api-devTest-schedule \
                          --targets "Id"="1","Arn"="$LAMBDA_ARN" \
                          --region $REGION
                  '''
              }
          }
      }
  }
}
