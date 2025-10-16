import aws_cdk as core
import aws_cdk.assertions as assertions

from server_lambda_bot.server_lambda_bot_stack import ServerLambdaBotStack

# example tests. To run these tests, uncomment this file along with the example
# resource in server_lambda_bot/server_lambda_bot_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = ServerLambdaBotStack(app, "server-lambda-bot")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
