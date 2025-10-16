from aws_cdk import App
from server_lambda_bot.server_lambda_bot_stack import ServerLambdaBotStack

app = App()

ctx = {
    **(app.node.try_get_context("default") or {}),
    "instanceId": app.node.try_get_context("instanceId"),
    "discordPublicKey": app.node.try_get_context("discordPublicKey"),
}

ServerLambdaBotStack(
    app,
    "ServerLambdaBotStack",
    instance_id=ctx.get("instanceId"),
    discord_public_key=ctx.get("discordPublicKey"),
)

app.synth()
