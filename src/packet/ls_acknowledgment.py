import packet.body as body
import lsa.lsa as lsa

'''
This class represents the body of an OSPF Link State Acknowledgement packet and contains its operations
'''


class LSAcknowledgement(body.Body):  # OSPFv2 and OSPFv3 - 20 bytes / LSA header

    def __init__(self, version):
        self.lsa_headers = []  # 20 bytes / LSA header
        self.version = version

    #  Adds one LSA header to the packet
    def add_lsa_header(self, lsa_header):
        self.lsa_headers.append(lsa_header)

    #  Creates byte object suitable to be sent and recognized as the body of an OSPF Link State Acknowledge packet
    def pack_packet_body(self):
        body_bytes = b''
        for i in self.lsa_headers:
            body_bytes += i.pack_header()
        return body_bytes

    #  Converts byte stream to body of an OSPF Link State Acknowledgement packet
    @staticmethod
    def unpack_packet_body(body_bytes, version):
        new_packet = LSAcknowledgement(version)
        for i in range(len(body_bytes) // 20):
            new_lsa = lsa.Lsa.unpack_header(body_bytes[i*20:(i+1)*20], version)
            new_packet.lsa_headers.append(new_lsa)
        return new_packet

    def __str__(self):
        lsa_headers = []
        for lsa_header in self.lsa_headers:
            lsa_headers.append(str(lsa_header))
        return str({'LSA Headers': lsa_headers, 'Version': self.version})
