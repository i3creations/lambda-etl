def reqMap = [
  'all': [ zip: 'lambda_package.zip', exclude: ''],
  'archer':[ zip: 'archer.zip', exclude: '"**/numpy*" "**/panda*"' ],
  'core': [ zip: 'core.zip', exclude: '' ],
  'uscis': [ zip: 'uscis.zip', exclude: '"**/six*" "**/urllib3*" "**/tzdata*" "**/numpy*" "**/panda*"']
]


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
            ['archer','core','uscis'].each { layer ->
              sh """
              echo "INFO: Current directory: ${env.WORKSPACE}"
              echo "INFO: Installing Python3 dependencies from requirements-${layer}.txt..."
              python3.9 -m venv venv
              . venv/bin/activate
              pip3.9 install --upgrade pip
              pip3.9 install -r requirements-${layer}.txt -t ./${layer} --upgrade
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
                  ['archer','core','uscis'].each { layer ->
                    sh """
                    echo "INFO: Zipping and publishing all required files for Lambda layer ${layer} to ${reqMap[layer].zip}..."
                    zip -r ${reqMap[layer].zip} ${layer} -x "**/_pycache_/" ".pyc" ".git/" "*/README.md" "**/Jenkinsfile" "logs/*" "test/*" ${reqMap[layer].exclude}
                    
                    aws lambda publish-layer-version \
                          --layer-name ${layer} \
                          --zip-file fileb://${reqMap[layer].zip} \
                          --compatible-runtimes python3.13 || true
                    """
                  }
                  
                  sh """
                    pwd
                    echo "INFO: Zipping and publishing all required files for Lambda function..."
                    zip -r lambda_package.zip config ops_api
                  """
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
                        --runtime python3.13 \
                        --role arn:aws:iam::297322678787:role/ops-api-lambda-access-role \
                        --handler ops_api.lambda_handler.lambda_handler \
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
