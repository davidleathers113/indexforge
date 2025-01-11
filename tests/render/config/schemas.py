"""JSON schemas for Render configuration validation."""

RENDER_YAML_SCHEMA = {
    "type": "object",
    "required": ["services"],
    "properties": {
        "services": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["type", "name", "env", "buildCommand", "startCommand"],
                "properties": {
                    "type": {"type": "string", "enum": ["web", "worker", "cron"]},
                    "name": {"type": "string"},
                    "env": {"type": "string"},
                    "buildCommand": {"type": "string"},
                    "startCommand": {"type": "string"},
                    "envVars": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["key"],
                            "properties": {
                                "key": {"type": "string"},
                                "value": {"type": "string"},
                                "sync": {"type": "boolean"},
                            },
                        },
                    },
                    "healthCheckPath": {"type": "string"},
                    "autoDeploy": {"type": "boolean"},
                    "branch": {"type": "string"},
                    "numInstances": {"type": "integer", "minimum": 1},
                    "plan": {"type": "string"},
                },
            },
        }
    },
}

DEPLOYMENT_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["id", "status", "service"],
    "properties": {
        "id": {"type": "string"},
        "status": {"type": "string", "enum": ["created", "building", "live", "failed"]},
        "service": {
            "type": "object",
            "required": ["id", "name"],
            "properties": {"id": {"type": "string"}, "name": {"type": "string"}},
        },
        "createdAt": {"type": "string", "format": "date-time"},
        "updatedAt": {"type": "string", "format": "date-time"},
    },
}

METRICS_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["cpu_usage", "memory_usage"],
    "properties": {
        "cpu_usage": {"type": "number", "minimum": 0, "maximum": 100},
        "memory_usage": {"type": "number", "minimum": 0, "maximum": 100},
        "requests_per_second": {"type": "number", "minimum": 0},
        "response_time_ms": {"type": "number", "minimum": 0},
    },
}

BUILD_LOGS_SCHEMA = {
    "type": "object",
    "required": ["deployment_id", "logs"],
    "properties": {
        "deployment_id": {"type": "string"},
        "logs": {"type": "array", "items": {"type": "string"}},
        "timestamp": {"type": "number"},
        "metadata": {"type": "object"},
    },
}
