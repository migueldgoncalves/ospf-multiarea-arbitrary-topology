from abc import ABC, abstractmethod


class Body(ABC):

    @abstractmethod
    def pack_packet_body(self):
        pass

    @staticmethod
    @abstractmethod
    def unpack_packet_body(body_bytes, version):
        pass

    @abstractmethod
    def __str__(self):
        pass
