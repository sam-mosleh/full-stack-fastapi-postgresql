from .base import AuthenticatedNamespace


class RootNamespace(AuthenticatedNamespace):
    pass


root_namespace = RootNamespace("/")
