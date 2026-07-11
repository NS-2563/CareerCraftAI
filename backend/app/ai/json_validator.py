from copy import deepcopy


class JSONValidationError(Exception):
    """Raised when AI response does not match the expected schema."""
    pass


def validate_json(
    data,
    schema,
    strict=False,
    remove_unknown_keys=False,
):
    """
    Validate AI JSON against a schema.

    Rules:
    - Missing keys are added from the schema.
    - Nested dictionaries are validated recursively.
    - Lists must remain lists.
    - Primitive values must match schema types.
    """

    if not isinstance(data, dict):
        raise JSONValidationError("Root JSON must be an object.")

    result = deepcopy(data)

    if remove_unknown_keys:
        result = {
            key: value
            for key, value in result.items()
            if key in schema
        }

    for key, default in schema.items():

        if key not in result:

            if strict:
                raise JSONValidationError(
                    f"Missing required key: {key}"
                )

            result[key] = deepcopy(default)
            continue

        value = result[key]

        if isinstance(default, dict):

            if not isinstance(value, dict):

                if strict:
                    raise JSONValidationError(
                        f"{key} must be an object."
                    )

                result[key] = deepcopy(default)

            else:

                result[key] = validate_json(
                    value,
                    default,
                    strict=strict,
                    remove_unknown_keys=remove_unknown_keys,
                )

        elif isinstance(default, list):

            if not isinstance(value, list):

                if strict:
                    raise JSONValidationError(
                        f"{key} must be a list."
                    )

                result[key] = deepcopy(default)

            else:

                if default:

                    expected_type = type(default[0])

                    cleaned = []

                    for item in value:

                        if isinstance(item, expected_type):
                            cleaned.append(item)

                    result[key] = cleaned

        elif isinstance(default, bool):

            if not isinstance(value, bool):

                if strict:
                    raise JSONValidationError(
                        f"{key} must be a boolean."
                    )

                result[key] = default

        elif isinstance(default, int):

            if type(value) is not int:

                if strict:
                    raise JSONValidationError(
                        f"{key} must be an integer."
                    )

                result[key] = default

        elif isinstance(default, float):

            if not isinstance(value, (int, float)):

                if strict:
                    raise JSONValidationError(
                        f"{key} must be a number."
                    )

                result[key] = default

        elif isinstance(default, str):

            if value is None:

                if strict:
                    raise JSONValidationError(
                        f"{key} cannot be null."
                    )

                result[key] = ""

    return result