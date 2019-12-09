from google.protobuf.timestamp_pb2 import Timestamp
from AerisRequester.grpc_client import GRPCClient, create_notification
from parser import base


def main(apiserverAddr, dId, path, key, value, token=None, cert=None, keyfile=None):
    ts = Timestamp()
    ts.GetCurrentTime()

    # Boilerplate values for dtype, sync, and compare
    dtype = "device"
    sync = True
    compare = None

    pathElts = path.split("/")
    update = [(key, value)]
    notifs = [create_notification(ts, pathElts, updates=update)]
    with GRPCClient(apiserverAddr) as client:
        client.publish(dtype, dId, sync, compare, notifs)
    return 0


if __name__ == "__main__":
    base.add_argument("--dataset", type=str, help="dataset to publish to")
    base.add_argument("--path", help="path to publish at")
    base.add_argument("--key", help="key to publish")
    base.add_argument("--value", help="value to publish at key")
    args = base.parse_args()

    exit(main(args.apiserver, args.dataset, args.path, args.key, args.value,
              token=args.tokenFile, cert=args.certFile, keyfile=args.keyFile))
