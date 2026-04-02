with source as (
    select * from {{ source('raw', 'raw_stock_prices') }}
),

cleaned as (
    select
        cast(date as date) as trade_date,
        upper(trim(ticker)) as ticker,
        trim(sector) as sector,
        cast(open as float64) as open_price,
        cast(high as float64) as high_price,
        cast(low as float64) as low_price,
        cast(close as float64) as close_price,
        cast(volume as int64) as volume,
        (cast(high as float64) - cast(low as float64)) as daily_range,
        case
            when cast(open as float64) > 0
            then (cast(close as float64) - cast(open as float64)) / cast(open as float64) * 100
            else 0
        end as intraday_return_pct
    from source
    where date is not null
      and close is not null
      and close > 0
),

deduped as (
    select *,
        row_number() over (partition by ticker, trade_date order by trade_date) as row_num
    from cleaned
)

select * except(row_num)
from deduped
where row_num = 1
