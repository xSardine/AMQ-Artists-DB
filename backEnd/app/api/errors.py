"""Translate contribution failures at the HTTP boundary."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from contribution.errors import (
    ContributionConflict,
    ContributionError,
    ContributionNotFound,
    InvalidContribution,
)

STATUS_CODES = {ContributionNotFound: 404, ContributionConflict: 409, InvalidContribution: 422}


async def contribution_error_response(request: Request, error: ContributionError):
    return JSONResponse(status_code=STATUS_CODES[type(error)], content={"detail": str(error)})


def install_contribution_errors(app: FastAPI) -> None:
    app.add_exception_handler(ContributionError, contribution_error_response)
