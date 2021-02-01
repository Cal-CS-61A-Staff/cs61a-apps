from google.cloud import firestore


def valid(id: str):
    if (
        not isinstance(id, str)
        or "/" in id
        or ".." in id
        or id == "."
        or id[:2] == "__"
    ):
        raise Exception("Invalid ID! This error has been logged.")
    return id


class SafeFirestore:
    def __init__(self, obj=None):
        self.obj = obj or firestore.Client()

    def document(self, name=None):
        return SafeFirestore(
            self.obj.document(valid(name)) if name else self.obj.document()
        )

    def collection(self, name=None):
        return SafeFirestore(
            self.obj.collection(valid(name)) if name else self.obj.collection()
        )

    def __getattr__(self, item):
        return getattr(self.obj, item)
