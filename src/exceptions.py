class InfrastructureException(Exception):
    pass


class InvalidDataError(InfrastructureException):
    pass


class RelationError(InfrastructureException):
    pass
