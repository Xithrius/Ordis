from collections.abc import Awaitable, Callable
from functools import wraps

import pandas as pd
from discord import ButtonStyle, Interaction
from discord.ui import Button, View, button

from bot.models import MarketOrderWithCombinedUser
from bot.utils import codeblock, histogram_2d


class MarketView(View):
    def __init__(
        self,
        df: pd.DataFrame,
        url_name: str,
        name: str,
        item: MarketOrderWithCombinedUser,
    ) -> None:
        super().__init__()

        self.df = df
        self.url = url_name
        self.name = name
        self.item = item

        self.add_item(
            Button(
                label="warframe.market",
                url=f"https://warframe.market/items/{url_name}",
            ),
        )

    @button(label="Cost distribution", style=ButtonStyle.blurple)
    async def cost_distribution(self, interaction: Interaction, button: Button) -> None:
        await histogram_2d(
            self.df,
            title=f"Cost distribution of {self.name}",
            x_label="platinum",
            y_label="quantity",
            ctx=interaction,
        )

    @button(label="Percentiles", style=ButtonStyle.blurple)
    async def percentiles(self, interaction: Interaction, button: Button) -> None:
        s = self.df["platinum"]

        df = pd.DataFrame(
            {
                "percentiles": [
                    "Minimum",
                    "Max",
                    "Mean",
                    "Median",
                    "0.95",
                    "0.99",
                    "0.999",
                ],
                "platinum": [
                    round(x, 2)
                    for x in [
                        s.min(),
                        s.max(),
                        s.mean(),
                        s.median(),
                        s.quantile(0.95),
                        s.quantile(0.99),
                        s.quantile(0.999),
                    ]
                ],
            },
        )

        block = codeblock(df.to_string(index=False))

        await interaction.response.send_message(block)


def order_interaction(action: str) -> Callable[[], Awaitable[None]]:
    def decorator(func: Callable[[], Awaitable[None]]) -> Callable[[], Awaitable[None]]:
        @wraps(func)
        async def wrapper(self: MarketView, interaction: Interaction, button: Button) -> None:
            rank = ""
            if (rank_level := self.item.mod_rank) is not None:
                rank = f" (rank {rank_level})"

            msg = (
                f'/w {self.item.user_ingame_name} Hi! I want to {action}: "{self.name}{rank}" '
                f"for {self.item.platinum} platinum. (warframe.market)"
            )

            await interaction.response.send_message(f"```{msg}```", ephemeral=True)
            self.stop()

        return wrapper  # type: ignore [return-value]

    return decorator  # type: ignore [return-value]


class MarketViewBuyInteraction(MarketView):
    @button(label="Buy", style=ButtonStyle.green)  # type: ignore [call-arg]
    @order_interaction(action="buy")
    async def buy(self, interaction: Interaction, button: Button) -> None:
        pass


class MarketViewSellInteraction(MarketView):
    @button(label="Sell", style=ButtonStyle.green)  # type: ignore [call-arg]
    @order_interaction(action="sell")
    async def sell(self, interaction: Interaction, button: Button) -> None:
        pass
