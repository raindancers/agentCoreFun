import * as path from 'path';
import * as core from 'aws-cdk-lib';
import { aws_secretsmanager as sm } from 'aws-cdk-lib';
import * as constructs from 'constructs';
import {
  agentCore,
} from 'raindancers-cdk';

export interface WeatherOnMarsProps extends core.StackProps {
  name: string;
}

export class WeatherOnMars extends core.Stack {

  constructor(scope: constructs.Construct, id: string, props: WeatherOnMarsProps) {
    super(scope, id, props);


    // Create the AgentCore OpenAPI gateway for Mars weather
    const marsWeatherGateway = new agentCore.AgentCoreOpenAPI(this, 'MarsWeatherGateway', {
      name: props.name,
      pathToOpenApiSpec: path.resolve(__dirname, '../../nasa/openApiSpec/nasaapi.json'),
      apiKey: {
        secret: sm.Secret.fromSecretCompleteArn(this, 'NasaApiSecret', 'arn:aws:secretsmanager:ap-southeast-2:366197773329:secret:apiKeys-nASpHB'),
        key: 'nasa',
      },
      gatewayDescription: 'Mars Weather API Gateway using NASA InSight data',
    });

    //Output important values
    new core.CfnOutput(this, 'GatewayUrl', {
      value: marsWeatherGateway.gatewayUrl,
      description: 'Mars Weather Gateway URL',
    });

    new core.CfnOutput(this, 'UserPoolId', {
      value: marsWeatherGateway.userPoolId,
      description: 'Cognito User Pool ID',
    });

    new core.CfnOutput(this, 'UserPoolClientId', {
      value: marsWeatherGateway.userPoolClientId,
      description: 'Cognito User Pool Client ID',
    });

    new core.CfnOutput(this, 'CognitoDomain', {
      value: props.name.replace('_', '').toLowerCase(),
      description: 'Cognito Domain Name',
    });

    new core.CfnOutput(this, 'TargetName', {
      value: `${props.name}Target`,
      description: 'Gateway Target Name',
    });

    new core.CfnOutput(this, 'ScopeString', {
      value: `${props.name}-gateway-id/gateway:read ${props.name}-gateway-id/gateway:write`,
      description: 'OAuth Scope String',
    });
  }
}
