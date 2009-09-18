from struct import unpack
from time import sleep
import sys

class TSPacket(object):
    def __init__(self, raw_data=None):
        self.raw_data = raw_data
        self.sync = None
        self.pid = None
        self.error = None
        self.start = None
        self.priority = None
        self.scramble = None
        self.adapt = None
        self.count = None
        self.payload = None

        if raw_data:
            self.parse(raw_data)

    def parse(self, raw_data):
        self.raw_data = raw_data

        sync, pid, count, payload = unpack('>BHB184s', raw_data)
        
        self.sync = sync

        self.error = (pid & 32768) >> 15
        self.start = (pid & 16384) >> 14
        self.priority = (pid & 8192) >> 13
        self.pid = pid & 8191

        self.scramble = (count & 192) >> 6
        self.adapt = (count & 48) >> 4
        self.count = count & 15

        self.payload = payload

    def __str__(self):
        return 'sync: %#x  error: %i  start: %i  priority: %i  pid: %#x  scramble: %i  adapt: %i  count: %#x  len(payload): %i' % (self.sync, self.error, self.start, self.priority, self.pid, self.scramble, self.adapt, self.count, len(self.payload))

class PESPacket(object):
    STREAM_TYPES = {
        '\xbc':     'program_stream_map',
        '\xbd':     'private_stream_1',
        '\xbe':     'padding_stream',
        '\xbf':     'private_stream_2',
        '\xf0':     'ECM_stream',
        '\xf1':     'EMM_stream',
        '\xf2':     'DSM-CC',
        '\xf3':     'ISO/IEG_13552_stream',
        '\xf4':     'PMT',
        '\xf5':     'PMT',
        '\xf6':     'PMT',
        '\xf7':     'PMT',
        '\xf8':     'PMT',
        '\xf9':     'ancillary_stream',
        '\xff':     'program_stream_directory',
    }

    def __init__(self, tspacket=None):
        self.tspacket = tspacket

        self.prefix = None
        self.id = None
        self.length = None

        self.streamid = None
        self.streamtype = None

        if tspacket:
            self.parse(tspacket)

    def parse(self, tspacket):
        if not tspacket.start:
            self.payload = tspacket.payload
            return

        if tspacket.adapt:
            length = unpack('>c', tspacket.payload[0])
            length = ord(length[0])
            length, adapt = unpack('>cs%i' % length, tspacket.payload)
            print repr(length, adapt)

        self.prefix, self.streamid, self.length = unpack('>3scH', tspacket.payload)
        self.payload = tspacket.payload[6:]

        if self.id in self.STREAM_TYPES:
            self.streamtype = self.STREAM_TYPES[self.id]
        else:
            if (self.id >> 4) == 14:
                self.streamtype = 'video'
                self.streamid = self.id & 15
            if (self.id >> 5) == 6:
                self.streamtype = 'audio'
                self.streamid = self.id & 31

    def is_header(self):
        if self.prefix and self.id and self.length:
            return True
        else:
            return False

def main():
    input = file(sys.argv[1], 'rb')
    psize = 188 
    chunksize = 7

    while True:
        data = input.read(psize * chunksize)
        if not data: break

        # Chop off anything before the sync bit
        sync_offset = data.find('\x47')
        if sync_offset == -1:
            print 'No sync bit in packet.'
            continue
        if sync_offset != 0:
            print 'Resync'
            data = data[sync_offset:]

        for i in range(chunksize):
            packet = data[:psize]
            data = data[psize:]

            packet = TSPacket(packet)
            print packet
            #pes = PESPacket(packet)
            #print pes.streamtype

if __name__ == '__main__': main()
