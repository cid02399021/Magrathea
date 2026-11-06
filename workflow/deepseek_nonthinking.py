import sys

import portable


class NonThinkingRunner(portable.Runner):
    def _post_api(self, base_url, path, body, key_name):
        if key_name == "DEEPSEEK_API_KEY":
            body = dict(body)
            body["thinking"] = {"type": "disabled"}
        return super()._post_api(base_url, path, body, key_name)


if __name__ == "__main__":
    portable.Runner = NonThinkingRunner
    sys.exit(portable._main())
