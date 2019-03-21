import sys
import os
from google.protobuf.timestamp_pb2 import Timestamp
sys.path.insert(0, os.path.abspath(os.path.join(
    os.path.dirname(__file__), '../')))
import grpc_client


def main(apiserverAddr, dId, path, key, value):
    client = grpc_client.GRPCClient(apiserverAddr)
    ts = Timestamp()
    ts.GetCurrentTime()

    # Boilerplate values for dtype, sync, and compare
    dtype = "device"
    sync = True
    compare = None

    pathElts = createPathElts(path)
    update = [(key, value)]
    notifs = [grpc_client.CreateNotification(ts, pathElts, updates=update)]
    s = client.Publish(dtype, dId, sync, compare, notifs)
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 6:
        print("usage: ", sys.argv[0], "<apiserverAddress> " +
              "<deviceID> <path> <key> <value>")
        exit(2)
    # Edit time range for events here
    exit(main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]))
