"""Read-only API routes for processed static NASA datasets."""

from fastapi import APIRouter, HTTPException, Query

from app.services import dataset_service


router = APIRouter(prefix="/api/datasets", tags=["NASA Datasets"])


def _raise_dataset_http_error(exc: dataset_service.DatasetServiceError) -> None:
    raise HTTPException(
        status_code=exc.status_code,
        detail={"code": exc.error_code, "message": str(exc)},
    ) from exc


@router.get("", summary="List supported NASA datasets and local availability")
def datasets_list() -> dict:
    try:
        return dataset_service.list_datasets()
    except dataset_service.DatasetServiceError as exc:
        _raise_dataset_http_error(exc)


@router.get("/{dataset_id}/metadata", summary="Get NASA dataset metadata")
def dataset_metadata(dataset_id: str) -> dict:
    try:
        return dataset_service.get_dataset_metadata(dataset_id)
    except dataset_service.DatasetServiceError as exc:
        _raise_dataset_http_error(exc)


@router.get("/{dataset_id}/summary", summary="Get NASA dataset summary statistics")
def dataset_summary(dataset_id: str) -> dict:
    try:
        return dataset_service.get_dataset_summary(dataset_id)
    except dataset_service.DatasetServiceError as exc:
        _raise_dataset_http_error(exc)


@router.get("/{dataset_id}/records", summary="Get a page of processed NASA records")
def dataset_records(
    dataset_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(
        default=dataset_service.DEFAULT_PAGE_SIZE,
        ge=1,
        le=dataset_service.MAX_PAGE_SIZE,
    ),
) -> dict:
    try:
        return dataset_service.get_dataset_records(
            dataset_id, page=page, page_size=page_size
        )
    except dataset_service.DatasetServiceError as exc:
        _raise_dataset_http_error(exc)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": "invalid_pagination", "message": str(exc)},
        ) from exc
