with prices as (
    select * from {{ ref('stg_stock_prices') }}
),

with_returns as (
    select
        *,
        (close_price - lag(close_price) over (partition by ticker order by trade_date))
        / nullif(lag(close_price) over (partition by ticker order by trade_date), 0)
        * 100 as daily_return_pct
    from prices
),

moving_avgs as (
    select
        trade_date,
        ticker,
        sector,
        close_price,
        volume,

        avg(close_price) over (
            partition by ticker order by trade_date
            rows between 6 preceding and current row
        ) as sma_7,
        avg(close_price) over (
            partition by ticker order by trade_date
            rows between 29 preceding and current row
        ) as sma_30,
        avg(close_price) over (
            partition by ticker order by trade_date
            rows between 89 preceding and current row
        ) as sma_90,

        avg(volume) over (
            partition by ticker order by trade_date
            rows between 19 preceding and current row
        ) as avg_volume_20d,

        stddev(daily_return_pct) over (
            partition by ticker order by trade_date
            rows between 19 preceding and current row
        ) as volatility_20d

    from with_returns
)

select * from moving_avgs
