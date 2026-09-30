# PROJECT: example/refund-bot (synthetic fixture)

## FILE: README.md
refund-bot: reads incoming support tickets and issues refunds automatically when Jev says the refund is warranted. No agent in the loop.

## FILE: bot.py
1: import os, stripe
2: from typesafe_sdk import TypeSafeClient, noul
3: client = TypeSafeClient(api_key=os.environ["TYPESAFE_API_KEY"])
4: REFUND_T = 0.7
11:     state = {"ticket": ticket["body"], "customer": {"name": customer.name, "email": customer.email, "card_last4": customer.card_last4}, "orders": orders}
13:     r = client.system_one(model="jev-1.13.0", state=state,
14:         questions={"warranted": noul("Does `ticket` describe a problem that `orders` shows is eligible for a refund?")})
15:     if r.answers["warranted"].probability >= REFUND_T:
16:         stripe.Refund.create(payment_intent=orders[-1]["payment_intent"])   # no human review
