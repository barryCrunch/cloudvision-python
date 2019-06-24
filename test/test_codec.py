import os
import sys
import numpy as np
import yaml
import logging
import msgpack
from AerisRequester.codec import Encoder, Decoder, frozendict, Float32

def grouped(it, n):
    return zip(*[iter(it)]*n)
# makeComplex creates a complex dictionary using a list of pairs
def makeComplex(l):
    res = {}
    for k, v in grouped(l, 2):
        if isinstance(k, dict):
            k = frozendict(k)
        res[k] = v
    return frozendict(res)


def runTest(encoder, decoder, test, inp):
    expected = bytearray(test["out"])
    res = encoder.Encode(inp)
    if res != expected:
        logging.error("Bad encoding for %s. Got %s expected %s"
                      % (test["name"], res, expected))
        return
    rev = decoder.Decode(res)
    if rev != inp:
        logging.error("Bad decoding for %s. Got %s expected %s"
                      % (test["name"], rev, inp))
        return

    print("Test passed for: ", test["name"])


with open("test_codec.yml", "r") as f:
    testDict = yaml.load(f.read())

encoder = Encoder()
decoder = Decoder()

identity = lambda x: x
preprocessing = {
    "bool": identity,
    "i8": identity,
    "i16": identity,
    "i32": identity,
    "i64": int,
    "f32": lambda x: Float32(np.float32(x)),
    "f64": float,
    "str": identity,
    "bytes": bytes,
    "array": identity,
    "map": lambda x: frozendict(x),
    "complex": makeComplex,
    "pointer": lambda x: msgpack.ExtType(0, encoder.Encode(x)),
    "nil": lambda x: None
}

for t in testDict["tests"]:
    testType, testVal = next(((key, val) for key, val in t.items()
                              if key != 'name' and key != 'out'))
    testVal = preprocessing[testType](testVal)
    runTest(encoder, decoder, t, testVal)
