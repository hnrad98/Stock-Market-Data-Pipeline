with prices as (
    select * from {{ ref('stg_stock_prices') }}
),

with_prev as (
    select
        *,
        lag(close_price) over (
            partition by ticker order by trade_date
        ) as prev_close
    from prices
),

returns as (
    select
        trade_date,
        ticker,
        sector,
        open_price,
        high_price,
        low_price,
        close_price,
        volume,
        prev_close,
        case
            when prev_close > 0
            then (close_price - prev_close) / prev_close * 100
            else null
        end as daily_return_pct,
        sum(
            case
                when prev_close > 0
                then (close_price - prev_close) / prev_close * 100
                else 0
            end
        ) over (
            partition by ticker
            order by trade_date
            rows between unbounded preceding and current row
        ) as cumulative_return_pct,
        daily_range,
        case
            when close_price > 0
            then daily_range / close_price * 100
            else 0
        end as daily_range_pct
    from with_prev
    where prev_close is not null
)

select * from returns
