class ReflectiveArgumentEngine:

    def build(self, reports):

        arguments = []

        for report in reports:

            state_keys = [
                key
                for key in report.keys()
                if key.endswith("_state") or key == "execution_permission"
            ]

            for key in state_keys:

                arguments.append({
                    "source": report.get("system", "unknown"),
                    "claim": key,
                    "value": report.get(key),
                })

        return {
            "system": "reflective_argument_engine",
            "arguments": arguments,
            "argument_count": len(arguments),
            "argument_state": (
                "reflective_arguments_available"
                if arguments
                else "reflective_arguments_empty"
            ),
        }
