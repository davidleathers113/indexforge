"""JSON schemas for Docker configuration validation."""

DOCKERFILE_SCHEMA = {
    "type": "object",
    "required": ["stages"],
    "properties": {
        "stages": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name", "base_image"],
                "properties": {
                    "name": {"type": "string"},
                    "base_image": {"type": "string"},
                    "commands": {"type": "array", "items": {"type": "string"}},
                    "copy_from": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["from", "source", "dest"],
                            "properties": {
                                "from": {"type": "string"},
                                "source": {"type": "string"},
                                "dest": {"type": "string"},
                            },
                        },
                    },
                },
            },
        }
    },
}

CONTAINER_CONFIG_SCHEMA = {
    "type": "object",
    "required": ["Image", "Cmd"],
    "properties": {
        "Image": {"type": "string"},
        "Cmd": {"type": "array", "items": {"type": "string"}},
        "Env": {"type": "array", "items": {"type": "string"}},
        "ExposedPorts": {"type": "object", "patternProperties": {"^[0-9]+/(tcp|udp)$": {}}},
        "Healthcheck": {
            "type": "object",
            "required": ["Test"],
            "properties": {
                "Test": {"type": "array", "items": {"type": "string"}},
                "Interval": {"type": "integer"},
                "Timeout": {"type": "integer"},
                "Retries": {"type": "integer"},
            },
        },
        "User": {"type": "string"},
        "WorkingDir": {"type": "string"},
        "Entrypoint": {"type": "array", "items": {"type": "string"}},
    },
}

CONTAINER_STATS_SCHEMA = {
    "type": "object",
    "required": ["cpu_stats", "memory_stats"],
    "properties": {
        "cpu_stats": {
            "type": "object",
            "required": ["cpu_usage", "system_cpu_usage"],
            "properties": {
                "cpu_usage": {
                    "type": "object",
                    "required": ["total_usage"],
                    "properties": {"total_usage": {"type": "number"}},
                },
                "system_cpu_usage": {"type": "number"},
            },
        },
        "memory_stats": {
            "type": "object",
            "required": ["usage", "limit"],
            "properties": {"usage": {"type": "number"}, "limit": {"type": "number"}},
        },
    },
}

BUILD_METRICS_SCHEMA = {
    "type": "object",
    "required": ["duration", "layers", "size"],
    "properties": {
        "duration": {"type": "number"},
        "layers": {"type": "integer"},
        "size": {"type": "number"},
        "cache_hits": {"type": "integer"},
        "cache_misses": {"type": "integer"},
    },
}
