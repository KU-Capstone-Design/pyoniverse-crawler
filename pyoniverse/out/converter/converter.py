from abc import ABCMeta, abstractmethod


class Converter(metaclass=ABCMeta):
    @abstractmethod
    def convert(self, *args, **kwargs) -> str:
        pass
