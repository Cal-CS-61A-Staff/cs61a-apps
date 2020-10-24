from google.cloud import firestore


def valid(id: str):
    if "/" in id or ".." in id or id == "." or id[:2] == "__":
        raise Exception("Invalid ID! This error has been logged.")
    return id


class SafeFirestore:
    def __init__(self, obj=None):
        self.obj = obj or firestore.Client()

    def document(self, name):
        return SafeFirestore(self.obj.document(valid(name)))

    def collection(self, name):
        return SafeFirestore(self.obj.collection(valid(name)))

    def __getattr__(self, item):
        return getattr(self.obj, item)
