import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../gen/')))
import router_pb2 as rtr
import router_pb2_grpc as rtr_client
import notification_pb2 as ntf
import codec
import grpc

def CreateQuery(pathKeys, dId, dtype="device"):
   """
   CreateQuery creates a protobuf query message with dataset ID dId and dataset type dtype.
   pathKeys must be of the form [([pathElts...], [keys...])...]
   """
   encoder = codec.Encoder()
   paths = []
   for path, key in pathKeys:
      if key is not None:
         key = [encoder.Encode(k) for k in key]
      paths.append(rtr.Path(
         keys=key,
         path_elements=[encoder.Encode(elt) for elt in path]
      ))
   return rtr.Query(
      dataset = ntf.Dataset(type=dtype, name=dId),
      paths = paths
   )

def CreateNotification(ts, paths, deletes=None, updates=None, retracts=None):
   """
   CreateNotification creates a notification protobuf message.
   ts must be of the type google.protobuf.timestamp_pb2.Timestamp
   paths must be a list of path elements
   deletes and retracts, if present, must be lists of keys
   updates, if present, must be of the form [(key, value)...]
   """
   encoder = codec.Encoder()
   dels = upd = ret = None
   if deletes is not None:
      dels = [encoder.Encode(d) for d in deletes]
   if updates is not None:
      upd = [ntf.Notification.Update(key=encoder.Encode(k), value=encoder.Encode(v)) for k, v in updates]
   if retracts is not None:
      ret = [encoder.Encoder(r) for r in retracts]
   pathElts = [encoder.Encode(elt) for elt in paths]
   return ntf.Notification(
      timestamp = ts,
      deletes = dels,
      updates = upd,
      retracts = ret,
      path_elements = pathElts
   )

class GRPCClient(object):
   """
   GRPCClient implements the protobuf client as well as its methods.
   grpcAddr must be a valid apiserver adress
   certs, if present, must be the path to the cert file.
   """

   def __init__(self, grpcAddr, certs=None):
      if certs is None:
         channel = grpc.insecure_channel(grpcAddr)
      else:
         with open(certs, "rb") as f:
            creds = grpc.ssl_channel_credentials(f.read())
         channel = grpc.secure_channel(grpcAddr, creds)
      self.__client = rtr_client.RouterV1Stub(channel)

      self.encoder = codec.Encoder()
      self.decoder = codec.Decoder()

   def Get(self, querries, start=None, end=None, versions=None, sharding=None):
      """
      Get creates and executes a Get protobuf message, returning a stream of
      notificationBatch.
      querries must be a list of querry protobuf messages.
      start and end, if present, must be nanoseconds timestamps (uint64).
      sharding, if present must be a protobuf sharding message.
      """
      request = rtr.GetRequest(
         query=querries,
         start=start,
         end=end,
         versions=versions
      )
      if sharding is not None:
         request.sharded_sub = sharding
      stream = self.__client.Get(request)
      return (self.DecodeNotificationBatch(nb) for nb in stream)

   def Subscribe(self, querries, sharding=None):
      """
      Subscribe creates and executes a Subscribe protobuf message, returning a stream of
      notificationBatch.
      querries must be a list of querry protobuf messages.
      sharding, if present must be a protobuf sharding message.
      """
      req = rtr.SubscribeRequest(
         query=querries
      )
      if sharding is not None:
         res.sharded_sub = sharding
      stream = self.__client.Subscribe(req)
      return (self.DecodeNotificationBatch(nb) for nb in stream)

   def Publish(self, dtype, dId, sync, compare, notifs):
      """
      Publish creates and executes a Publish protobuf message.
      refer to AerisRequester/protobufs/router.proto:124
      """
      req = rtr.PublishRequest(
         batch = ntf.NotificationBatch(
            d = "device",
            dataset = ntf.Dataset(type=dtype, name=dId),
            notifications = notifs
         ),
         sync = sync,
         compare = compare
      )
      self.__client.Publish(req)

   def GetDatasets(self, types=[]):
      """
      GetDatasets retrieves all the dataset streaming on Aeris
      types, if present, filter the querried dataset by types
      """
      req = rtr.DatasetsRequest(
         types = types
      )
      stream = self.__client.GetDatasets(req)
      return stream

   def CreateDataset(self, dtype, dId):
      """
      CreateDataset creates a new dataset on Aeris with type dtype and ID dId
      """
      req = rtr.CreateDatasetRequest(
         ntf.Dataset(type=dtype, name=dId)
      )
      self.__client.CreateDataset(req)

   def DecodeNotificationBatch(self, batch):
      res = {
         "dataset": {
            "name": batch.dataset.name,
            "type": batch.dataset.type
         },
         "notifications": [self.DecodeNotification(n) for n in batch.notifications]
      }
      return res

   def DecodeNotification(self, notif):
      res = {
         "timestamp": notif.timestamp,
         "deletes": [self.decoder.Decode(d) for d in notif.deletes],
         "updates": [(self.decoder.Decode(u.key), self.decoder.Decode(u.value)) for u in notif.updates],
         "retracts": [self.decoder.Decode(r) for r in notif.retracts],
         "path_elements": [self.decoder.Decode(elt) for elt in notif.path_elements]
      }
      return res
