from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    aws_lambda as lambda_,
    aws_iam as iam
)
from constructs import Construct

LAMBDA_MEMORY_SIZE = 512
LAMBDA_TIMEOUT_SECONDS = 3

class ServerLambdaBotStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, instance_id: str, discord_public_key: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        instance_arn = f"arn:aws:ec2:{self.region}:{self.account}:instance/{instance_id}"

        assert instance_id, "Provided EC2 instance ID was either empty or not provided"
        assert discord_public_key, "Provided Discord application public key was either empty or not provided"

        docker_function = lambda_.DockerImageFunction(
            self,
            "DockerFunction",
            code=lambda_.DockerImageCode.from_image_asset("./src"),
            memory_size=LAMBDA_MEMORY_SIZE,
            timeout=Duration.seconds(LAMBDA_TIMEOUT_SECONDS),
            architecture=lambda_.Architecture.X86_64,
            environment={
                "PUBLIC_KEY": discord_public_key,
                "INSTANCE_ID": instance_id,
            },
        )

        docker_function.add_to_role_policy(
            iam.PolicyStatement(
                actions=["ec2:DescribeInstances"],
                resources=["*"],
            )
        )
        docker_function.add_to_role_policy(
            iam.PolicyStatement(
                actions=["ec2:StartInstances", "ec2:StopInstances"],
                resources=[instance_arn],
            )
        )

        function_url = docker_function.add_function_url(
            auth_type=lambda_.FunctionUrlAuthType.NONE,
            cors=lambda_.FunctionUrlCorsOptions(
                allowed_origins=["*"],
                allowed_methods=[lambda_.HttpMethod.ALL],
                allowed_headers=["*"],
            ),
        )

        CfnOutput(self, "FunctionUrl", value=function_url.url)
