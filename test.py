# import tempfile
#
# from google.cloud.storage import Client
#
# client = Client()
# bucket = client.bucket("website.buckets.cs61a.org")
# for _ in range(100):
#     blob = bucket.blob("released/index.html")
#     with tempfile.NamedTemporaryFile() as temp:
#         blob.download_to_filename(temp.name)
from shutil import copyfile

for _ in range(1000):
    copyfile("test", "test2")
