# odata_builder.py
from urllib.parse import quote


def build_odata_from_plan(plan: dict) -> str:
    """
    Construit une URL OData complète en utilisant :
    - $select
    - $filter
    - $expand
    - $orderby
    - $top
    """

    table = plan["table"]
    select = plan.get("select", [])
    filters = plan.get("filters")
    expand = plan.get("expand")
    order_by = plan.get("order_by")
    top = plan.get("top")

    query_params = []

    # $select
    if select:
        query_params.append("$select=" + ",".join(select))

    # $expand
    if expand:
        query_params.append("$expand=" + expand)

    # $filter
    if filters:
        encoded = quote(filters, safe=" ='<>,()/")
        query_params.append("$filter=" + encoded)

    # $orderby
    if order_by:
        query_params.append("$orderby=" + order_by)

    # $top
    if top:
        query_params.append("$top=" + str(top))

    # Construire l’URL finale
    if query_params:
        return f"{table}?" + "&".join(query_params)
    else:
        return table
