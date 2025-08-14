import os
import sys
import boto3
import utils
import requests
import time
from botocore.exceptions import ClientError
from pprint import pprint
from botocore.config import Config

# Use AWS profile 'sandpit' for credentials Modify as reuqired.
session = boto3.Session(profile_name='sandpit')
credentials = session.get_credentials()

os.environ['AWS_ACCESS_KEY_ID'] = credentials.access_key
os.environ['AWS_SECRET_ACCESS_KEY'] = credentials.secret_key

if credentials.token:
    os.environ['AWS_SESSION_TOKEN'] = credentials.token
os.environ['AWS_DEFAULT_REGION'] = session.region_name or 'ap-southeast-2'



# Values from CDK deployment outputs
user_pool_id = 'ap-southeast-2_9CyEjLY6o'

client_id = '1jug9sc007mo068dohvf57h0ah'
gatewayURL = 'https://nasamarsweathergateway-yg6am900xf.gateway.bedrock-agentcore.ap-southeast-2.amazonaws.com/mcp'
targetname = 'NasaMarsWeatherTarget'
REGION = 'ap-southeast-2'
scopeString = 'NasaMarsWeather-gateway-id/gateway:read NasaMarsWeather-gateway-id/gateway:write'

# Get client secret from Cognito
cognito_client = boto3.client('cognito-idp', region_name=REGION)
client_response = cognito_client.describe_user_pool_client(
    UserPoolId=user_pool_id,
    ClientId=client_id
)
client_secret = client_response['UserPoolClient']['ClientSecret']

# Use the correct domain for token request
domain = 'nasamarsweather'  # From CDK domain creation
token_url = f"https://{domain}.auth.{REGION}.amazoncognito.com/oauth2/token"

print("Requesting the access token from Amazon Cognito authorizer...")
headers = {"Content-Type": "application/x-www-form-urlencoded"}
data = {
    "grant_type": "client_credentials",
    "client_id": client_id,
    "client_secret": client_secret,
    "scope": scopeString,
}
response = requests.post(token_url, headers=headers, data=data)
token_response = response.json() if response.status_code == 200 else {"error": response.text}
print("Full token response:", token_response)

if "access_token" in token_response:
    token = token_response["access_token"]
    print("Token response:", token)
else:
    print("Error getting token:", token_response)
    sys.exit(1)



from strands.models import BedrockModel
from mcp.client.streamable_http import streamablehttp_client 
from strands.tools.mcp.mcp_client import MCPClient
from strands import Agent

def create_streamable_http_transport():
    return streamablehttp_client(gatewayURL,headers={"Authorization": f"Bearer {token}"})

client = MCPClient(create_streamable_http_transport)

## The IAM group/user/ configured in ~/.aws/credentials should have access to Bedrock model
yourmodel = BedrockModel(
    model_id="apac.anthropic.claude-sonnet-4-20250514-v1:0",
    temperature=0.7,
)


from strands import Agent
import logging


# Configure the root strands logger. Change it to DEBUG if you are debugging the issue.
logging.getLogger("strands").setLevel(logging.INFO)

# Add a handler to see the logs
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s", 
    handlers=[logging.StreamHandler()]
)

print('\n\n\n************** Talking to Mars API At Nasa *******************')


with client:
    # Call the listTools 
    tools = client.list_tools_sync()
    # Create an Agent with the model and tools
    agent = Agent(model=yourmodel,tools=tools) ## you can replace with any model you like
    print(f"Tools loaded in the agent are {agent.tool_names}")
    #print(f"Tools configuration in the agent are {agent.tool_config}")
    # Invoke the agent with the sample prompt. This will only invoke  MCP listTools and retrieve the list of tools the LLM has access to. The below does not actually call any tool.
    agent("Hi , can you list all tools available to you")
    agent("What is the weather in northern part of the mars")
    # Invoke the agent with sample prompt, invoke the tool and display the response
    #Call the MCP tool explicitly. The MCP Tool name and arguments must match with your AWS Lambda function or the OpenAPI/Smithy API
    result = client.call_tool_sync(
    tool_use_id="get-insight-weather-1", # You can replace this with unique identifier. 
    name=targetname+"___getInsightWeather", # This is the tool name based on AWS Lambda target types. This will change based on the target name
    arguments={"ver": "1.0","feedtype": "json"}
    )
    #Print the MCP Tool response
    print(f"Tool Call result: {result['content'][0]['text']}")
