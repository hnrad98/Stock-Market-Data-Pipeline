with daily_returns as (
    select * from {{ ref('fct_daily_returns') }}
),

sector_daily as (
    select
        trade_date,
        sector,
        count(distinct ticker) as num_stocks,
        avg(daily_return_pct) as avg_daily_return,
        min(daily_return_pct) as min_daily_return,
        max(daily_return_pct) as max_daily_return,
        sum(volume) as total_volume,
        avg(daily_range_pct) as avg_daily_range_pct
    from daily_returns
    group by trade_date, sector
),

sector_stats as (
    select
        *,
        sum(avg_daily_return) over (
            partition by sector
            order by trade_date
            rows between unbounded preceding and current row
        ) as cumulative_return
    from sector_daily
)

select
    *,
    rank() over (
        partition by trade_date
        order by avg_daily_return desc
    ) as daily_rank
from sector_stats
