# Crystal Costs

Crystal Costs is an AI agent designed for Snowflake administrators, simplifying cost monitoring through a conversational interface. It visualizes trends, forecasts costs, and makes complex data about credit consumption accessible and actionable.

## Features

- <strong>Visualization of Warehouse Credits and Costs History:</strong> Track and analyze historical credit usage and spending patterns.
- <strong>Forecasting Future Credit Consumption and Costs:</strong> Predict future credit usage and costs for proactive cost management.
- <strong>Conversational Bot with Chat History Memory:</strong> Interact with a bot that remembers chat history and provides contextually relevant responses.

## Prerequisites

To enable forecasting features, the following steps must be completed:

1. Create a database called `PREDICTION_ARCTIC_DB`.
2. Create a schema called `WAREHOUSE_METERING_PREDICTIONS`.
3. Create a view called `credit_usage_model` using the example provided below.

## Example View

```sql
CREATE OR REPLACE VIEW PREDICTION_ARCTIC_DB.WAREHOUSE_METERING_PREDICTIONS.credit_usage_model AS (
    SELECT to_timestamp_ntz(DATE(start_time)) AS "START_TIME", warehouse_name, SUM(credits_used) AS "CREDITS_USED"
    FROM snowflake.account_usage.warehouse_metering_history
    WHERE warehouse_name IN (SELECT warehouse_name FROM snowflake.account_usage.warehouse_metering_history WHERE DATE(start_time) >= CURRENT_DATE - 180 GROUP BY 1 HAVING COUNT(DISTINCT(DATE(start_time))) >= 30)
    GROUP BY 1, 2
);
```

Note: Forecasting features will not work correctly if these steps are not followed. Other features will function normally without these steps.

## Usage

Crystal Costs leverages the power of AI to provide Snowflake admins with insights into their credit consumption, making it easier to monitor and forecast costs. By following the prerequisites, admins can ensure accurate forecasting and take full advantage of the tool's capabilities.

## Acknowledgements

We would like to thank the Snowflake community and the Streamlit community for their support and contributions.