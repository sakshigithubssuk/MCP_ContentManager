import requests
from urllib.parse import urlencode
from typing import Optional

BASE_URL = "http://localhost/CMServiceAPI"


def _normalize_type_token(v: str) -> str:
    if not isinstance(v, str):
        return v
    t = v.strip().lower()
    if t in {"document", "doc", "docs", "documents", "file", "files"}:
        return "Document"
    if t in {"folder", "dir", "directory", "folders", "dirs"}:
        return "Folder"
    return v


def _normalize_types_in_dict(d: dict, keys: tuple):
    if not isinstance(d, dict):
        return
    for k in keys:
        if k in d and isinstance(d[k], str):
            d[k] = _normalize_type_token(d[k])


def _update_record_core(
    path: str = "Record/",
    parameters_to_search: Optional[dict] = None,
    parameters_to_update: Optional[dict] = None,
):
    """Core UPDATE logic: search then PUT or server-side POST."""

    if not parameters_to_update or not isinstance(parameters_to_update, dict):
        return {"error": "parameters_to_update is required and must be a dict."}

    # Normalize type tokens when present
    if parameters_to_search and isinstance(parameters_to_search, dict):
        _normalize_types_in_dict(parameters_to_search, ("type",))
    _normalize_types_in_dict(parameters_to_update, ("RecordRecordType",))

    # Determine record ids
    record_ids = []

    if parameters_to_search and isinstance(parameters_to_search, dict) and len(parameters_to_search) > 0:
        # Build search URL similar to search.py
        to_append = urlencode(parameters_to_search)
        search_url = f"{BASE_URL}/Record?q={to_append}"
        try:
            resp = requests.get(search_url)
            resp.raise_for_status()
            resp_json = resp.json()
        except Exception as e:
            return {"error": "Search request failed", "details": str(e)}

        # Extract records from common shapes
        records = []
        if isinstance(resp_json, list):
            records = resp_json
        elif isinstance(resp_json, dict):
            for candidate in ("results", "items", "rows", "data"):
                if candidate in resp_json and isinstance(resp_json[candidate], list):
                    records = resp_json[candidate]
                    break
            else:
                records = [resp_json]
        else:
            records = []

        if not records:
            # no matching records found
            # allow server-side bulk update as fallback below
            records = []

        # collect ids
        for r in records:
            if not isinstance(r, dict):
                continue
            for id_key in (
                "RecordID",
                "RecordId",
                "record_id",
                "id",
                "Id",
                "nodeId",
                "nodeRef",
                "NodeRef",
            ):
                if id_key in r and r[id_key]:
                    record_ids.append(str(r[id_key]))
                    break

    else:
        # No search params: try to find explicit ID in update payload
        explicit_id = (
            parameters_to_update.get("RecordNumber")
            or parameters_to_update.get("RecordID")
            or parameters_to_update.get("RecordId")
            or parameters_to_update.get("id")
        )
        if explicit_id:
            record_ids = [str(explicit_id)]
        else:
            return {
                "error": "No search parameters provided and no explicit record identifier found in parameters_to_update. Provide parameters_to_search or include RecordNumber/RecordID in parameters_to_update."
            }

    result = {"updated": [], "put_errors": []}

    # If we found record ids, attempt PUT for each
    if record_ids:
        for rid in record_ids:
            put_url = f"{BASE_URL}/Record/{rid}"
            try:
                r = requests.put(put_url, json=parameters_to_update)
                r.raise_for_status()
                try:
                    updated_resp = r.json()
                except Exception:
                    updated_resp = {"status_code": r.status_code, "text": r.text}
                result["updated"].append({"record_id": rid, "response": updated_resp})
            except Exception as e:
                result["put_errors"].append({"record_id": rid, "error": str(e)})
        return result

    # If no record ids but search params were provided, attempt server-side update via POST
    if parameters_to_search and isinstance(parameters_to_search, dict):
        post_url = f"{BASE_URL}/Record"
        payload = {"search": parameters_to_search, "update": parameters_to_update}
        try:
            r = requests.post(post_url, json=payload)
            r.raise_for_status()
            try:
                post_resp = r.json()
            except Exception:
                post_resp = {"status_code": r.status_code, "text": r.text}
            return {"server_side_update": post_resp}
        except Exception as e:
            return {"error": "Server-side update failed", "details": str(e)}

    # Fallback (shouldn't normally reach here)
    return {"error": "Could not determine update path."}


async def update_record_impl(action_plan: dict):
    """
    MCP-style implementation: accepts action_plan dict.
    Extracts parameters_to_search and parameters_to_update from action_plan.
    """
    path = action_plan.get("path", "Record/")
    parameters_to_search = action_plan.get("parameters_to_search")
    parameters_to_update = action_plan.get("parameters_to_update")
    return _update_record_core(
        path=path,
        parameters_to_search=parameters_to_search,
        parameters_to_update=parameters_to_update,
    )
