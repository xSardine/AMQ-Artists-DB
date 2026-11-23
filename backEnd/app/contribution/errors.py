"""Contribution failures translated to HTTP responses by the API layer."""


class ContributionError(Exception):
    pass


class ContributionNotFound(ContributionError):
    pass


class ContributionConflict(ContributionError):
    pass


class InvalidContribution(ContributionError):
    pass
