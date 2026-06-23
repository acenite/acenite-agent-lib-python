__all__ = ["AceniteAgent"]
__version__ = "0.2.0"


def __getattr__(name):
    if name == "AceniteAgent":
        from .agent import AceniteAgent

        return AceniteAgent
    raise AttributeError(name)
