import re

from integration import Integration


class ClapIntegration(Integration):
    @property
    def message(self):
        if self._message.startswith(r"\kavi"):
            return re.sub(
                r"^\\kavi(.*)$",
                lambda mat: ":kavi: ".join(mat.group(1).strip().split(" ")),
                self._message,
            )
        return re.sub(
            r"^\\clap(.*)$",
            lambda mat: ":clap: ".join(mat.group(1).strip().split(" ")),
            self._message,
        )
