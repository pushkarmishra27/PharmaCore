import pandas as pd

from database import fetch_all


# ==========================================================
# SALES DATA
# ==========================================================

def sales_dataframe(start_date=None, end_date=None):

    query = """
        SELECT
            s.sale_id,
            s.customer_name,
            s.customer_phone,
            s.sale_date,
            si.batch_no,
            si.medicine_name,
            si.quantity,
            si.unit_price,
            si.line_total

        FROM sales s

        JOIN sale_items si
        ON s.sale_id = si.sale_id
    """

    if start_date and end_date:

        query = query + """
            WHERE DATE(s.sale_date) >= %s
            AND DATE(s.sale_date) <= %s
        """

        data = fetch_all(
            query,
            (start_date, end_date)
        )

    elif start_date:

        query = query + """
            WHERE DATE(s.sale_date) >= %s
        """

        data = fetch_all(
            query,
            (start_date,)
        )

    elif end_date:

        query = query + """
            WHERE DATE(s.sale_date) <= %s
        """

        data = fetch_all(
            query,
            (end_date,)
        )

    else:

        data = fetch_all(query)

    return pd.DataFrame(data)

