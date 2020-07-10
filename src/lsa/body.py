from abc import ABC, abstractmethod


class Body(ABC):

    @abstractmethod
    def pack_lsa_body(self):
        pass

    @staticmethod
    @abstractmethod
    def unpack_lsa_body(body_bytes, version):
        pass

    @abstractmethod
    def __str__(self):
        pass
