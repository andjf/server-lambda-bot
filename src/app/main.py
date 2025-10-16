import os
import boto3
from flask import Flask, jsonify, request
from mangum import Mangum
from asgiref.wsgi import WsgiToAsgi
from discord_interactions import verify_key_decorator
from functools import wraps
from botocore.exceptions import BotoCoreError, ClientError

# === Configuration ===
PUBLIC_KEY = os.environ["PUBLIC_KEY"]
INSTANCE_ID = os.environ["INSTANCE_ID"]
ec2 = boto3.client("ec2")

app = Flask(__name__)
asgi_app = WsgiToAsgi(app)
handler = Mangum(asgi_app)


# === Helper Decorator for consistent error handling ===
def safe_ec2_action(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except (BotoCoreError, ClientError) as e:
            raise RuntimeError(f"AWS error: {e.response.get('Error', {}).get('Message', str(e))}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error: {str(e)}")
    return wrapper


# === EC2 Management Functions ===

@safe_ec2_action
def server_status() -> str:
    """Return EC2 instance status, IP, and DNS."""
    resp = ec2.describe_instances(InstanceIds=[INSTANCE_ID])
    instance = resp["Reservations"][0]["Instances"][0]
    state = instance["State"]["Name"]
    ipv4 = instance.get("PublicIpAddress", "N/A")
    dns = instance.get("PublicDnsName", "N/A")

    icons = {
        "running": "✅",
        "stopped": "🛑",
        "pending": "⏳",
        "stopping": "⏳",
    }
    icon = icons.get(state, "❓")

    return (
        f"{icon} Instance state: **{state}**\n"
        f"🌐 Public IPv4: `{ipv4.strip() or 'N/A'}`\n"
        f"🌐 Public DNS: `{dns.strip() or 'N/A'}`"
    )


@safe_ec2_action
def server_start() -> str:
    """Start the EC2 instance."""
    ec2.start_instances(InstanceIds=[INSTANCE_ID])
    return "🚀 Starting the EC2 instance..."


@safe_ec2_action
def server_stop() -> str:
    """Stop the EC2 instance."""
    ec2.stop_instances(InstanceIds=[INSTANCE_ID])
    return "🛑 Stopping the EC2 instance..."


OPTION_MAP = {
    "status": server_status,
    "start": server_start,
    "stop": server_stop,
}


# === Discord interaction handler ===

@app.route("/", methods=["POST"])
async def interactions():
    print(f"👉 Request: {request.json}")
    return interact(request.json)


@verify_key_decorator(PUBLIC_KEY)
def interact(raw_request):
    """Handles Discord interaction events."""
    try:
        # Ping from Discord
        if raw_request.get("type") == 1:
            return jsonify({"type": 1})

        data = raw_request["data"]
        command_name = data.get("name", "").lower()
        if command_name != "server":
            raise ValueError(f"Unknown command `{command_name}`")

        options = data.get("options", [])
        if len(options) != 1:
            raise ValueError("Expected a single subcommand (start, stop, status).")

        option_name = options[0]["name"].lower()
        if option_name not in OPTION_MAP:
            raise ValueError(f"Unknown option `{option_name}`. Expected one of {list(OPTION_MAP)}.")

        result_message = OPTION_MAP[option_name]()

        return jsonify({
            "type": 4,
            "data": {"content": result_message},
        })

    except Exception as e:
        error_message = f"⚠️ Error:\n```{str(e)}```"
        print(error_message)
        return jsonify({
            "type": 4,
            "data": {"content": error_message},
        })


if __name__ == "__main__":
    app.run(debug=True)
